# GeoLift Calculator Engine
# Marketing Intelligence Tool

from .power_analysis import PowerAnalysis
from .increment_calc import IncrementCalculator
from .difference_in_diff import DifferenceInDiff, prepare_did_data
from .synthetic_control import SyntheticControl
from .statistics import calculate_power, calculate_mde, calculate_sample_size
from .utils import (
    validate_data, 
    parse_dates_flexible, 
    detect_date_format,
    calculate_data_quality_score, 
    get_faq_content, 
    create_scenario_comparison,
    get_outlier_details,
    detect_and_handle_outliers,
    interpolate_missing_days,
    setup_logger,
    log_action,
    get_metric_tooltip,
    METRIC_TOOLTIPS
)
from .history import TestHistory
from .visualizations import (
    create_sparkline,
    create_sparkline_html,
    create_power_gauge,
    create_comparison_chart,
    create_lift_waterfall,
    create_mde_heatmap_chart,
    generate_pdf_report,
    export_to_excel_with_charts,
    get_presentation_css
)

__all__ = [
    'PowerAnalysis',
    'IncrementCalculator',
    'DifferenceInDiff',
    'prepare_did_data',
    'SyntheticControl',
    'calculate_power',
    'calculate_mde',
    'calculate_sample_size',
    'validate_data',
    'parse_dates_flexible',
    'detect_date_format',
    'calculate_data_quality_score',
    'get_faq_content',
    'create_scenario_comparison',
    'get_outlier_details',
    'detect_and_handle_outliers',
    'interpolate_missing_days',
    'setup_logger',
    'log_action',
    'get_metric_tooltip',
    'METRIC_TOOLTIPS',
    'TestHistory',
    # Visualizations
    'create_sparkline',
    'create_sparkline_html',
    'create_power_gauge',
    'create_comparison_chart',
    'create_lift_waterfall',
    'create_mde_heatmap_chart',
    'generate_pdf_report',
    'export_to_excel_with_charts',
    'get_presentation_css'
]

__version__ = '2.2.0'
