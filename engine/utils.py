# -*- coding: utf-8 -*-
"""
Utility functions for GeoLift Calculator
Data validation, date parsing, caching helpers
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re


def detect_date_format(date_str: str) -> Optional[str]:
    """
    Auto-detect date format from a string.
    Supports: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY
    """
    patterns = [
        (r'^\d{4}-\d{2}-\d{2}$', '%Y-%m-%d'),      # 2024-01-15
        (r'^\d{2}/\d{2}/\d{4}$', '%d/%m/%Y'),      # 15/01/2024
        (r'^\d{2}-\d{2}-\d{4}$', '%d-%m-%Y'),      # 15-01-2024
        (r'^\d{4}/\d{2}/\d{2}$', '%Y/%m/%d'),      # 2024/01/15
    ]
    
    for pattern, fmt in patterns:
        if re.match(pattern, str(date_str).strip()):
            return fmt
    return None


def parse_dates_flexible(df: pd.DataFrame, date_column: str = 'date') -> Tuple[pd.DataFrame, str]:
    """
    Parse dates with auto-detection of format.
    Returns: (DataFrame with parsed dates, detected format)
    """
    if date_column not in df.columns:
        raise ValueError(f"Column '{date_column}' not found")
    
    # Get sample date
    sample = str(df[date_column].dropna().iloc[0])
    detected_format = detect_date_format(sample)
    
    if detected_format:
        df[date_column] = pd.to_datetime(df[date_column], format=detected_format)
    else:
        # Fallback to pandas auto-detection (modern approach)
        df[date_column] = pd.to_datetime(df[date_column], format='mixed', dayfirst=True)
        detected_format = 'auto-detected'
    
    return df, detected_format


def validate_data(df: pd.DataFrame, required_columns: List[str]) -> Dict:
    """
    Comprehensive data validation.
    Returns dict with validation results and warnings.
    """
    results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    # Check required columns
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        results['is_valid'] = False
        results['errors'].append(f"Columnas faltantes: {', '.join(missing)}")
        return results
    
    # Check for empty data
    if len(df) == 0:
        results['is_valid'] = False
        results['errors'].append("El archivo está vacío")
        return results
    
    # Check for null values in required columns
    for col in required_columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            pct = (null_count / len(df)) * 100
            results['warnings'].append(f"⚠️ {col}: {null_count} valores nulos ({pct:.1f}%)")
            if pct > 20:
                results['errors'].append(f"Demasiados valores nulos en {col}: {pct:.1f}%")
                results['is_valid'] = False
    
    # Numeric validation for new_customers
    if 'new_customers' in df.columns:
        # Check for negative values
        neg_count = (df['new_customers'] < 0).sum()
        if neg_count > 0:
            results['warnings'].append(f"⚠️ {neg_count} valores negativos en new_customers")
        
        # Check for outliers (IQR method)
        Q1 = df['new_customers'].quantile(0.25)
        Q3 = df['new_customers'].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = ((df['new_customers'] < lower) | (df['new_customers'] > upper)).sum()
        if outliers > 0:
            pct = (outliers / len(df)) * 100
            results['warnings'].append(f"📊 {outliers} outliers detectados ({pct:.1f}%) - valores muy altos o bajos")
            results['stats']['outliers'] = outliers
            results['stats']['outlier_bounds'] = (lower, upper)
    
    # Date validation
    if 'date' in df.columns:
        try:
            df_temp = df.copy()
            df_temp, fmt = parse_dates_flexible(df_temp, 'date')
            results['stats']['date_format'] = fmt
            
            # Check for duplicate dates per city
            if 'city' in df.columns:
                duplicates = df_temp.groupby(['city', 'date']).size()
                dup_count = (duplicates > 1).sum()
                if dup_count > 0:
                    results['warnings'].append(f"⚠️ {dup_count} fechas duplicadas por ciudad")
                
                # Check for missing days
                for city in df_temp['city'].unique():
                    city_data = df_temp[df_temp['city'] == city].sort_values('date')
                    if len(city_data) > 1:
                        date_range = pd.date_range(
                            city_data['date'].min(), 
                            city_data['date'].max()
                        )
                        missing_days = len(date_range) - len(city_data)
                        if missing_days > 0:
                            pct = (missing_days / len(date_range)) * 100
                            if pct > 5:
                                results['warnings'].append(
                                    f"📅 {city}: {missing_days} días faltantes ({pct:.1f}%)"
                                )
                
            results['stats']['date_range'] = (
                df_temp['date'].min().strftime('%Y-%m-%d'),
                df_temp['date'].max().strftime('%Y-%m-%d')
            )
            results['stats']['total_days'] = (df_temp['date'].max() - df_temp['date'].min()).days + 1
            
        except Exception as e:
            results['warnings'].append(f"⚠️ Error parseando fechas: {str(e)}")
    
    # City validation
    if 'city' in df.columns:
        cities = df['city'].nunique()
        results['stats']['n_cities'] = cities
        if cities < 3:
            results['warnings'].append("⚠️ Menos de 3 ciudades - análisis limitado")
        
        # Check for cities with very few data points
        city_counts = df.groupby('city').size()
        low_data_cities = city_counts[city_counts < 14].index.tolist()
        if low_data_cities:
            results['warnings'].append(
                f"⚠️ Ciudades con <14 días de datos: {', '.join(low_data_cities)}"
            )
    
    return results


def get_outlier_details(df: pd.DataFrame, column: str = 'new_customers') -> pd.DataFrame:
    """
    Get detailed information about outliers.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    
    outliers = df[(df[column] < lower) | (df[column] > upper)].copy()
    outliers['outlier_type'] = np.where(outliers[column] < lower, 'Bajo', 'Alto')
    
    return outliers


def calculate_data_quality_score(validation_results: Dict) -> int:
    """
    Calculate overall data quality score (0-100).
    """
    score = 100
    
    # Deduct for errors
    score -= len(validation_results.get('errors', [])) * 25
    
    # Deduct for warnings
    warnings = validation_results.get('warnings', [])
    for w in warnings:
        if 'outliers' in w.lower():
            score -= 5
        elif 'faltantes' in w.lower() or 'missing' in w.lower():
            score -= 10
        elif 'duplicadas' in w.lower():
            score -= 8
        else:
            score -= 3
    
    return max(0, min(100, score))


def format_number(n: float, decimals: int = 0) -> str:
    """Format number with thousand separators."""
    if decimals == 0:
        return f"{int(n):,}".replace(",", ".")
    return f"{n:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_faq_content() -> List[Dict]:
    """Return FAQ content for help section."""
    return [
        {
            "question": "¿Qué es un GeoLift Test?",
            "answer": """
            Un GeoLift Test es un experimento de marketing que mide el **impacto incremental** 
            de una campaña comparando ciudades donde se ejecuta la campaña (tratamiento) vs 
            ciudades donde no se ejecuta (control).
            
            Es el estándar de la industria para medir la efectividad real del marketing,
            eliminando sesgos y factores externos.
            """
        },
        {
            "question": "¿Cuántos días de datos históricos necesito?",
            "answer": """
            **Mínimo recomendado: 30 días**
            
            - 30-60 días: Aceptable para tests cortos
            - 60-90 días: Ideal para la mayoría de casos
            - 90+ días: Óptimo para alta precisión
            
            Más datos = estimaciones más estables y confiables.
            """
        },
        {
            "question": "¿Cómo elijo ciudades de control?",
            "answer": """
            Las ciudades de control deben ser **similares** a las de tratamiento:
            
            ✅ Tamaño de población comparable
            ✅ Comportamiento histórico similar
            ✅ Sin eventos especiales durante el test
            ✅ Sin spillover (no deben ser vecinas cercanas)
            
            Usá la recomendación automática como punto de partida.
            """
        },
        {
            "question": "¿Qué significa poder estadístico del 80%?",
            "answer": """
            Significa que tenés **80% de probabilidad de detectar** el efecto de tu campaña
            si realmente existe.
            
            - <60%: Riesgo alto de no detectar el efecto
            - 60-80%: Aceptable con precaución
            - 80%+: Estándar de la industria ✅
            - 90%+: Excelente para decisiones críticas
            """
        },
        {
            "question": "¿Qué es el MDE (Minimum Detectable Effect)?",
            "answer": """
            Es el **lift mínimo que tu test puede detectar** con confianza estadística.
            
            Ejemplo: Si tu MDE es 12%, solo podrás detectar lifts de 12% o más.
            Lifts menores podrían existir pero no serán estadísticamente significativos.
            
            **Tu MDE debe ser menor al lift que esperas.**
            """
        },
        {
            "question": "¿Cuánto debe durar mi test?",
            "answer": """
            Depende del poder estadístico deseado y el lift esperado:
            
            - **Mínimo absoluto:** 7 días (alta variabilidad)
            - **Mínimo recomendado:** 14 días
            - **Ideal:** 21-28 días
            - **Máximo típico:** 42-56 días
            
            Usá el gráfico de "Poder vs Duración" para encontrar tu punto óptimo.
            """
        },
        {
            "question": "¿Qué es Diferencias en Diferencias (DiD)?",
            "answer": """
            Es el método estadístico principal para analizar GeoLift tests.
            
            Compara el **cambio** en tratamiento vs el **cambio** en control:
            
            `Lift = (Trat_post - Trat_pre) - (Ctrl_post - Ctrl_pre)`
            
            Esto elimina factores externos que afectan a ambos grupos por igual.
            """
        },
        {
            "question": "¿Qué es una Ciudad Sintética?",
            "answer": """
            Cuando no tenés una ciudad de control perfecta, podés crear una **combinación 
            ponderada** de varias ciudades que juntas se parecen al tratamiento.
            
            Ejemplo: Ciudad Sintética = 40% Córdoba + 35% Rosario + 25% Mendoza
            
            El algoritmo encuentra los pesos óptimos automáticamente.
            """
        },
        {
            "question": "¿Cómo interpreto el p-value?",
            "answer": """
            El p-value indica la probabilidad de ver estos resultados **por azar**.
            
            - **p < 0.05:** Estadísticamente significativo ✅
            - **p < 0.01:** Muy significativo ✅✅
            - **p > 0.05:** No significativo (podría ser azar) ⚠️
            
            Un p-value bajo significa que el efecto es real, no casualidad.
            """
        },
        {
            "question": "¿Qué es el iROAS?",
            "answer": """
            **iROAS** = Incremental Return on Ad Spend
            
            Mide cuántos pesos de revenue **incremental** generás por cada peso invertido.
            
            - iROAS > 1: Rentable ✅ (cada $1 genera más de $1)
            - iROAS = 1: Break-even
            - iROAS < 1: No rentable ❌
            
            Es la métrica más importante para decisiones de inversión.
            """
        }
    ]


def create_scenario_comparison(scenarios: List[Dict]) -> pd.DataFrame:
    """
    Create a comparison table for multiple test scenarios.
    """
    if not scenarios:
        return pd.DataFrame()
    
    comparison_data = []
    for i, scenario in enumerate(scenarios, 1):
        comparison_data.append({
            'Escenario': f"#{i}: {scenario.get('name', 'Sin nombre')}",
            'Tratamiento': ', '.join(scenario.get('treatment', [])),
            'Control': ', '.join(scenario.get('control', [])),
            'Duración': f"{scenario.get('duration', 0)} días",
            'Lift Esperado': f"{scenario.get('expected_lift', 0)*100:.0f}%",
            'Poder': f"{scenario.get('power', 0):.0f}%",
            'MDE': f"{scenario.get('mde', 0):.1f}%",
            'Viable': '✅' if scenario.get('power', 0) >= 80 else '⚠️'
        })
    
    return pd.DataFrame(comparison_data)


# ============================================
# NEW: OUTLIER DETECTION & EXCLUSION
# ============================================
def detect_and_handle_outliers(
    df: pd.DataFrame, 
    column: str = 'new_customers',
    method: str = 'iqr',  # 'iqr', 'zscore', 'percentile'
    action: str = 'flag',  # 'flag', 'exclude', 'cap', 'interpolate'
    threshold: float = 1.5
) -> Tuple[pd.DataFrame, Dict]:
    """
    Detect and optionally handle outliers in data.
    
    Args:
        df: DataFrame with data
        column: Column to check for outliers
        method: Detection method ('iqr', 'zscore', 'percentile')
        action: How to handle outliers:
            - 'flag': Just mark them (add outlier column)
            - 'exclude': Remove outlier rows
            - 'cap': Cap values at bounds (winsorize)
            - 'interpolate': Replace with interpolated values
        threshold: Sensitivity (1.5 for IQR, 3 for zscore, 0.01 for percentile)
    
    Returns:
        (processed_df, stats_dict)
    """
    df_result = df.copy()
    stats = {
        'total_rows': len(df),
        'outliers_found': 0,
        'outlier_indices': [],
        'bounds': {},
        'method': method,
        'action': action
    }
    
    if column not in df.columns:
        return df_result, {'error': f'Column {column} not found'}
    
    values = df[column].dropna()
    
    # Detect outliers based on method
    if method == 'iqr':
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - threshold * IQR
        upper = Q3 + threshold * IQR
        is_outlier = (df[column] < lower) | (df[column] > upper)
        stats['bounds'] = {'lower': lower, 'upper': upper, 'Q1': Q1, 'Q3': Q3, 'IQR': IQR}
        
    elif method == 'zscore':
        mean = values.mean()
        std = values.std()
        z_scores = np.abs((df[column] - mean) / std)
        is_outlier = z_scores > threshold
        lower = mean - threshold * std
        upper = mean + threshold * std
        stats['bounds'] = {'lower': lower, 'upper': upper, 'mean': mean, 'std': std}
        
    elif method == 'percentile':
        lower = values.quantile(threshold)
        upper = values.quantile(1 - threshold)
        is_outlier = (df[column] < lower) | (df[column] > upper)
        stats['bounds'] = {'lower': lower, 'upper': upper}
    
    else:
        return df_result, {'error': f'Unknown method: {method}'}
    
    outlier_indices = df[is_outlier].index.tolist()
    stats['outliers_found'] = len(outlier_indices)
    stats['outlier_indices'] = outlier_indices
    stats['outlier_percent'] = len(outlier_indices) / len(df) * 100
    
    # Handle outliers based on action
    if action == 'flag':
        df_result['is_outlier'] = is_outlier
        df_result['outlier_type'] = np.where(
            df[column] < stats['bounds']['lower'], 'low',
            np.where(df[column] > stats['bounds']['upper'], 'high', 'normal')
        )
        
    elif action == 'exclude':
        df_result = df_result[~is_outlier].reset_index(drop=True)
        stats['rows_removed'] = len(outlier_indices)
        
    elif action == 'cap':
        df_result[column] = df_result[column].clip(
            lower=stats['bounds']['lower'],
            upper=stats['bounds']['upper']
        )
        stats['values_capped'] = len(outlier_indices)
        
    elif action == 'interpolate':
        # Replace outliers with NaN and interpolate
        df_result.loc[is_outlier, column] = np.nan
        if 'date' in df_result.columns:
            df_result = df_result.sort_values('date')
        df_result[column] = df_result[column].interpolate(method='linear')
        # Fill any remaining NaN at edges
        df_result[column] = df_result[column].fillna(method='bfill').fillna(method='ffill')
        stats['values_interpolated'] = len(outlier_indices)
    
    return df_result, stats


# ============================================
# NEW: MISSING DAYS INTERPOLATION
# ============================================
def interpolate_missing_days(
    df: pd.DataFrame,
    date_column: str = 'date',
    value_column: str = 'new_customers',
    group_column: str = 'city',
    method: str = 'linear'  # 'linear', 'time', 'spline', 'polynomial'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Fill in missing days with interpolated values.
    
    Args:
        df: DataFrame with time series data
        date_column: Name of date column
        value_column: Name of value column to interpolate
        group_column: Group by this column (e.g., 'city')
        method: Interpolation method
    
    Returns:
        (df_filled, stats_dict)
    """
    stats = {
        'total_days_added': 0,
        'by_group': {}
    }
    
    df_result = df.copy()
    
    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df_result[date_column]):
        df_result, _ = parse_dates_flexible(df_result, date_column)
    
    filled_dfs = []
    
    for group_name in df_result[group_column].unique():
        group_df = df_result[df_result[group_column] == group_name].copy()
        group_df = group_df.sort_values(date_column)
        
        # Create complete date range
        min_date = group_df[date_column].min()
        max_date = group_df[date_column].max()
        full_range = pd.date_range(min_date, max_date, freq='D')
        
        # Find missing days
        existing_dates = set(group_df[date_column])
        missing_dates = [d for d in full_range if d not in existing_dates]
        
        if missing_dates:
            # Create rows for missing dates
            for missing_date in missing_dates:
                new_row = {date_column: missing_date, group_column: group_name}
                # Copy constant columns from existing data
                for col in group_df.columns:
                    if col not in [date_column, group_column, value_column]:
                        if group_df[col].nunique() == 1:
                            new_row[col] = group_df[col].iloc[0]
                        else:
                            new_row[col] = np.nan
                new_row[value_column] = np.nan
                group_df = pd.concat([group_df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Sort and interpolate
            group_df = group_df.sort_values(date_column)
            group_df[value_column] = group_df[value_column].interpolate(method=method)
            group_df['interpolated'] = group_df[date_column].isin(missing_dates)
            
            stats['by_group'][group_name] = len(missing_dates)
            stats['total_days_added'] += len(missing_dates)
        else:
            group_df['interpolated'] = False
        
        filled_dfs.append(group_df)
    
    result = pd.concat(filled_dfs, ignore_index=True)
    result = result.sort_values([group_column, date_column]).reset_index(drop=True)
    
    return result, stats


# ============================================
# NEW: LOGGING FOR PRODUCTION
# ============================================
import logging
from datetime import datetime as dt

def setup_logger(name: str = 'geolift', level: str = 'INFO') -> logging.Logger:
    """
    Setup logger for production debugging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # File handler
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'geolift_{dt.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger


def log_action(action: str, details: Dict = None, level: str = 'info'):
    """
    Log an action for debugging.
    """
    logger = setup_logger()
    message = action
    if details:
        detail_str = ' | '.join([f'{k}={v}' for k, v in details.items()])
        message = f'{action} | {detail_str}'
    
    getattr(logger, level.lower())(message)


# ============================================
# NEW: METRIC TOOLTIPS
# ============================================
METRIC_TOOLTIPS = {
    'power': {
        'name': 'Poder Estadístico',
        'description': 'Probabilidad de detectar el efecto si realmente existe.',
        'interpretation': {
            'good': '≥80% - Estándar de la industria',
            'warning': '60-79% - Aceptable con precaución',
            'bad': '<60% - Riesgo alto de no detectar efecto'
        },
        'formula': 'P(rechazar H0 | H1 verdadera)'
    },
    'mde': {
        'name': 'MDE (Mínimo Efecto Detectable)',
        'description': 'El lift más pequeño que tu test puede detectar con significancia estadística.',
        'interpretation': {
            'good': 'MDE < Lift esperado',
            'bad': 'MDE ≥ Lift esperado - No podrás detectar tu efecto'
        },
        'formula': 'δ = t(α) + t(β) × σ / √n'
    },
    'lift': {
        'name': 'Lift (%)',
        'description': 'Incremento porcentual en la métrica objetivo atribuible a la campaña.',
        'interpretation': {
            'good': 'Positivo y significativo',
            'neutral': 'Cercano a 0 o no significativo',
            'bad': 'Negativo - La campaña tuvo efecto adverso'
        },
        'formula': '(Tratamiento_post - Counterfactual) / Counterfactual × 100'
    },
    'p_value': {
        'name': 'P-Value',
        'description': 'Probabilidad de observar estos resultados si no hubiera efecto real.',
        'interpretation': {
            'good': '<0.05 - Estadísticamente significativo',
            'warning': '0.05-0.10 - Marginalmente significativo',
            'bad': '>0.10 - No significativo'
        },
        'formula': 'P(datos | H0)'
    },
    'iroas': {
        'name': 'iROAS (Incremental Return on Ad Spend)',
        'description': 'Retorno incremental por cada peso invertido en publicidad.',
        'interpretation': {
            'good': '>1.0 - Rentable, cada $1 genera más de $1',
            'neutral': '=1.0 - Break-even',
            'bad': '<1.0 - No rentable'
        },
        'formula': 'Revenue Incremental / Inversión'
    },
    'roi': {
        'name': 'ROI (%)',
        'description': 'Retorno sobre la inversión como porcentaje.',
        'interpretation': {
            'good': '>100% - Excelente',
            'neutral': '0-100% - Positivo',
            'bad': '<0% - Pérdida'
        },
        'formula': '(Revenue - Inversión) / Inversión × 100'
    },
    'confidence': {
        'name': 'Nivel de Confianza',
        'description': 'Probabilidad de que el intervalo contenga el valor real.',
        'interpretation': {
            'standard': '95% - Estándar de la industria',
            'strict': '99% - Para decisiones críticas'
        }
    },
    'match_score': {
        'name': 'Market Matching Score',
        'description': 'Qué tan similares son las ciudades de control vs tratamiento.',
        'interpretation': {
            'good': '≥60% - Buen match',
            'warning': '40-60% - Match aceptable',
            'bad': '<40% - Match pobre, revisar selección'
        }
    }
}

def get_metric_tooltip(metric_key: str) -> Dict:
    """Get tooltip information for a metric."""
    return METRIC_TOOLTIPS.get(metric_key, {
        'name': metric_key,
        'description': 'Sin descripción disponible'
    })
