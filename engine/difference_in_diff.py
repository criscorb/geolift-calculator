"""
Difference-in-Differences (DiD) method for GeoLift analysis.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional


class DifferenceInDiff:
    """
    Implement Difference-in-Differences methodology for geo experiments.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with data.
        
        Args:
            data: DataFrame with columns [city, date, new_customers, group, period]
                  where group is 'treatment' or 'control'
                  and period is 'pre' or 'test'
        """
        self.data = data
    
    def calculate_did(self) -> Dict:
        """
        Calculate DiD estimate.
        
        Returns:
            Dictionary with DiD results
        """
        # Group means
        treatment_pre = self.data[
            (self.data['group'] == 'treatment') & (self.data['period'] == 'pre')
        ]['new_customers'].mean()
        
        treatment_post = self.data[
            (self.data['group'] == 'treatment') & (self.data['period'] == 'test')
        ]['new_customers'].mean()
        
        control_pre = self.data[
            (self.data['group'] == 'control') & (self.data['period'] == 'pre')
        ]['new_customers'].mean()
        
        control_post = self.data[
            (self.data['group'] == 'control') & (self.data['period'] == 'test')
        ]['new_customers'].mean()
        
        # DiD estimate
        treatment_diff = treatment_post - treatment_pre
        control_diff = control_post - control_pre
        did_estimate = treatment_diff - control_diff
        
        # Lift percentage (relative to counterfactual)
        counterfactual = treatment_pre + control_diff
        lift_percent = (did_estimate / counterfactual * 100) if counterfactual > 0 else 0
        
        return {
            'did_estimate': did_estimate,
            'treatment_pre': treatment_pre,
            'treatment_post': treatment_post,
            'control_pre': control_pre,
            'control_post': control_post,
            'treatment_change': treatment_diff,
            'control_change': control_diff,
            'counterfactual': counterfactual,
            'lift_percent': lift_percent
        }
    
    def statistical_test(self) -> Dict:
        """
        Perform statistical test on DiD estimate.
        
        Returns:
            Dictionary with test statistics
        """
        # Get individual observations
        treatment_pre = self.data[
            (self.data['group'] == 'treatment') & (self.data['period'] == 'pre')
        ]['new_customers'].values
        
        treatment_post = self.data[
            (self.data['group'] == 'treatment') & (self.data['period'] == 'test')
        ]['new_customers'].values
        
        control_pre = self.data[
            (self.data['group'] == 'control') & (self.data['period'] == 'pre')
        ]['new_customers'].values
        
        control_post = self.data[
            (self.data['group'] == 'control') & (self.data['period'] == 'test')
        ]['new_customers'].values
        
        # Calculate individual DiD effects
        # Simplified: compare post-period differences
        treatment_changes = treatment_post[:min(len(treatment_post), len(treatment_pre))] - \
                          treatment_pre[:min(len(treatment_post), len(treatment_pre))]
        control_changes = control_post[:min(len(control_post), len(control_pre))] - \
                         control_pre[:min(len(control_post), len(control_pre))]
        
        # Two-sample t-test on changes
        if len(treatment_changes) > 1 and len(control_changes) > 1:
            t_stat, p_value = stats.ttest_ind(treatment_changes, control_changes)
        else:
            # Not enough data for t-test, use simple comparison
            t_stat = 0
            p_value = 1.0
        
        # Standard error of DiD
        n_t = len(treatment_post)
        n_c = len(control_post)
        
        var_treatment = np.var(treatment_post, ddof=1) if n_t > 1 else 0
        var_control = np.var(control_post, ddof=1) if n_c > 1 else 0
        
        se = np.sqrt(var_treatment/n_t + var_control/n_c) if (n_t > 0 and n_c > 0) else 0
        
        # DiD estimate
        did_result = self.calculate_did()
        did_estimate = did_result['did_estimate']
        
        # Confidence interval
        ci_lower = did_estimate - 1.96 * se
        ci_upper = did_estimate + 1.96 * se
        
        # Lift CI
        counterfactual = did_result['counterfactual']
        ci_lower_pct = (ci_lower / counterfactual * 100) if counterfactual > 0 else 0
        ci_upper_pct = (ci_upper / counterfactual * 100) if counterfactual > 0 else 0
        
        return {
            't_statistic': t_stat,
            'p_value': p_value,
            'standard_error': se,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'ci_lower_percent': ci_lower_pct,
            'ci_upper_percent': ci_upper_pct,
            'is_significant': p_value < 0.05,
            'n_treatment': n_t,
            'n_control': n_c
        }
    
    def get_summary_table(self) -> pd.DataFrame:
        """
        Get summary table by group and period.
        
        Returns:
            DataFrame with summary statistics
        """
        summary = self.data.groupby(['group', 'period']).agg({
            'new_customers': ['mean', 'std', 'count', 'sum']
        }).round(2)
        
        summary.columns = ['mean', 'std', 'n_days', 'total']
        
        return summary.reset_index()
    
    def get_city_breakdown(self) -> pd.DataFrame:
        """
        Get breakdown by city.
        
        Returns:
            DataFrame with city-level statistics
        """
        city_stats = self.data.groupby(['city', 'group', 'period']).agg({
            'new_customers': ['mean', 'sum', 'count']
        }).round(2)
        
        city_stats.columns = ['daily_avg', 'total', 'n_days']
        
        return city_stats.reset_index()


def prepare_did_data(
    data: pd.DataFrame,
    treatment_cities: List[str],
    control_cities: List[str],
    pre_period_end: str,
    test_period_start: str
) -> pd.DataFrame:
    """
    Prepare data for DiD analysis from raw format.
    
    Args:
        data: Raw data with columns [city, date, new_customers]
        treatment_cities: List of treatment city names
        control_cities: List of control city names
        pre_period_end: End of pre-period (YYYY-MM-DD)
        test_period_start: Start of test period (YYYY-MM-DD)
    
    Returns:
        DataFrame ready for DiD analysis
    """
    df = data.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Assign groups
    df['group'] = df['city'].apply(
        lambda x: 'treatment' if x in treatment_cities 
                  else ('control' if x in control_cities else 'other')
    )
    
    # Filter to treatment and control only
    df = df[df['group'].isin(['treatment', 'control'])]
    
    # Assign periods
    pre_end = pd.to_datetime(pre_period_end)
    test_start = pd.to_datetime(test_period_start)
    
    df['period'] = df['date'].apply(
        lambda x: 'pre' if x <= pre_end else ('test' if x >= test_start else 'gap')
    )
    
    # Filter out gap period
    df = df[df['period'].isin(['pre', 'test'])]
    
    return df
