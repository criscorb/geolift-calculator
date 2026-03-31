"""
Synthetic Control method for GeoLift analysis.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional


class SyntheticControl:
    """
    Implement Synthetic Control Method for causal inference in geo experiments.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with data.
        
        Args:
            data: DataFrame with columns [city, date, new_customers]
        """
        self.data = data
        self.cities = data['city'].unique().tolist()
    
    def _prepare_matrix(self, metric: str = 'new_customers') -> pd.DataFrame:
        """Pivot data to create city x date matrix."""
        return self.data.pivot_table(
            index='date',
            columns='city',
            values=metric,
            aggfunc='sum'
        ).fillna(0)
    
    def fit_weights(
        self,
        treatment_city: str,
        control_cities: List[str],
        pre_period_end: str
    ) -> Dict:
        """
        Find optimal weights for control cities to create synthetic control.
        
        Args:
            treatment_city: Name of treatment city
            control_cities: List of potential control cities
            pre_period_end: End date of pre-treatment period (YYYY-MM-DD)
        
        Returns:
            Dictionary with weights and fit statistics
        """
        matrix = self._prepare_matrix()
        
        # Filter to pre-period
        pre_period = matrix[matrix.index <= pre_period_end]
        
        # Treatment and control data
        y_treatment = pre_period[treatment_city].values
        X_control = pre_period[control_cities].values
        
        # Optimize weights to minimize pre-period RMSE
        n_controls = len(control_cities)
        
        def objective(weights):
            synthetic = X_control @ weights
            return np.sqrt(np.mean((y_treatment - synthetic) ** 2))
        
        # Constraints: weights sum to 1, all non-negative
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        bounds = [(0, 1) for _ in range(n_controls)]
        
        # Initial weights (equal)
        w0 = np.ones(n_controls) / n_controls
        
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        weights = result.x
        
        # Calculate fit statistics
        synthetic_pre = X_control @ weights
        rmse = np.sqrt(np.mean((y_treatment - synthetic_pre) ** 2))
        r_squared = 1 - (np.sum((y_treatment - synthetic_pre) ** 2) / 
                        np.sum((y_treatment - np.mean(y_treatment)) ** 2))
        
        return {
            'weights': dict(zip(control_cities, weights)),
            'rmse': rmse,
            'r_squared': max(0, r_squared),
            'treatment_city': treatment_city,
            'control_cities': control_cities,
            'pre_period_end': pre_period_end
        }
    
    def estimate_effect(
        self,
        treatment_city: str,
        control_cities: List[str],
        pre_period_end: str,
        post_period_start: str,
        post_period_end: str = None
    ) -> Dict:
        """
        Estimate treatment effect using synthetic control.
        
        Returns:
            Dictionary with effect estimates and confidence intervals
        """
        # Fit weights on pre-period
        fit_result = self.fit_weights(treatment_city, control_cities, pre_period_end)
        weights = np.array(list(fit_result['weights'].values()))
        
        matrix = self._prepare_matrix()
        
        # Filter to post-period
        if post_period_end:
            post_mask = (matrix.index >= post_period_start) & (matrix.index <= post_period_end)
        else:
            post_mask = matrix.index >= post_period_start
        
        post_period = matrix[post_mask]
        
        # Calculate synthetic control in post-period
        y_treatment_post = post_period[treatment_city].values
        X_control_post = post_period[control_cities].values
        synthetic_post = X_control_post @ weights
        
        # Effect estimates
        effects = y_treatment_post - synthetic_post
        total_effect = np.sum(effects)
        avg_daily_effect = np.mean(effects)
        
        # Percentage lift
        avg_synthetic = np.mean(synthetic_post)
        lift_percent = (avg_daily_effect / avg_synthetic * 100) if avg_synthetic > 0 else 0
        
        # Standard error (simple estimate)
        se = np.std(effects) / np.sqrt(len(effects))
        
        # Confidence interval (95%)
        ci_lower = avg_daily_effect - 1.96 * se
        ci_upper = avg_daily_effect + 1.96 * se
        
        return {
            'total_incremental': total_effect,
            'avg_daily_effect': avg_daily_effect,
            'lift_percent': lift_percent,
            'standard_error': se,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_lower_percent': (ci_lower / avg_synthetic * 100) if avg_synthetic > 0 else 0,
            'ci_upper_percent': (ci_upper / avg_synthetic * 100) if avg_synthetic > 0 else 0,
            'treatment_avg': np.mean(y_treatment_post),
            'synthetic_avg': avg_synthetic,
            'n_days': len(effects),
            'weights': fit_result['weights'],
            'pre_period_fit': fit_result['r_squared']
        }
    
    def get_time_series(
        self,
        treatment_city: str,
        control_cities: List[str],
        weights: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Get time series of treatment vs synthetic control.
        
        Returns:
            DataFrame with date, treatment, synthetic columns
        """
        matrix = self._prepare_matrix()
        
        weight_array = np.array([weights.get(c, 0) for c in control_cities])
        synthetic = matrix[control_cities].values @ weight_array
        
        return pd.DataFrame({
            'date': matrix.index,
            'treatment': matrix[treatment_city].values,
            'synthetic_control': synthetic,
            'difference': matrix[treatment_city].values - synthetic
        })
