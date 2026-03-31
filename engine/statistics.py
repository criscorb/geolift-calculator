"""
Statistical utility functions for GeoLift calculations.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Optional


def z_score(confidence_level: float) -> float:
    """Get z-score for a given confidence level (one-tailed)."""
    return stats.norm.ppf(1 - (1 - confidence_level) / 2)


def calculate_power(
    effect_size: float,
    std_dev: float,
    n_treatment: int,
    n_control: int,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for a two-sample test.
    
    Args:
        effect_size: Expected effect size (absolute difference)
        std_dev: Standard deviation of the metric
        n_treatment: Sample size in treatment group
        n_control: Sample size in control group
        alpha: Significance level
    
    Returns:
        Statistical power (0 to 1)
    """
    if std_dev == 0 or effect_size == 0:
        return 0.0
    
    # Pooled standard error
    se = std_dev * np.sqrt(1/n_treatment + 1/n_control)
    
    # Non-centrality parameter
    ncp = effect_size / se
    
    # Critical value
    z_alpha = stats.norm.ppf(1 - alpha/2)
    
    # Power calculation
    power = 1 - stats.norm.cdf(z_alpha - ncp) + stats.norm.cdf(-z_alpha - ncp)
    
    return min(max(power, 0), 1)


def calculate_mde(
    std_dev: float,
    n_treatment: int,
    n_control: int,
    alpha: float = 0.05,
    power: float = 0.80
) -> float:
    """
    Calculate Minimum Detectable Effect (MDE).
    
    Args:
        std_dev: Standard deviation of the metric
        n_treatment: Sample size in treatment group
        n_control: Sample size in control group
        alpha: Significance level
        power: Desired statistical power
    
    Returns:
        Minimum detectable effect (absolute)
    """
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    se = std_dev * np.sqrt(1/n_treatment + 1/n_control)
    
    mde = (z_alpha + z_beta) * se
    
    return mde


def calculate_sample_size(
    effect_size: float,
    std_dev: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> Tuple[int, int]:
    """
    Calculate required sample size for treatment and control.
    
    Args:
        effect_size: Expected effect size (absolute)
        std_dev: Standard deviation
        alpha: Significance level
        power: Desired power
        ratio: Ratio of control to treatment size
    
    Returns:
        Tuple of (n_treatment, n_control)
    """
    if effect_size == 0:
        return (float('inf'), float('inf'))
    
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    # Sample size formula
    n_treatment = ((z_alpha + z_beta) ** 2 * std_dev ** 2 * (1 + 1/ratio)) / (effect_size ** 2)
    n_control = n_treatment * ratio
    
    return (int(np.ceil(n_treatment)), int(np.ceil(n_control)))


def t_test_two_sample(
    treatment_data: np.ndarray,
    control_data: np.ndarray,
    alternative: str = 'two-sided'
) -> Tuple[float, float, float]:
    """
    Perform two-sample t-test.
    
    Args:
        treatment_data: Array of treatment observations
        control_data: Array of control observations
        alternative: 'two-sided', 'greater', or 'less'
    
    Returns:
        Tuple of (t_statistic, p_value, effect_size)
    """
    t_stat, p_value = stats.ttest_ind(treatment_data, control_data, alternative=alternative)
    
    effect_size = np.mean(treatment_data) - np.mean(control_data)
    
    return (t_stat, p_value, effect_size)


def confidence_interval(
    effect: float,
    std_error: float,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for an effect.
    
    Args:
        effect: Point estimate of effect
        std_error: Standard error of the estimate
        confidence: Confidence level
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    lower = effect - z * std_error
    upper = effect + z * std_error
    
    return (lower, upper)


class StatisticalTests:
    """Class for performing statistical tests on GeoLift data."""
    
    @staticmethod
    def calculate_lift(treatment_mean: float, control_mean: float) -> float:
        """Calculate percentage lift."""
        if control_mean == 0:
            return 0.0
        return ((treatment_mean - control_mean) / control_mean) * 100
    
    @staticmethod
    def pooled_std(group1: np.ndarray, group2: np.ndarray) -> float:
        """Calculate pooled standard deviation."""
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
        return np.sqrt(pooled_var)
    
    @staticmethod
    def is_significant(p_value: float, alpha: float = 0.05) -> bool:
        """Check if result is statistically significant."""
        return p_value < alpha
