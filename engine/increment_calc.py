"""
Increment Calculator for post-test analysis.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional
from .synthetic_control import SyntheticControl
from .difference_in_diff import DifferenceInDiff, prepare_did_data


class IncrementCalculator:
    """
    Calculate incremental lift from GeoLift test results.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with test results data.
        
        Args:
            data: DataFrame with columns [city, date, new_customers, group, period]
        """
        self.data = data
        self.treatment_data = data[data['group'] == 'treatment']
        self.control_data = data[data['group'] == 'control']
    
    def calculate_increment(self, method: str = 'did') -> Dict:
        """
        Calculate incremental effect using specified method.
        
        Args:
            method: 'did' for Difference-in-Differences or 'synthetic' for Synthetic Control
        
        Returns:
            Dictionary with increment results
        """
        if method == 'did':
            return self._calculate_did()
        elif method == 'synthetic':
            return self._calculate_synthetic()
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_did(self) -> Dict:
        """Calculate increment using DiD."""
        did = DifferenceInDiff(self.data)
        
        did_result = did.calculate_did()
        test_result = did.statistical_test()
        
        # Total incremental customers
        test_days = len(self.data[
            (self.data['group'] == 'treatment') & (self.data['period'] == 'test')
        ]['date'].unique())
        
        total_incremental = did_result['did_estimate'] * test_days
        
        return {
            'method': 'Difference-in-Differences',
            'daily_increment': did_result['did_estimate'],
            'total_incremental': total_incremental,
            'lift_percent': did_result['lift_percent'],
            'p_value': test_result['p_value'],
            'is_significant': test_result['is_significant'],
            'ci_lower': test_result['ci_lower'],
            'ci_upper': test_result['ci_upper'],
            'ci_lower_percent': test_result['ci_lower_percent'],
            'ci_upper_percent': test_result['ci_upper_percent'],
            'treatment_pre_avg': did_result['treatment_pre'],
            'treatment_post_avg': did_result['treatment_post'],
            'control_pre_avg': did_result['control_pre'],
            'control_post_avg': did_result['control_post'],
            'counterfactual': did_result['counterfactual'],
            'test_days': test_days
        }
    
    def _calculate_synthetic(self) -> Dict:
        """Calculate increment using Synthetic Control."""
        # Prepare data for synthetic control
        treatment_cities = self.treatment_data['city'].unique().tolist()
        control_cities = self.control_data['city'].unique().tolist()
        
        # Get period boundaries
        pre_data = self.data[self.data['period'] == 'pre']
        test_data = self.data[self.data['period'] == 'test']
        
        pre_period_end = pre_data['date'].max().strftime('%Y-%m-%d')
        post_period_start = test_data['date'].min().strftime('%Y-%m-%d')
        post_period_end = test_data['date'].max().strftime('%Y-%m-%d')
        
        # Aggregate by date for synthetic control
        agg_data = self.data.groupby(['date', 'city']).agg({
            'new_customers': 'sum'
        }).reset_index()
        
        # For single treatment city
        if len(treatment_cities) == 1:
            sc = SyntheticControl(agg_data)
            result = sc.estimate_effect(
                treatment_cities[0],
                control_cities,
                pre_period_end,
                post_period_start,
                post_period_end
            )
            
            return {
                'method': 'Synthetic Control',
                'daily_increment': result['avg_daily_effect'],
                'total_incremental': result['total_incremental'],
                'lift_percent': result['lift_percent'],
                'p_value': None,  # SC doesn't provide p-value directly
                'is_significant': result['ci_lower'] > 0,
                'ci_lower': result['ci_lower'],
                'ci_upper': result['ci_upper'],
                'ci_lower_percent': result['ci_lower_percent'],
                'ci_upper_percent': result['ci_upper_percent'],
                'treatment_avg': result['treatment_avg'],
                'synthetic_avg': result['synthetic_avg'],
                'weights': result['weights'],
                'pre_period_fit': result['pre_period_fit'],
                'test_days': result['n_days']
            }
        else:
            # Multiple treatment cities - fallback to DiD
            return self._calculate_did()
    
    def city_breakdown(self) -> pd.DataFrame:
        """
        Get increment breakdown by city.
        
        Returns:
            DataFrame with city-level statistics
        """
        results = []
        
        for city in self.data['city'].unique():
            city_data = self.data[self.data['city'] == city]
            group = city_data['group'].iloc[0]
            
            pre_avg = city_data[city_data['period'] == 'pre']['new_customers'].mean()
            test_avg = city_data[city_data['period'] == 'test']['new_customers'].mean()
            pre_total = city_data[city_data['period'] == 'pre']['new_customers'].sum()
            test_total = city_data[city_data['period'] == 'test']['new_customers'].sum()
            
            change_pct = ((test_avg - pre_avg) / pre_avg * 100) if pre_avg > 0 else 0
            
            results.append({
                'city': city,
                'group': group,
                'pre_daily_avg': round(pre_avg, 1),
                'test_daily_avg': round(test_avg, 1),
                'change_percent': round(change_pct, 1),
                'pre_total': int(pre_total),
                'test_total': int(test_total)
            })
        
        return pd.DataFrame(results)
    
    def generate_insights(self, increment_result: Dict) -> str:
        """
        Generate human-readable insights from results.
        
        Args:
            increment_result: Result from calculate_increment()
        
        Returns:
            String with insights
        """
        lift = increment_result['lift_percent']
        total = increment_result['total_incremental']
        is_sig = increment_result['is_significant']
        ci_lower = increment_result.get('ci_lower_percent', 0)
        ci_upper = increment_result.get('ci_upper_percent', 0)
        p_value = increment_result.get('p_value')
        
        # Build insight text
        insights = []
        
        # Main result
        if lift > 0:
            insights.append(
                f"📈 El test mostró un incremento de **+{lift:.1f}%** en nuevos clientes."
            )
        else:
            insights.append(
                f"📉 El test mostró una disminución de **{lift:.1f}%** en nuevos clientes."
            )
        
        # Confidence interval
        insights.append(
            f"📊 Intervalo de confianza (95%): **{ci_lower:.1f}%** a **{ci_upper:.1f}%**"
        )
        
        # Statistical significance
        if p_value is not None:
            insights.append(f"🔬 P-value: **{p_value:.4f}**")
        
        if is_sig:
            insights.append("✅ El resultado **ES estadísticamente significativo**.")
        else:
            insights.append("⚠️ El resultado **NO es estadísticamente significativo**.")
        
        # Total impact
        insights.append(
            f"👥 Clientes incrementales totales: **{total:,.0f}**"
        )
        
        # Recommendation
        insights.append("\n**Recomendación:**")
        if is_sig and lift > 5:
            insights.append("🚀 Proceder con el escalado de la campaña a nivel nacional.")
        elif is_sig and lift > 0:
            insights.append("👍 Resultados positivos. Considerar optimizar antes de escalar.")
        elif not is_sig and lift > 0:
            insights.append("🔄 Extender el test o aumentar el presupuesto para mayor certeza.")
        else:
            insights.append("🛑 Revisar la estrategia de campaña antes de continuar.")
        
        return "\n\n".join(insights)
    
    # =========================================
    # NEW FEATURES - GeoLift Enhanced
    # =========================================
    
    def calculate_cumulative_lift(self) -> pd.DataFrame:
        """
        Calculate cumulative lift day by day during the test period.
        Shows how lift evolves over time.
        """
        test_treatment = self.treatment_data[self.treatment_data['period'] == 'test'].copy()
        test_control = self.control_data[self.control_data['period'] == 'test'].copy()
        
        # Get pre-period averages for baseline
        pre_treatment_avg = self.treatment_data[
            self.treatment_data['period'] == 'pre'
        ]['new_customers'].mean()
        
        pre_control_avg = self.control_data[
            self.control_data['period'] == 'pre'
        ]['new_customers'].mean()
        
        # Daily aggregates
        t_daily = test_treatment.groupby('date')['new_customers'].sum().reset_index()
        c_daily = test_control.groupby('date')['new_customers'].sum().reset_index()
        
        # Merge and calculate
        merged = t_daily.merge(c_daily, on='date', suffixes=('_treatment', '_control'))
        merged = merged.sort_values('date')
        
        # Calculate cumulative metrics
        merged['cumsum_treatment'] = merged['new_customers_treatment'].cumsum()
        merged['cumsum_control'] = merged['new_customers_control'].cumsum()
        
        # Calculate expected (counterfactual) based on control's change
        merged['day_num'] = range(1, len(merged) + 1)
        
        # DiD-style cumulative lift
        results = []
        for i, row in merged.iterrows():
            days_elapsed = row['day_num']
            
            # Actual treatment cumsum
            actual_treatment = row['cumsum_treatment']
            
            # Control ratio (how much control changed from baseline)
            control_ratio = row['cumsum_control'] / (pre_control_avg * days_elapsed) if pre_control_avg > 0 else 1
            
            # Expected treatment (if no campaign)
            expected_treatment = pre_treatment_avg * days_elapsed * control_ratio
            
            # Cumulative lift
            cum_lift = actual_treatment - expected_treatment
            cum_lift_pct = (cum_lift / expected_treatment * 100) if expected_treatment > 0 else 0
            
            results.append({
                'date': row['date'],
                'day': days_elapsed,
                'actual_treatment': actual_treatment,
                'expected_treatment': expected_treatment,
                'cumulative_lift': cum_lift,
                'cumulative_lift_pct': cum_lift_pct,
                'daily_treatment': row['new_customers_treatment'],
                'daily_control': row['new_customers_control']
            })
        
        return pd.DataFrame(results)
    
    def run_placebo_test(self, n_simulations: int = 100) -> Dict:
        """
        Run placebo test to validate that there's no effect when there shouldn't be.
        Uses pre-period data to simulate "fake" tests.
        """
        pre_treatment = self.treatment_data[self.treatment_data['period'] == 'pre'].copy()
        pre_control = self.control_data[self.control_data['period'] == 'pre'].copy()
        
        # Need at least 10 days of pre-period
        min_days = min(pre_treatment['date'].nunique(), pre_control['date'].nunique())
        if min_days < 10:
            return {
                'error': 'No hay suficientes datos pre-período para placebo test (mínimo 10 días)',
                'is_valid': None
            }
        
        # Split pre-period in half: first half = "pre", second half = "fake test"
        split_point = min_days // 2
        
        t_daily = pre_treatment.groupby('date')['new_customers'].sum().sort_index()
        c_daily = pre_control.groupby('date')['new_customers'].sum().sort_index()
        
        fake_pre_t = t_daily.iloc[:split_point].values
        fake_test_t = t_daily.iloc[split_point:2*split_point].values
        fake_pre_c = c_daily.iloc[:split_point].values
        fake_test_c = c_daily.iloc[split_point:2*split_point].values
        
        # Calculate DiD on placebo period
        t_pre_mean = np.mean(fake_pre_t)
        t_test_mean = np.mean(fake_test_t)
        c_pre_mean = np.mean(fake_pre_c)
        c_test_mean = np.mean(fake_test_c)
        
        t_change = t_test_mean - t_pre_mean
        c_change = c_test_mean - c_pre_mean
        
        placebo_did = t_change - c_change
        placebo_lift_pct = (placebo_did / t_pre_mean * 100) if t_pre_mean > 0 else 0
        
        # Run bootstrap to get distribution
        placebo_lifts = []
        for _ in range(n_simulations):
            # Resample
            idx_t = np.random.choice(len(fake_test_t), len(fake_test_t), replace=True)
            idx_c = np.random.choice(len(fake_test_c), len(fake_test_c), replace=True)
            
            boot_t_test = np.mean(fake_test_t[idx_t])
            boot_c_test = np.mean(fake_test_c[idx_c])
            
            boot_t_change = boot_t_test - t_pre_mean
            boot_c_change = boot_c_test - c_pre_mean
            boot_did = boot_t_change - boot_c_change
            boot_lift = (boot_did / t_pre_mean * 100) if t_pre_mean > 0 else 0
            placebo_lifts.append(boot_lift)
        
        # Check if 0 is within 95% CI (expected for valid placebo)
        ci_lower = np.percentile(placebo_lifts, 2.5)
        ci_upper = np.percentile(placebo_lifts, 97.5)
        zero_in_ci = ci_lower <= 0 <= ci_upper
        
        return {
            'placebo_lift_pct': placebo_lift_pct,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'zero_in_ci': zero_in_ci,
            'is_valid': zero_in_ci,  # Valid if no effect in placebo
            'interpretation': self._interpret_placebo(placebo_lift_pct, zero_in_ci, ci_lower, ci_upper),
            'distribution': placebo_lifts
        }
    
    def _interpret_placebo(self, lift: float, zero_ok: bool, ci_l: float, ci_u: float) -> str:
        """Interpret placebo test results."""
        if zero_ok:
            return f"✅ Placebo test PASÓ. No se detectó efecto falso (lift: {lift:.1f}%, IC: [{ci_l:.1f}%, {ci_u:.1f}%]). El diseño es válido."
        else:
            return f"⚠️ Placebo test FALLÓ. Se detectó efecto donde no debería haber (lift: {lift:.1f}%). Puede haber problemas con el diseño."
    
    def generate_counterfactual(self) -> pd.DataFrame:
        """
        Generate counterfactual projection: what would have happened without the campaign.
        """
        # Get daily data
        t_pre = self.treatment_data[self.treatment_data['period'] == 'pre'].groupby('date')['new_customers'].sum()
        t_test = self.treatment_data[self.treatment_data['period'] == 'test'].groupby('date')['new_customers'].sum()
        c_pre = self.control_data[self.control_data['period'] == 'pre'].groupby('date')['new_customers'].sum()
        c_test = self.control_data[self.control_data['period'] == 'test'].groupby('date')['new_customers'].sum()
        
        # Pre-period baseline
        t_pre_mean = t_pre.mean()
        c_pre_mean = c_pre.mean()
        ratio = t_pre_mean / c_pre_mean if c_pre_mean > 0 else 1
        
        # Build counterfactual
        results = []
        
        # Pre-period (actual = counterfactual)
        for date in t_pre.index:
            results.append({
                'date': date,
                'period': 'pre',
                'actual': t_pre[date],
                'counterfactual': t_pre[date],
                'lift': 0
            })
        
        # Test period (counterfactual based on control)
        for date in t_test.index:
            actual = t_test[date]
            # Counterfactual: what treatment would be if it followed control's pattern
            control_val = c_test[date] if date in c_test.index else c_pre_mean
            counterfactual = control_val * ratio
            lift = actual - counterfactual
            
            results.append({
                'date': date,
                'period': 'test',
                'actual': actual,
                'counterfactual': counterfactual,
                'lift': lift
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values('date')
        
        return df
    
    def calculate_roi(
        self,
        media_spend: float,
        customer_value: float = 500
    ) -> Dict:
        """
        Calculate ROI from actual test results.
        
        Args:
            media_spend: Total media investment during the test
            customer_value: Average customer lifetime value
        """
        # Get actual increment from DiD
        result = self._calculate_did()
        
        total_incremental = result['total_incremental']
        incremental_revenue = total_incremental * customer_value
        
        # ROI calculations
        roi = ((incremental_revenue - media_spend) / media_spend * 100) if media_spend > 0 else 0
        iroas = incremental_revenue / media_spend if media_spend > 0 else 0
        cpic = media_spend / total_incremental if total_incremental > 0 else float('inf')
        
        # Break-even analysis
        break_even_lift = (media_spend / (result['treatment_pre_avg'] * result['test_days'] * customer_value)) * 100
        
        return {
            'total_incremental_customers': total_incremental,
            'lift_percent': result['lift_percent'],
            'incremental_revenue': incremental_revenue,
            'media_spend': media_spend,
            'roi_percent': roi,
            'iroas': iroas,
            'cost_per_incremental_customer': cpic,
            'customer_value_used': customer_value,
            'is_profitable': roi > 0,
            'break_even_lift_pct': break_even_lift,
            'interpretation': self._interpret_roi_result(roi, iroas, cpic, result['is_significant'])
        }
    
    def _interpret_roi_result(self, roi: float, iroas: float, cpic: float, is_sig: bool) -> str:
        """Interpret ROI results with significance context."""
        sig_note = " (estadísticamente significativo)" if is_sig else " (no significativo, usar con cautela)"
        
        if roi > 100:
            return f"🟢 Excelente ROI{sig_note}: Por cada $1 invertido, ganás ${iroas:.2f}."
        elif roi > 0:
            return f"🟡 ROI positivo{sig_note}: {roi:.0f}%. Costo por cliente: ${cpic:.0f}."
        else:
            return f"🔴 ROI negativo{sig_note}. La campaña no fue rentable."
    
    # =========================================================================
    # NEW: Bootstrap Confidence Intervals for Post-Test
    # =========================================================================
    def calculate_bootstrap_lift_ci(
        self,
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Calculate bootstrap confidence intervals for the lift estimate.
        More robust than parametric methods for geo-experiments.
        
        Args:
            n_bootstrap: Number of bootstrap iterations
            confidence_level: Confidence level (0.95 = 95% CI)
        
        Returns:
            Dict with CI bounds, point estimate, and interpretation
        """
        # Get test period data
        treatment_test = self.treatment_data[self.treatment_data['period'] == 'test']
        control_test = self.control_data[self.control_data['period'] == 'test']
        
        treatment_pre = self.treatment_data[self.treatment_data['period'] == 'pre']
        control_pre = self.control_data[self.control_data['period'] == 'pre']
        
        # Get daily values
        treat_test_daily = treatment_test.groupby('date')['new_customers'].sum().values
        ctrl_test_daily = control_test.groupby('date')['new_customers'].sum().values
        treat_pre_daily = treatment_pre.groupby('date')['new_customers'].sum().values
        ctrl_pre_daily = control_pre.groupby('date')['new_customers'].sum().values
        
        # Point estimate (DiD)
        did_result = self._calculate_did()
        point_estimate = did_result['lift_percent']
        
        # Bootstrap DiD
        np.random.seed(42)
        bootstrap_lifts = []
        
        n_test = len(treat_test_daily)
        n_pre = len(treat_pre_daily)
        
        for _ in range(n_bootstrap):
            # Sample with replacement
            test_idx = np.random.choice(n_test, size=n_test, replace=True)
            pre_idx = np.random.choice(n_pre, size=n_pre, replace=True)
            
            # Bootstrap samples
            boot_treat_test = treat_test_daily[test_idx].mean() if n_test > 0 else 0
            boot_ctrl_test = ctrl_test_daily[test_idx].mean() if n_test > 0 else 0
            boot_treat_pre = treat_pre_daily[pre_idx].mean() if n_pre > 0 else 0
            boot_ctrl_pre = ctrl_pre_daily[pre_idx].mean() if n_pre > 0 else 0
            
            # DiD estimate
            treat_diff = boot_treat_test - boot_treat_pre
            ctrl_diff = boot_ctrl_test - boot_ctrl_pre
            did = treat_diff - ctrl_diff
            
            # Lift percentage
            counterfactual = boot_treat_pre + ctrl_diff
            if counterfactual > 0:
                lift = (did / counterfactual) * 100
                bootstrap_lifts.append(lift)
        
        if not bootstrap_lifts:
            return {'error': 'No se pudieron calcular intervalos de confianza'}
        
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
            'is_significant': not includes_zero and point_estimate > 0,
            'interpretation': self._interpret_bootstrap(point_estimate, ci_lower, ci_upper, includes_zero)
        }
    
    def _interpret_bootstrap(self, point: float, lower: float, upper: float, includes_zero: bool) -> str:
        """Interpret bootstrap CI results for post-test."""
        if includes_zero:
            return f"⚠️ IC Bootstrap [{lower:.1f}%, {upper:.1f}%] incluye el cero. " \
                   f"El efecto ({point:.1f}%) podría deberse al azar."
        elif point > 0:
            return f"✅ Lift de {point:.1f}% con IC Bootstrap [{lower:.1f}%, {upper:.1f}%]. " \
                   f"El efecto es positivo y robusto."
        else:
            return f"🔴 Efecto negativo ({point:.1f}%) con IC [{lower:.1f}%, {upper:.1f}%]."
