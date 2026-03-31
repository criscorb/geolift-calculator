"""
Power Analysis module for GeoLift pre-test calculations.
Includes Synthetic Control methodology for creating synthetic cities.
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional


class PowerAnalysis:
    """
    Calculate statistical power and optimal test parameters for GeoLift tests.
    Includes Synthetic Control for creating synthetic comparison cities.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with historical data.
        
        Args:
            data: DataFrame with columns [city, date, new_customers, ...]
        """
        self.data = data
        self.cities = data['city'].unique().tolist()
        self._compute_city_stats()
    
    def _compute_city_stats(self):
        """Compute statistics for each city."""
        self.city_stats = {}
        
        for city in self.cities:
            city_data = self.data[self.data['city'] == city]['new_customers']
            
            # Get additional metrics if available
            city_df = self.data[self.data['city'] == city]
            media_spend = city_df['media_spend'].mean() if 'media_spend' in city_df.columns else 0
            population = city_df['population'].iloc[0] if 'population' in city_df.columns else 0
            
            self.city_stats[city] = {
                'mean': city_data.mean(),
                'std': city_data.std(),
                'cv': city_data.std() / city_data.mean() if city_data.mean() > 0 else 0,
                'total': city_data.sum(),
                'days': len(city_data),
                'daily_avg': city_data.mean(),
                'media_spend': media_spend,
                'population': population,
                # Investment efficiency: customers per $ spent
                'efficiency': city_data.mean() / media_spend if media_spend > 0 else 0,
                # Penetration: customers per population
                'penetration': city_data.mean() / population * 100000 if population > 0 else 0
            }
    
    def calculate_test_power(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        expected_lift: float,
        test_duration_days: int,
        confidence_level: float = 0.95,
        use_synthetic: bool = False,
        synthetic_weights: Dict[str, float] = None
    ) -> Dict:
        """
        Calculate power for a given test configuration.
        
        STRINGENT calculation that properly accounts for:
        - Sample size (days) with diminishing returns
        - Media investment efficiency
        - Population coverage
        - Autocorrelation in time series
        - Geo-level clustering
        """
        # Validate inputs
        if not treatment_cities:
            return {
                'power': 0, 'power_percent': 0, 'mde': np.inf, 'mde_percent': np.inf,
                'is_powered': False, 'error': 'No treatment cities provided'
            }
        if not control_cities and not (use_synthetic and synthetic_weights):
            return {
                'power': 0, 'power_percent': 0, 'mde': np.inf, 'mde_percent': np.inf,
                'is_powered': False, 'error': 'No control cities provided'
            }
        
        # Get data for each group
        treatment_data = self.data[self.data['city'].isin(treatment_cities)]
        
        if use_synthetic and synthetic_weights:
            # Use synthetic control data
            control_daily = self._get_synthetic_control_series(synthetic_weights)
        else:
            control_data = self.data[self.data['city'].isin(control_cities)]
            control_daily = control_data.groupby('date')['new_customers'].sum()
        
        # Calculate daily totals per group
        treatment_daily = treatment_data.groupby('date')['new_customers'].sum()
        
        treatment_mean = treatment_daily.mean()
        control_mean = control_daily.mean()
        
        # Standard deviation of daily totals
        treatment_std = treatment_daily.std()
        control_std = control_daily.std()
        
        # Pooled standard deviation - CONSERVATIVE approach
        n_treatment_hist = len(treatment_daily)
        n_control_hist = len(control_daily)
        
        pooled_var = ((n_treatment_hist - 1) * treatment_std**2 + 
                      (n_control_hist - 1) * control_std**2) / (n_treatment_hist + n_control_hist - 2)
        pooled_std = np.sqrt(pooled_var) if pooled_var > 0 else max(treatment_std, control_std)
        
        # Effect size (absolute difference we want to detect)
        effect_size = treatment_mean * expected_lift
        
        # ===========================================
        # CRITICAL: More stringent effective sample size
        # ===========================================
        
        # 1. Autocorrelation penalty - VERY CONSERVATIVE
        # Time series data is highly autocorrelated (day to day)
        # Short tests = data points are more correlated = less independent info
        # Using continuous function for smoother power curves
        if test_duration_days <= 7:
            autocorr_factor = 0.20  # Very short test, extremely high autocorrelation
        elif test_duration_days <= 14:
            autocorr_factor = 0.25 + (test_duration_days - 7) * 0.01  # 0.25-0.32
        elif test_duration_days <= 28:
            autocorr_factor = 0.32 + (test_duration_days - 14) * 0.015  # 0.32-0.53
        elif test_duration_days <= 42:
            autocorr_factor = 0.53 + (test_duration_days - 28) * 0.01  # 0.53-0.67
        elif test_duration_days <= 60:
            autocorr_factor = 0.67 + (test_duration_days - 42) * 0.005  # 0.67-0.76
        else:
            autocorr_factor = 0.76 + min((test_duration_days - 60) * 0.002, 0.14)  # max 0.90
        
        # 2. Number of geos penalty
        # More geos = more independent observations = higher effective n
        n_geos = len(treatment_cities) + len(control_cities)
        if n_geos <= 2:
            geo_boost = 0.5  # Very few geos - high uncertainty
        elif n_geos <= 4:
            geo_boost = 0.7
        elif n_geos <= 6:
            geo_boost = 0.85
        else:
            geo_boost = min(1.0, 0.85 + (n_geos - 6) * 0.02)  # Diminishing returns
        
        # 3. Calculate effective sample size
        # base_n * autocorr_factor * geo_factor
        # Much more conservative calculation
        effective_n = test_duration_days * autocorr_factor * geo_boost
        
        # Minimum effective n to avoid division issues
        effective_n = max(effective_n, 2)
        
        # ===========================================
        # Investment efficiency adjustment - MORE STRINGENT
        # ===========================================
        treatment_spend = sum(self.city_stats[c]['media_spend'] for c in treatment_cities)
        treatment_pop = sum(self.city_stats[c]['population'] for c in treatment_cities)
        
        # Investment per customer metric
        if treatment_spend > 0 and treatment_mean > 0:
            cost_per_customer = treatment_spend / treatment_mean
            # Penalize very high CPC (noisy, inefficient campaigns)
            # Lower CPC = better signal-to-noise ratio
            if cost_per_customer <= 30:
                cpc_factor = 1.0  # Excellent efficiency
            elif cost_per_customer <= 50:
                cpc_factor = 0.9  # Good efficiency
            elif cost_per_customer <= 100:
                cpc_factor = 0.75  # Average efficiency
            elif cost_per_customer <= 200:
                cpc_factor = 0.6  # Below average
            else:
                cpc_factor = 0.4  # Poor efficiency - noisy signal
        else:
            cpc_factor = 0.8  # No spend data = penalty for uncertainty
        
        # Population coverage adjustment - MUCH MORE STRINGENT
        # Low coverage = unstable metrics = harder to detect effects
        if treatment_pop > 0:
            target_audience = treatment_pop * 0.70  # 70% = +18 target audience
            # Coverage = customers per day / target audience (as ppm - parts per million)
            coverage_ppm = (treatment_mean / target_audience) * 1_000_000
            
            # Coverage factor based on penetration
            if coverage_ppm >= 100:  # 100+ customers per million = excellent
                coverage_factor = 1.0
            elif coverage_ppm >= 50:
                coverage_factor = 0.85
            elif coverage_ppm >= 20:
                coverage_factor = 0.70
            elif coverage_ppm >= 10:
                coverage_factor = 0.55
            else:
                coverage_factor = 0.40  # Very low coverage = very noisy
        else:
            coverage_factor = 0.7  # No population data = penalty for uncertainty
        
        # ===========================================
        # Power calculation with stringent SE
        # ===========================================
        alpha = 1 - confidence_level
        z_alpha = stats.norm.ppf(1 - alpha/2)
        
        # Cluster factor - accounts for within-geo correlation
        # Higher cluster factor = more conservative (penalizes correlation)
        cluster_factor = 1.8  # Very conservative for geo-experiments
        
        # Coefficient of variation penalty
        # High CV = more noise = harder to detect
        cv_treatment = treatment_std / treatment_mean if treatment_mean > 0 else 1
        cv_factor = 1 + max(0, cv_treatment - 0.3)  # Penalize CV > 30%
        
        # Standard error with all adjustments
        # Higher SE = lower power (more conservative)
        se = pooled_std * np.sqrt(2 / effective_n) * cluster_factor * cv_factor
        
        # Adjust SE by investment/coverage factors (worse factors = higher SE)
        quality_adjustment = 1 / (cpc_factor * coverage_factor)
        se = se * min(quality_adjustment, 3.0)  # Cap at 3x
        
        # Ensure minimum SE to prevent unrealistic power
        min_se = treatment_mean * 0.05  # At least 5% of mean
        se = max(se, min_se)
        
        # Non-centrality parameter
        if se > 0:
            ncp = effect_size / se
            # Power = P(reject H0 | H1 is true)
            power = 1 - stats.norm.cdf(z_alpha - ncp) + stats.norm.cdf(-z_alpha - ncp)
        else:
            power = 0.5
        
        # Cap power at realistic bounds (never claim 100%)
        power = min(max(power, 0.05), 0.95)
        
        # Calculate MDE at 80% power
        z_beta = stats.norm.ppf(0.80)
        mde = (z_alpha + z_beta) * se
        mde_percent = (mde / treatment_mean) * 100 if treatment_mean > 0 else 100
        
        return {
            'power': power,
            'power_percent': power * 100,
            'mde_absolute': mde,
            'mde_percent': mde_percent,
            'treatment_mean': treatment_mean,
            'control_mean': control_mean,
            'pooled_std': pooled_std,
            'effect_size': effect_size,
            'standard_error': se,
            'n_days': test_duration_days,
            'effective_n': effective_n,
            'n_treatment_cities': len(treatment_cities),
            'n_control_cities': len(control_cities) if not use_synthetic else 1,
            'confidence_level': confidence_level,
            'is_powered': power >= 0.80,
            'treatment_spend': treatment_spend,
            'treatment_population': treatment_pop,
            # Diagnostic factors
            'autocorr_factor': autocorr_factor,
            'cluster_factor': cluster_factor,
            'geo_boost': geo_boost,
            'cpc_factor': cpc_factor,
            'coverage_factor': coverage_factor,
            'cv_treatment': cv_treatment,
            'cv_factor': cv_factor,
            'quality_adjustment': quality_adjustment,
            # Warnings for users
            'warnings': {
                'low_cpc_factor': cpc_factor < 0.7,
                'low_coverage': coverage_factor < 0.6,
                'high_cv': cv_treatment > 0.5,
                'few_geos': n_geos <= 2,
                'short_test': test_duration_days < 21
            }
        }
    
    def create_synthetic_control(
        self,
        treatment_cities: List[str],
        donor_cities: List[str] = None
    ) -> Dict:
        """
        Create a synthetic control city using weighted combination of donor cities.
        
        This implements the Synthetic Control Method (Abadie, Diamond, Hainmueller):
        - Finds optimal weights for donor cities
        - Minimizes pre-treatment RMSE between treatment and synthetic control
        
        Returns:
            Dictionary with weights, fit quality, and synthetic series
        """
        if donor_cities is None:
            donor_cities = [c for c in self.cities if c not in treatment_cities]
        
        if len(donor_cities) < 2:
            return {
                'error': 'Se necesitan al menos 2 ciudades donantes para crear un control sintético',
                'weights': {},
                'fit_quality': 0
            }
        
        # Get treatment time series (aggregate)
        treatment_data = self.data[self.data['city'].isin(treatment_cities)]
        treatment_series = treatment_data.groupby('date')['new_customers'].sum().values
        
        # Get donor time series matrix
        dates = treatment_data['date'].unique()
        donor_matrix = np.zeros((len(dates), len(donor_cities)))
        
        for j, city in enumerate(donor_cities):
            city_data = self.data[self.data['city'] == city]
            for i, date in enumerate(dates):
                val = city_data[city_data['date'] == date]['new_customers'].values
                donor_matrix[i, j] = val[0] if len(val) > 0 else 0
        
        # Objective function: minimize RMSE between treatment and synthetic
        def objective(weights):
            synthetic = donor_matrix @ weights
            rmse = np.sqrt(np.mean((treatment_series - synthetic) ** 2))
            return rmse
        
        # Constraints: weights sum to 1, all non-negative
        n_donors = len(donor_cities)
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        bounds = [(0, 1) for _ in range(n_donors)]
        
        # Initial guess: equal weights
        w0 = np.ones(n_donors) / n_donors
        
        # Optimize
        result = minimize(
            objective, w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        
        # Create synthetic series
        synthetic_series = donor_matrix @ optimal_weights
        
        # Calculate fit quality (R-squared)
        ss_res = np.sum((treatment_series - synthetic_series) ** 2)
        ss_tot = np.sum((treatment_series - np.mean(treatment_series)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Calculate RMSE and MAPE
        rmse = np.sqrt(np.mean((treatment_series - synthetic_series) ** 2))
        mape = np.mean(np.abs((treatment_series - synthetic_series) / treatment_series)) * 100
        
        # Build weights dictionary (only include cities with weight > 1%)
        weights_dict = {}
        for city, weight in zip(donor_cities, optimal_weights):
            if weight > 0.01:
                weights_dict[city] = float(weight)
        
        # Normalize to sum to 1
        total = sum(weights_dict.values())
        if total > 0:
            weights_dict = {k: v/total for k, v in weights_dict.items()}
        
        return {
            'weights': weights_dict,
            'all_weights': dict(zip(donor_cities, optimal_weights.tolist())),
            'fit_quality': r_squared,
            'rmse': rmse,
            'mape': mape,
            'synthetic_series': synthetic_series.tolist(),
            'treatment_series': treatment_series.tolist(),
            'dates': dates.tolist(),
            'is_good_fit': r_squared >= 0.80 and mape < 15,
            'synthetic_mean': np.mean(synthetic_series),
            'treatment_mean': np.mean(treatment_series)
        }
    
    def _get_synthetic_control_series(self, weights: Dict[str, float]) -> pd.Series:
        """Get the synthetic control time series based on weights."""
        dates = self.data['date'].unique()
        synthetic_values = []
        
        for date in dates:
            value = 0
            for city, weight in weights.items():
                city_val = self.data[
                    (self.data['city'] == city) & (self.data['date'] == date)
                ]['new_customers'].values
                if len(city_val) > 0:
                    value += city_val[0] * weight
            synthetic_values.append(value)
        
        return pd.Series(synthetic_values, index=dates)
    
    def explain_synthetic_control_simple(self, weights: Dict[str, float]) -> str:
        """
        Explain synthetic control in simple terms for C-Level executives.
        
        Args:
            weights: Dictionary of city weights from create_synthetic_control
            
        Returns:
            Simple explanation string
        """
        if not weights:
            return "No se pudo crear la ciudad sintética."
        
        # Sort by weight
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        # Build explanation
        parts = []
        for city, weight in sorted_weights:
            pct = weight * 100
            parts.append(f"{pct:.0f}% de {city}")
        
        composition = " + ".join(parts)
        
        explanation = f"""
**¿Qué es la Ciudad Sintética?**

Es una ciudad "virtual" que creamos combinando datos de otras ciudades reales 
para que se parezca lo más posible a tu ciudad de tratamiento ANTES de la campaña.

**¿Para qué sirve?**

Cuando no tienes una ciudad espejo natural (similar en tamaño y comportamiento), 
creamos una usando estadística. Así podemos comparar qué habría pasado 
en la ciudad de tratamiento SI NO hubiéramos hecho la campaña.

**¿Cómo se compone?**

Tu Ciudad Sintética = {composition}

**¿Es confiable?**

El sistema ajusta automáticamente los pesos para minimizar las diferencias 
con tu ciudad de tratamiento antes del test. Si el ajuste es ≥80%, es confiable.
"""
        return explanation
    
    def find_optimal_duration(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        expected_lift: float,
        target_power: float = 0.80,
        confidence_level: float = 0.95,
        max_days: int = 90
    ) -> Dict:
        """
        Find optimal test duration to achieve target power.
        """
        power_curve = []
        optimal_days = None
        
        for days in range(7, max_days + 1, 7):
            result = self.calculate_test_power(
                treatment_cities, control_cities, expected_lift, days, confidence_level
            )
            power_curve.append({
                'days': days,
                'power': result['power'],
                'mde_percent': result['mde_percent']
            })
            
            if result['power'] >= target_power and optimal_days is None:
                optimal_days = days
        
        return {
            'optimal_days': optimal_days or max_days,
            'power_curve': power_curve,
            'achievable': optimal_days is not None
        }
    
    def power_by_lift(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        test_duration_days: int,
        confidence_level: float = 0.95,
        lift_range: Tuple[float, float] = (0.05, 0.50)
    ) -> List[Dict]:
        """
        Calculate power for different lift values.
        """
        results = []
        lifts = np.arange(lift_range[0], lift_range[1] + 0.01, 0.05)
        
        for lift in lifts:
            result = self.calculate_test_power(
                treatment_cities, control_cities, lift, test_duration_days, confidence_level
            )
            results.append({
                'lift_percent': lift * 100,
                'power': result['power'],
                'power_percent': result['power_percent']
            })
        
        return results
    
    def recommend_cities(
        self,
        n_treatment: int = 1,
        n_control: int = 1,
        exclude_cities: List[str] = None
    ) -> Dict:
        """
        Recommend treatment and control cities based on multiple criteria.
        """
        exclude_cities = exclude_cities or []
        available_cities = [c for c in self.cities if c not in exclude_cities]
        
        if len(available_cities) < n_treatment + n_control:
            return {
                'error': 'Not enough cities available',
                'treatment': [],
                'control': []
            }
        
        # Sort cities by volume
        sorted_cities = sorted(
            available_cities,
            key=lambda c: self.city_stats[c]['mean'],
            reverse=True
        )
        
        # Treatment: highest volume cities
        treatment = sorted_cities[:n_treatment]
        treatment_mean = np.mean([self.city_stats[c]['mean'] for c in treatment])
        treatment_std = np.mean([self.city_stats[c]['std'] for c in treatment])
        
        # Control: cities most similar to treatment
        remaining = [c for c in sorted_cities if c not in treatment]
        
        # Score remaining cities by similarity
        scored_cities = []
        for city in remaining:
            stats = self.city_stats[city]
            volume_diff = abs(stats['mean'] - treatment_mean) / treatment_mean if treatment_mean > 0 else 0
            std_diff = abs(stats['std'] - treatment_std) / treatment_std if treatment_std > 0 else 0
            similarity_score = 1 - (volume_diff * 0.7 + std_diff * 0.3)
            scored_cities.append({
                'city': city,
                'score': similarity_score,
                'volume_similarity': 1 - volume_diff,
                'variance_similarity': 1 - std_diff
            })
        
        scored_cities.sort(key=lambda x: x['score'], reverse=True)
        control = [c['city'] for c in scored_cities[:n_control]]
        control_scores = {c['city']: c for c in scored_cities[:n_control]}
        
        # Build detailed rationale
        treatment_rationale = []
        for i, city in enumerate(treatment):
            stats = self.city_stats[city]
            treatment_rationale.append({
                'city': city,
                'reason': f"#{i+1} en volumen con {stats['mean']:.0f} clientes/día",
                'detail': "Mayor volumen = más datos = mejor detección del efecto"
            })
        
        control_rationale = []
        for city in control:
            stats = self.city_stats[city]
            score_info = control_scores[city]
            similarity_pct = score_info['volume_similarity'] * 100
            control_rationale.append({
                'city': city,
                'reason': f"{similarity_pct:.0f}% similar en volumen al tratamiento",
                'detail': f"Volumen: {stats['mean']:.0f}/día vs {treatment_mean:.0f}/día"
            })
        
        return {
            'treatment': treatment,
            'control': control,
            'treatment_stats': {c: self.city_stats[c] for c in treatment},
            'control_stats': {c: self.city_stats[c] for c in control},
            'treatment_rationale': treatment_rationale,
            'control_rationale': control_rationale,
            'treatment_mean': treatment_mean,
            'rationale': f"Tratamiento: ciudades con mayor volumen. Control: ciudades similares."
        }
    
    def calculate_similarity_matrix(self) -> pd.DataFrame:
        """
        Calculate similarity matrix between all cities.
        """
        n = len(self.cities)
        matrix = np.zeros((n, n))
        
        for i, city1 in enumerate(self.cities):
            for j, city2 in enumerate(self.cities):
                if i == j:
                    matrix[i, j] = 100
                else:
                    stats1 = self.city_stats[city1]
                    stats2 = self.city_stats[city2]
                    
                    mean_diff = abs(stats1['mean'] - stats2['mean']) / max(stats1['mean'], stats2['mean'])
                    std_diff = abs(stats1['std'] - stats2['std']) / max(stats1['std'], stats2['std']) if max(stats1['std'], stats2['std']) > 0 else 0
                    
                    similarity = (1 - mean_diff * 0.7 - std_diff * 0.3) * 100
                    matrix[i, j] = max(0, similarity)
        
        return pd.DataFrame(matrix, index=self.cities, columns=self.cities).round(1)
    
    def calculate_population_coverage(self, cities: List[str]) -> Dict:
        """
        Calculate population coverage metrics.
        Assumes 70% of population is +18 (target audience).
        """
        total_pop = sum(self.city_stats[c]['population'] for c in cities)
        target_audience_factor = 0.70  # 70% is +18 years old
        
        return {
            'total_population': total_pop,
            'target_audience': total_pop * target_audience_factor,
            'target_audience_factor': target_audience_factor,
            'disclaimer': "Se asume que el 70% de la población es +18 años (público objetivo)"
        }
    
    # =========================================
    # NEW FEATURES - GeoLift Enhanced
    # =========================================
    
    def calculate_market_matching_score(
        self,
        treatment_cities: List[str],
        control_cities: List[str]
    ) -> Dict:
        """
        Calculate how well control cities match treatment cities.
        Returns detailed matching metrics.
        """
        # Get time series for each group
        treatment_data = self.data[self.data['city'].isin(treatment_cities)]
        control_data = self.data[self.data['city'].isin(control_cities)]
        
        treatment_daily = treatment_data.groupby('date')['new_customers'].sum()
        control_daily = control_data.groupby('date')['new_customers'].sum()
        
        # Align series
        common_dates = treatment_daily.index.intersection(control_daily.index)
        t_series = treatment_daily.loc[common_dates].values
        c_series = control_daily.loc[common_dates].values
        
        # 1. Correlation
        correlation = np.corrcoef(t_series, c_series)[0, 1] if len(t_series) > 2 else 0
        
        # 2. Volume ratio (ideally close to 1)
        t_mean = np.mean(t_series)
        c_mean = np.mean(c_series)
        volume_ratio = min(t_mean, c_mean) / max(t_mean, c_mean) if max(t_mean, c_mean) > 0 else 0
        
        # 3. Trend similarity (compare slopes)
        if len(t_series) > 5:
            t_trend = np.polyfit(range(len(t_series)), t_series, 1)[0]
            c_trend = np.polyfit(range(len(c_series)), c_series, 1)[0]
            trend_diff = abs(t_trend - c_trend) / max(abs(t_trend), abs(c_trend), 1)
            trend_similarity = max(0, 1 - trend_diff)
        else:
            trend_similarity = 0.5
        
        # 4. Volatility similarity (compare std)
        t_cv = np.std(t_series) / np.mean(t_series) if np.mean(t_series) > 0 else 0
        c_cv = np.std(c_series) / np.mean(c_series) if np.mean(c_series) > 0 else 0
        volatility_similarity = 1 - min(abs(t_cv - c_cv), 1)
        
        # Overall matching score (weighted average)
        overall_score = (
            correlation * 0.40 +           # Correlation is most important
            volume_ratio * 0.25 +          # Volume similarity
            trend_similarity * 0.20 +      # Same trend
            volatility_similarity * 0.15   # Same volatility
        ) * 100
        
        # Rating
        if overall_score >= 80:
            rating = "Excelente"
            rating_emoji = "🟢"
        elif overall_score >= 60:
            rating = "Bueno"
            rating_emoji = "🟡"
        elif overall_score >= 40:
            rating = "Aceptable"
            rating_emoji = "🟠"
        else:
            rating = "Bajo"
            rating_emoji = "🔴"
        
        return {
            'overall_score': overall_score,
            'correlation': correlation * 100,
            'volume_ratio': volume_ratio * 100,
            'trend_similarity': trend_similarity * 100,
            'volatility_similarity': volatility_similarity * 100,
            'rating': rating,
            'rating_emoji': rating_emoji,
            'treatment_mean': t_mean,
            'control_mean': c_mean,
            'interpretation': self._interpret_matching_score(overall_score, correlation, volume_ratio)
        }
    
    def _interpret_matching_score(self, score: float, corr: float, vol_ratio: float) -> str:
        """Generate human-readable interpretation of matching score."""
        issues = []
        
        if corr < 0.7:
            issues.append("baja correlación histórica")
        if vol_ratio < 0.5:
            issues.append("diferencia significativa en volumen")
        
        if score >= 80:
            return "✅ Las ciudades de control son muy similares al tratamiento. Excelente para el test."
        elif score >= 60:
            base = "⚠️ Match aceptable."
            if issues:
                return f"{base} Notas: {', '.join(issues)}."
            return base
        else:
            return f"❌ Match bajo. Problemas: {', '.join(issues) if issues else 'diferencias significativas'}. Considera otras ciudades."
    
    def calculate_mde_heatmap(
        self,
        test_duration: int = 28,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Calculate MDE for all possible city combinations.
        Returns a matrix for heatmap visualization.
        """
        cities = self.cities
        n = len(cities)
        mde_matrix = np.zeros((n, n))
        
        for i, treat_city in enumerate(cities):
            for j, ctrl_city in enumerate(cities):
                if i == j:
                    mde_matrix[i, j] = np.nan  # Can't be both treatment and control
                else:
                    result = self.calculate_test_power(
                        [treat_city], [ctrl_city],
                        0.15, test_duration, confidence_level
                    )
                    mde_matrix[i, j] = result['mde_percent']
        
        return pd.DataFrame(mde_matrix, index=cities, columns=cities).round(1)
    
    def check_pretest_balance(
        self,
        treatment_cities: List[str],
        control_cities: List[str]
    ) -> Dict:
        """
        Check pre-test balance (parallel trends assumption).
        Verifies that treatment and control have similar trends before the test.
        """
        treatment_data = self.data[self.data['city'].isin(treatment_cities)]
        control_data = self.data[self.data['city'].isin(control_cities)]
        
        treatment_daily = treatment_data.groupby('date')['new_customers'].sum().reset_index()
        control_daily = control_data.groupby('date')['new_customers'].sum().reset_index()
        
        treatment_daily['day_num'] = range(len(treatment_daily))
        control_daily['day_num'] = range(len(control_daily))
        
        # Fit trends
        t_slope, t_intercept = np.polyfit(treatment_daily['day_num'], treatment_daily['new_customers'], 1)
        c_slope, c_intercept = np.polyfit(control_daily['day_num'], control_daily['new_customers'], 1)
        
        # Calculate residuals
        t_predicted = t_intercept + t_slope * treatment_daily['day_num']
        c_predicted = c_intercept + c_slope * control_daily['day_num']
        
        t_residuals = treatment_daily['new_customers'] - t_predicted
        c_residuals = control_daily['new_customers'] - c_predicted
        
        # Parallel trends test (slopes should be similar)
        slope_diff_pct = abs(t_slope - c_slope) / max(abs(t_slope), abs(c_slope), 0.01) * 100
        
        # Correlation of changes
        t_changes = treatment_daily['new_customers'].diff().dropna()
        c_changes = control_daily['new_customers'].diff().dropna()
        changes_corr = np.corrcoef(t_changes, c_changes[:len(t_changes)])[0, 1] if len(t_changes) > 2 else 0
        
        # Determine if balance is acceptable
        is_balanced = slope_diff_pct < 30 and changes_corr > 0.3
        
        return {
            'is_balanced': is_balanced,
            'treatment_trend': t_slope,
            'control_trend': c_slope,
            'slope_diff_pct': slope_diff_pct,
            'changes_correlation': changes_corr,
            'treatment_daily': treatment_daily.to_dict('records'),
            'control_daily': control_daily.to_dict('records'),
            'interpretation': self._interpret_balance(is_balanced, slope_diff_pct, changes_corr)
        }
    
    def _interpret_balance(self, is_balanced: bool, slope_diff: float, corr: float) -> str:
        """Interpret pre-test balance results."""
        if is_balanced:
            return "✅ Las tendencias pre-test son paralelas. El diseño cumple el supuesto clave de DiD."
        else:
            issues = []
            if slope_diff >= 30:
                issues.append(f"tendencias divergentes ({slope_diff:.0f}% diferencia)")
            if corr < 0.3:
                issues.append(f"baja correlación en cambios diarios ({corr:.0%})")
            return f"⚠️ Posible violación de tendencias paralelas: {', '.join(issues)}. Considera Synthetic Control."
    
    def calculate_power_over_time(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        expected_lift: float,
        confidence_level: float = 0.95,
        max_weeks: int = 12
    ) -> List[Dict]:
        """
        Calculate how power evolves week by week.
        Useful for deciding when to stop a test.
        """
        results = []
        
        for week in range(1, max_weeks + 1):
            days = week * 7
            result = self.calculate_test_power(
                treatment_cities, control_cities,
                expected_lift, days, confidence_level
            )
            
            results.append({
                'week': week,
                'days': days,
                'power': result['power_percent'],
                'mde': result['mde_percent'],
                'is_powered': result['is_powered'],
                'recommendation': self._week_recommendation(week, result['power_percent'])
            })
        
        return results
    
    def _week_recommendation(self, week: int, power: float) -> str:
        """Generate recommendation for a specific week."""
        if power >= 80:
            return "✅ Poder alcanzado"
        elif power >= 70:
            return "🟡 Casi listo, 1-2 semanas más"
        elif power >= 50:
            return f"🟠 En progreso, ~{int((80-power)/10)+1} semanas más"
        else:
            return "🔴 Necesita más tiempo"
    
    def calculate_roi_projection(
        self,
        treatment_cities: List[str],
        expected_lift: float,
        test_duration_days: int,
        customer_value: float = 500  # Average customer lifetime value
    ) -> Dict:
        """
        Project ROI if the expected lift is achieved.
        """
        # Calculate baseline metrics
        treatment_data = self.data[self.data['city'].isin(treatment_cities)]
        daily_customers = treatment_data.groupby('date')['new_customers'].sum().mean()
        
        # Media spend
        total_spend = sum(self.city_stats[c]['media_spend'] for c in treatment_cities) * test_duration_days
        
        # Expected incremental customers
        incremental_daily = daily_customers * expected_lift
        total_incremental = incremental_daily * test_duration_days
        
        # Revenue calculations
        incremental_revenue = total_incremental * customer_value
        
        # ROI and iROAS
        roi = ((incremental_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0
        iroas = incremental_revenue / total_spend if total_spend > 0 else 0
        
        # Cost per incremental customer
        cpic = total_spend / total_incremental if total_incremental > 0 else 0
        
        return {
            'daily_baseline': daily_customers,
            'daily_incremental': incremental_daily,
            'total_incremental_customers': total_incremental,
            'total_media_spend': total_spend,
            'incremental_revenue': incremental_revenue,
            'roi_percent': roi,
            'iroas': iroas,
            'cost_per_incremental_customer': cpic,
            'customer_value_used': customer_value,
            'is_profitable': roi > 0,
            'interpretation': self._interpret_roi(roi, iroas, cpic)
        }
    
    def _interpret_roi(self, roi: float, iroas: float, cpic: float) -> str:
        """Interpret ROI metrics."""
        if roi > 100:
            return f"🟢 Excelente: Por cada $1 invertido, ganás ${iroas:.2f}. ROI del {roi:.0f}%."
        elif roi > 0:
            return f"🟡 Positivo: ROI del {roi:.0f}%. Costo por cliente incremental: ${cpic:.0f}."
        else:
            return f"🔴 Negativo: El test no sería rentable con este lift. Necesitás mayor efecto o menor inversión."
    
    # =========================================================================
    # NEW: Bootstrap Confidence Intervals
    # =========================================================================
    def calculate_bootstrap_ci(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Calculate bootstrap confidence intervals for the lift estimate.
        This provides more robust uncertainty quantification than parametric methods.
        
        Args:
            treatment_cities: List of treatment city names
            control_cities: List of control city names
            n_bootstrap: Number of bootstrap iterations
            confidence_level: Confidence level (0.95 = 95% CI)
        
        Returns:
            Dict with CI bounds, point estimate, and interpretation
        """
        # Get daily data
        treatment_data = self.data[self.data['city'].isin(treatment_cities)]
        control_data = self.data[self.data['city'].isin(control_cities)]
        
        treatment_daily = treatment_data.groupby('date')['new_customers'].sum().values
        control_daily = control_data.groupby('date')['new_customers'].sum().values
        
        n_days = min(len(treatment_daily), len(control_daily))
        treatment_daily = treatment_daily[:n_days]
        control_daily = control_daily[:n_days]
        
        # Point estimate of lift
        point_estimate = (treatment_daily.mean() - control_daily.mean()) / control_daily.mean() * 100
        
        # Bootstrap
        np.random.seed(42)
        bootstrap_lifts = []
        
        for _ in range(n_bootstrap):
            # Sample with replacement
            indices = np.random.choice(n_days, size=n_days, replace=True)
            boot_treatment = treatment_daily[indices]
            boot_control = control_daily[indices]
            
            if boot_control.mean() > 0:
                boot_lift = (boot_treatment.mean() - boot_control.mean()) / boot_control.mean() * 100
                bootstrap_lifts.append(boot_lift)
        
        bootstrap_lifts = np.array(bootstrap_lifts)
        
        # Calculate CI
        alpha = 1 - confidence_level
        ci_lower = np.percentile(bootstrap_lifts, alpha/2 * 100)
        ci_upper = np.percentile(bootstrap_lifts, (1 - alpha/2) * 100)
        
        # Standard error
        se = bootstrap_lifts.std()
        
        # Check if CI includes zero
        includes_zero = ci_lower <= 0 <= ci_upper
        
        return {
            'point_estimate': point_estimate,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_width': ci_upper - ci_lower,
            'standard_error': se,
            'confidence_level': confidence_level,
            'n_bootstrap': n_bootstrap,
            'includes_zero': includes_zero,
            'is_significant': not includes_zero,
            'interpretation': self._interpret_bootstrap_ci(point_estimate, ci_lower, ci_upper, includes_zero)
        }
    
    def _interpret_bootstrap_ci(self, point: float, lower: float, upper: float, includes_zero: bool) -> str:
        """Interpret bootstrap CI results."""
        if includes_zero:
            return f"⚠️ El intervalo de confianza [{lower:.1f}%, {upper:.1f}%] incluye el cero. El efecto podría no ser estadísticamente significativo."
        elif point > 0:
            return f"✅ Lift estimado de {point:.1f}% con IC [{lower:.1f}%, {upper:.1f}%]. El efecto es positivo y significativo."
        else:
            return f"🔴 El efecto parece negativo ({point:.1f}%) con IC [{lower:.1f}%, {upper:.1f}%]."
    
    # =========================================================================
    # NEW: Automatic Location Selection
    # =========================================================================
    def auto_select_locations(
        self,
        min_treatment: int = 1,
        max_treatment: int = None,
        min_control: int = 1,
        max_control: int = None,
        expected_lift: float = 0.15,
        test_duration: int = 28,
        target_power: float = 0.80,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Automatically find the optimal combination of treatment and control cities
        that achieves the target power with minimum number of cities.
        
        This is similar to GeoLift's GeoLiftMarketSelection() function.
        
        Args:
            min_treatment: Minimum number of treatment cities
            max_treatment: Maximum number of treatment cities (default: half of cities)
            min_control: Minimum number of control cities
            max_control: Maximum number of control cities (default: remaining cities)
            expected_lift: Expected lift percentage (0.15 = 15%)
            test_duration: Test duration in days
            target_power: Target power (0.80 = 80%)
            confidence_level: Statistical confidence level
        
        Returns:
            Dict with optimal configuration and alternatives
        """
        n_cities = len(self.cities)
        
        # Ensure all parameters are integers
        min_treatment = int(min_treatment)
        min_control = int(min_control)
        test_duration = int(test_duration)
        
        if max_treatment is None:
            max_treatment = n_cities // 2
        else:
            max_treatment = int(max_treatment)
        if max_control is None:
            max_control = n_cities - 1
        else:
            max_control = int(max_control)
        
        # Sort cities by volume (larger cities first for treatment)
        cities_by_volume = sorted(
            self.cities, 
            key=lambda c: self.city_stats[c]['mean'], 
            reverse=True
        )
        
        results = []
        
        # Try different combinations
        for n_treat in range(min_treatment, min(max_treatment + 1, n_cities)):
            for n_ctrl in range(min_control, min(max_control + 1, n_cities - n_treat + 1)):
                if n_treat + n_ctrl > n_cities:
                    continue
                
                # Get recommendation for this configuration
                try:
                    rec = self.recommend_cities(n_treat, n_ctrl)
                    if 'error' in rec:
                        continue
                    
                    treatment = rec['treatment']
                    control = rec['control']
                    
                    # Calculate power
                    power_result = self.calculate_test_power(
                        treatment, control, expected_lift, test_duration, confidence_level
                    )
                    
                    results.append({
                        'n_treatment': n_treat,
                        'n_control': n_ctrl,
                        'treatment_cities': treatment,
                        'control_cities': control,
                        'power': power_result['power_percent'],
                        'mde': power_result['mde_percent'],
                        'meets_target': power_result['power_percent'] >= target_power * 100,
                        'total_cities': n_treat + n_ctrl
                    })
                except:
                    continue
        
        if not results:
            return {'error': 'No se encontraron configuraciones válidas'}
        
        # Sort by: meets target (True first), then by fewest cities, then by highest power
        results.sort(key=lambda x: (
            not x['meets_target'],  # True first
            x['total_cities'],      # Fewer cities better
            -x['power']             # Higher power better
        ))
        
        # Best option
        best = results[0]
        
        # Alternatives that meet target
        alternatives = [r for r in results[1:6] if r['meets_target']]
        
        # If no config meets target, show best achievable
        if not best['meets_target']:
            best_achievable = max(results, key=lambda x: x['power'])
            recommendation = f"⚠️ Ninguna configuración alcanza {target_power*100:.0f}% de poder. " \
                           f"La mejor opción logra {best_achievable['power']:.0f}%."
        else:
            recommendation = f"✅ Configuración óptima: {best['n_treatment']} tratamiento + " \
                           f"{best['n_control']} control = {best['power']:.0f}% poder."
        
        return {
            'optimal': best,
            'alternatives': alternatives,
            'all_results': results[:10],  # Top 10
            'recommendation': recommendation,
            'target_power': target_power * 100,
            'expected_lift': expected_lift * 100,
            'test_duration': test_duration
        }
    
    # =========================================================================
    # NEW: Budget Allocator
    # =========================================================================
    def allocate_budget(
        self,
        treatment_cities: List[str],
        total_budget: float,
        allocation_method: str = 'proportional',  # 'proportional', 'equal', 'optimized'
        expected_lift: float = 0.15
    ) -> Dict:
        """
        Suggest how to distribute media budget across treatment cities.
        
        Args:
            treatment_cities: List of treatment city names
            total_budget: Total budget to allocate
            allocation_method: 
                - 'proportional': Based on historical customer volume
                - 'equal': Equal split across cities
                - 'optimized': Based on efficiency (customers per $)
            expected_lift: Expected lift for projections
        
        Returns:
            Dict with allocation per city and projections
        """
        if not treatment_cities:
            return {'error': 'No treatment cities provided'}
        
        n_cities = len(treatment_cities)
        
        # Get stats for treatment cities
        city_data = {city: self.city_stats[city] for city in treatment_cities}
        
        allocations = {}
        
        if allocation_method == 'equal':
            # Equal split
            budget_per_city = total_budget / n_cities
            for city in treatment_cities:
                allocations[city] = {
                    'budget': budget_per_city,
                    'percentage': 100 / n_cities
                }
        
        elif allocation_method == 'proportional':
            # Based on customer volume
            total_customers = sum(city_data[c]['mean'] for c in treatment_cities)
            for city in treatment_cities:
                proportion = city_data[city]['mean'] / total_customers
                allocations[city] = {
                    'budget': total_budget * proportion,
                    'percentage': proportion * 100
                }
        
        elif allocation_method == 'optimized':
            # Based on efficiency (customers per $ spent historically)
            efficiencies = {c: city_data[c]['efficiency'] for c in treatment_cities}
            total_efficiency = sum(efficiencies.values())
            
            if total_efficiency > 0:
                for city in treatment_cities:
                    proportion = efficiencies[city] / total_efficiency
                    allocations[city] = {
                        'budget': total_budget * proportion,
                        'percentage': proportion * 100
                    }
            else:
                # Fallback to equal if no efficiency data
                for city in treatment_cities:
                    allocations[city] = {
                        'budget': total_budget / n_cities,
                        'percentage': 100 / n_cities
                    }
        
        # Add projections
        total_projected_customers = 0
        for city in treatment_cities:
            baseline = city_data[city]['mean']
            projected_lift = baseline * expected_lift
            allocations[city]['baseline_daily'] = baseline
            allocations[city]['projected_incremental_daily'] = projected_lift
            allocations[city]['historical_spend'] = city_data[city]['media_spend']
            total_projected_customers += projected_lift
        
        # Calculate expected efficiency
        expected_cpi = total_budget / (total_projected_customers * 28) if total_projected_customers > 0 else 0
        
        return {
            'allocations': allocations,
            'total_budget': total_budget,
            'method': allocation_method,
            'method_description': self._describe_allocation_method(allocation_method),
            'expected_incremental_customers_daily': total_projected_customers,
            'expected_cost_per_incremental': expected_cpi,
            'summary_table': self._create_allocation_table(allocations, treatment_cities)
        }
    
    def _describe_allocation_method(self, method: str) -> str:
        """Describe allocation method."""
        descriptions = {
            'equal': '💰 Distribución igualitaria: Cada ciudad recibe el mismo presupuesto.',
            'proportional': '📊 Distribución proporcional: Mayor presupuesto a ciudades con más clientes.',
            'optimized': '🎯 Distribución optimizada: Mayor presupuesto a ciudades más eficientes (mejor ROI histórico).'
        }
        return descriptions.get(method, '')
    
    def _create_allocation_table(self, allocations: Dict, cities: List[str]) -> pd.DataFrame:
        """Create a summary table of budget allocations."""
        rows = []
        for city in cities:
            alloc = allocations[city]
            rows.append({
                'Ciudad': city,
                'Presupuesto ($)': f"${alloc['budget']:,.0f}",
                'Porcentaje': f"{alloc['percentage']:.1f}%",
                'Baseline Diario': f"{alloc['baseline_daily']:.0f}",
                'Incremental Est.': f"+{alloc['projected_incremental_daily']:.0f}/día"
            })
        return pd.DataFrame(rows)
    
    # =========================================================================
    # NEW: What-If Simulator
    # =========================================================================
    def simulate_what_if(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        scenarios: List[Dict]
    ) -> List[Dict]:
        """
        Simulate multiple what-if scenarios for test planning.
        
        Args:
            treatment_cities: Base treatment cities
            control_cities: Base control cities
            scenarios: List of scenario dicts with keys:
                - name: Scenario name
                - lift: Expected lift (e.g., 0.10 for 10%)
                - duration: Test duration in days
                - budget: Total budget (optional)
        
        Returns:
            List of scenario results with power, MDE, and projections
        """
        results = []
        
        for scenario in scenarios:
            name = scenario.get('name', 'Scenario')
            lift = scenario.get('lift', 0.15)
            duration = scenario.get('duration', 28)
            budget = scenario.get('budget', None)
            
            # Calculate power
            power_result = self.calculate_test_power(
                treatment_cities, control_cities, lift, duration, 0.95
            )
            
            # Calculate ROI if budget provided
            if budget:
                roi_result = self.calculate_roi_projection(
                    treatment_cities, lift, duration, 500
                )
            else:
                roi_result = None
            
            # Bootstrap CI
            bootstrap = self.calculate_bootstrap_ci(treatment_cities, control_cities)
            
            results.append({
                'scenario_name': name,
                'config': {
                    'lift': lift * 100,
                    'duration': duration,
                    'budget': budget
                },
                'power': power_result['power_percent'],
                'mde': power_result['mde_percent'],
                'is_viable': power_result['is_powered'] and power_result['mde_percent'] < lift * 100,
                'bootstrap_ci': f"[{bootstrap['ci_lower']:.1f}%, {bootstrap['ci_upper']:.1f}%]",
                'roi': roi_result['roi_percent'] if roi_result else None,
                'iroas': roi_result['iroas'] if roi_result else None,
                'recommendation': self._scenario_recommendation(power_result, lift)
            })
        
        return results
    
    def _scenario_recommendation(self, power_result: Dict, expected_lift: float) -> str:
        """Generate recommendation for a scenario."""
        power = power_result['power_percent']
        mde = power_result['mde_percent']
        
        if power >= 80 and mde < expected_lift * 100:
            return "✅ Viable - Buena configuración"
        elif power >= 60:
            return "⚠️ Aceptable - Considerar más días"
        else:
            return "❌ No viable - Necesita ajustes"
