"""
Pre-Test Calculator - Plan your GeoLift experiment
Marketing Intelligence Tool
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import sys
import os
import datetime
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.power_analysis import PowerAnalysis
from engine.statistics import calculate_power, calculate_mde
from engine.utils import (
    validate_data, parse_dates_flexible, get_outlier_details,
    calculate_data_quality_score, get_faq_content, create_scenario_comparison
)
from engine.history import TestHistory

# Initialize history
test_history = TestHistory()

st.set_page_config(page_title="Pre-Test Calculator", page_icon="📊", layout="wide")

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    :root {
        --primary-navy: #002F6C;
        --primary-gold: #C6A34F;
        --primary-red: #E31837;
        --primary-light-gold: #F5EBD7;
        --primary-cream: #FAF8F3;
        --primary-success: #2E7D32;
        --primary-warning: #F57C00;
    }
    
    .stApp {
        background: linear-gradient(180deg, var(--primary-cream) 0%, #ffffff 100%);
    }
    
    /* Headers */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--primary-navy);
        margin-bottom: 4px;
    }
    
    .main-title span {
        color: var(--primary-gold);
    }
    
    .subtitle {
        color: #666;
        font-size: 1rem;
        margin-bottom: 32px;
        font-weight: 400;
    }
    
    /* Progress Steps */
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .step-circle {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 8px;
        transition: all 0.3s;
    }
    
    .step-done {
        background: var(--primary-success);
        color: white;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }
    
    .step-active {
        background: var(--primary-navy);
        color: white;
        box-shadow: 0 4px 12px rgba(0, 47, 108, 0.4);
    }
    
    .step-pending {
        background: #e0e0e0;
        color: #999;
    }
    
    .step-label {
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .step-label-done { color: var(--primary-success); }
    .step-label-active { color: var(--primary-navy); }
    .step-label-pending { color: #999; }
    
    /* Force dark text on light backgrounds */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-navy) !important;
    }
    
    .stMarkdown h5 {
        color: var(--primary-navy) !important;
        font-weight: 600 !important;
    }
    
    .stMarkdown p, .stMarkdown span {
        color: #333 !important;
    }
    
    .stCaption, .stCaption p {
        color: #666 !important;
    }
    
    label, .stRadio label, .stCheckbox label {
        color: #333 !important;
    }
    
    /* Cards */
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 28px;
        box-shadow: 0 2px 16px rgba(0,47,108,0.06);
        border: 1px solid rgba(198,163,79,0.15);
        margin-bottom: 24px;
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--primary-navy);
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        border: 1px solid #eee;
        transition: all 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-navy);
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #888;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-good { border-left: 4px solid var(--primary-success); }
    .metric-warning { border-left: 4px solid var(--primary-warning); }
    .metric-bad { border-left: 4px solid var(--primary-red); }
    
    /* Alert Boxes */
    .info-box {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #2196F3;
        margin: 16px 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid var(--primary-success);
        margin: 16px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid var(--primary-warning);
        margin: 16px 0;
    }
    
    .gold-box {
        background: linear-gradient(135deg, var(--primary-light-gold) 0%, #F8F3E8 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid var(--primary-gold);
        margin: 16px 0;
    }
    
    /* City chips */
    .city-chip {
        display: inline-block;
        background: var(--primary-navy);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        margin: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .city-chip-control {
        background: var(--primary-gold);
        color: var(--primary-navy);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-navy) 0%, #004494 100%);
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #003d80 0%, var(--primary-navy) 100%);
        box-shadow: 0 4px 15px rgba(0, 47, 108, 0.3);
    }
    
    /* Data table */
    .dataframe {
        border: none !important;
    }
    
    .dataframe th {
        background: var(--primary-navy) !important;
        color: white !important;
    }
    
    /* Plotly charts */
    .js-plotly-plot .plotly .modebar {
        top: 5px !important;
        right: 5px !important;
    }
    
    /* Loading spinner overlay */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255,255,255,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
    
    /* Data quality badge */
    .quality-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .quality-excellent { background: #C8E6C9; color: #2E7D32; }
    .quality-good { background: #DCEDC8; color: #558B2F; }
    .quality-fair { background: #FFF9C4; color: #F57F17; }
    .quality-poor { background: #FFCDD2; color: #C62828; }
    
    /* Clickable breadcrumb */
    .breadcrumb-clickable {
        cursor: pointer;
        transition: all 0.2s;
    }
    .breadcrumb-clickable:hover {
        transform: scale(1.1);
    }
    
    /* FAQ accordion */
    .faq-item {
        background: white;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Scenario card */
    .scenario-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%);
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        transition: all 0.3s;
    }
    .scenario-card:hover {
        border-color: var(--primary-gold);
        box-shadow: 0 4px 15px rgba(198,163,79,0.2);
    }
    .scenario-card.active {
        border-color: var(--primary-navy);
        background: linear-gradient(135deg, #E3F2FD 0%, #fff 100%);
    }
    
    /* Progress Bar */
    .progress-bar-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 20px 0 30px 0;
        padding: 0 40px;
    }
    
    .progress-step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        flex: 1;
    }
    
    .progress-step-item:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 22px;
        left: 50%;
        width: 100%;
        height: 4px;
        background: #e0e0e0;
        z-index: 0;
    }
    
    .progress-step-item.completed:not(:last-child)::after {
        background: var(--primary-success);
    }
    
    .progress-step-item.active:not(:last-child)::after {
        background: linear-gradient(90deg, var(--primary-navy) 50%, #e0e0e0 50%);
    }
    
    .progress-circle {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1rem;
        z-index: 1;
        transition: all 0.3s;
    }
    
    .progress-circle.completed {
        background: var(--primary-success);
        color: white;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }
    
    .progress-circle.active {
        background: var(--primary-navy);
        color: white;
        box-shadow: 0 4px 12px rgba(0, 47, 108, 0.4);
        transform: scale(1.1);
    }
    
    .progress-circle.pending {
        background: #e0e0e0;
        color: #999;
    }
    
    .progress-label {
        margin-top: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .progress-label.completed { color: var(--primary-success); }
    .progress-label.active { color: var(--primary-navy); }
    .progress-label.pending { color: #999; }
    
    /* Apply Recommendation Button */
    .apply-btn {
        background: linear-gradient(135deg, var(--primary-success) 0%, #1B5E20 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        padding: 16px 32px !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.4) !important;
        transition: all 0.3s !important;
    }
    
    .apply-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(46, 125, 50, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DARK MODE CSS (applied conditionally)
# ============================================
if 'dark_mode' in st.session_state and st.session_state.dark_mode:
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
        }
        
        .section-card {
            background: #1f1f3d !important;
            border-color: rgba(198,163,79,0.3) !important;
        }
        
        .metric-card {
            background: #1f1f3d !important;
            border-color: #444 !important;
        }
        
        .main-title, .section-title, h1, h2, h3 {
            color: #ffffff !important;
        }
        
        .main-title span {
            color: var(--primary-gold) !important;
        }
        
        .metric-value {
            color: var(--primary-gold) !important;
        }
        
        .metric-label {
            color: #aaa !important;
        }
        
        .subtitle {
            color: #aaa !important;
        }
        
        p, span, label, .stMarkdown {
            color: #e0e0e0 !important;
        }
        
        .info-box, .success-box, .warning-box, .gold-box {
            background: rgba(255,255,255,0.1) !important;
        }
        
        .stSelectbox > div > div,
        .stMultiSelect > div > div,
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: #2a2a4a !important;
            color: #fff !important;
            border-color: #444 !important;
        }
        
        .stDataFrame {
            background: #1f1f3d !important;
        }
        
        .progress-circle.pending {
            background: #3a3a5a !important;
            color: #888 !important;
        }
        
        .progress-step-item:not(:last-child)::after {
            background: #3a3a5a !important;
        }
        
        /* Expander dark mode */
        .streamlit-expanderHeader {
            background: #2a2a4a !important;
            color: #fff !important;
        }
        
        .streamlit-expanderContent {
            background: #1f1f3d !important;
            color: #e0e0e0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'pretest_data' not in st.session_state:
    st.session_state.pretest_data = None
if 'power_results' not in st.session_state:
    st.session_state.power_results = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'treatment_cities' not in st.session_state:
    st.session_state.treatment_cities = []
if 'control_cities' not in st.session_state:
    st.session_state.control_cities = []
if 'config' not in st.session_state:
    st.session_state.config = {
        'confidence_level': 0.95,
        'target_power': 0.80,
        'expected_lift': 0.15,
        'test_duration': 28
    }
# New session states for improvements
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = []
if 'data_validation' not in st.session_state:
    st.session_state.data_validation = None
if 'show_faq' not in st.session_state:
    st.session_state.show_faq = False

# ============================================
# CACHING FOR PERFORMANCE
# ============================================
@st.cache_data(ttl=3600)
def cached_power_analysis(df_hash, treatment, control, lift, duration, confidence):
    """Cache power analysis results for performance."""
    # Recreate dataframe from session state (can't hash DataFrame directly)
    df = st.session_state.pretest_data
    if df is None:
        return None
    pa = PowerAnalysis(df)
    return pa.calculate_test_power(list(treatment), list(control), lift, duration, confidence)

@st.cache_data(ttl=3600)
def cached_optimal_duration(df_hash, treatment, control, lift, target_power, confidence):
    """Cache optimal duration calculation."""
    df = st.session_state.pretest_data
    if df is None:
        return None
    pa = PowerAnalysis(df)
    return pa.find_optimal_duration(list(treatment), list(control), lift, target_power, confidence)

# ============================================
# HEADER WITH CONTROLS
# ============================================
header_col1, header_col2, header_col3, header_col4 = st.columns([1, 7, 2, 2])

with header_col1:
    if st.button("← Home"):
        st.switch_page("app.py")

with header_col3:
    # Dark mode toggle
    dark_mode = st.toggle("🌙 Dark", value=st.session_state.dark_mode, help="Modo oscuro")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()

with header_col4:
    if st.button("❓ FAQ", use_container_width=True):
        st.session_state.show_faq = not st.session_state.show_faq
        st.rerun()

# Title
st.markdown('<h1 class="main-title">📊 Pre-Test <span>Calculator</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Planificá tu experimento GeoLift en 4 pasos</p>', unsafe_allow_html=True)

# ============================================
# VISUAL PROGRESS BAR
# ============================================
steps = [
    ("1", "Datos", 1),
    ("2", "Ciudades", 2),
    ("3", "Análisis", 3),
    ("4", "Export", 4)
]

progress_html = '<div class="progress-bar-container">'
for num, label, step_num in steps:
    if step_num < st.session_state.current_step:
        status = "completed"
        icon = "✓"
    elif step_num == st.session_state.current_step:
        status = "active"
        icon = num
    else:
        status = "pending"
        icon = num
    
    progress_html += f'''
    <div class="progress-step-item {status}">
        <div class="progress-circle {status}">{icon}</div>
        <span class="progress-label {status}">{label}</span>
    </div>
    '''

progress_html += '</div>'
st.markdown(progress_html, unsafe_allow_html=True)

# ============================================
# FAQ MODAL
# ============================================
if st.session_state.show_faq:
    st.markdown("---")
    st.markdown("### ❓ Preguntas Frecuentes (FAQ)")
    
    faq_items = get_faq_content()
    for item in faq_items:
        with st.expander(f"**{item['question']}**"):
            st.markdown(item['answer'])
    
    if st.button("Cerrar FAQ", type="primary"):
        st.session_state.show_faq = False
        st.rerun()
    
    st.markdown("---")

# ============================================
# CLICKABLE PROGRESS INDICATOR (BREADCRUMBS)
# ============================================
steps = [
    ("1", "Cargar Datos"),
    ("2", "Seleccionar Ciudades"),
    ("3", "Analizar Poder"),
    ("4", "Exportar Plan")
]

# Check which steps are accessible (completed)
def can_go_to_step(step_num):
    if step_num == 1:
        return True
    if step_num == 2:
        return st.session_state.pretest_data is not None
    if step_num == 3:
        return (st.session_state.pretest_data is not None and 
                st.session_state.treatment_cities and 
                st.session_state.control_cities)
    if step_num == 4:
        return st.session_state.power_results is not None
    return False

cols = st.columns(len(steps))
for i, (num, name) in enumerate(steps):
    step_num = i + 1
    if st.session_state.current_step > step_num:
        status = "done"
        icon = "✓"
    elif st.session_state.current_step == step_num:
        status = "active"
        icon = num
    else:
        status = "pending"
        icon = num
    
    with cols[i]:
        # Make completed and current steps clickable
        can_click = can_go_to_step(step_num) and step_num <= st.session_state.current_step
        
        if can_click and step_num != st.session_state.current_step:
            if st.button(f"{icon}", key=f"step_btn_{step_num}", help=f"Ir a {name}"):
                st.session_state.current_step = step_num
                st.rerun()
            st.markdown(f'<div class="step-label step-label-{status}" style="cursor:pointer;">{name}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="progress-step">
                <div class="step-circle step-{status}">{icon}</div>
                <div class="step-label step-label-{status}">{name}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# STEP 1: LOAD DATA
# ============================================
if st.session_state.current_step == 1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📁 Paso 1: Cargá tus datos históricos</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="gold-box">
            <strong>🚀 ¿Primera vez?</strong> Probá la herramienta con datos de ejemplo para familiarizarte.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ Cargar Datos Demo", type="primary", use_container_width=True):
            cities_data = [
                ('Argentina', 'Buenos_Aires', 150, 3000000, 5000),
                ('Argentina', 'Córdoba', 80, 1500000, 2500),
                ('Argentina', 'Rosario', 60, 1200000, 2000),
                ('Argentina', 'Mendoza', 45, 900000, 1500),
            ]
            
            demo_rows = []
            start_date = datetime.date(2024, 1, 1)
            
            for country, city, base, pop, spend in cities_data:
                for day in range(30):
                    date = start_date + datetime.timedelta(days=day)
                    customers = int(base * (1 + np.random.uniform(-0.1, 0.1)))
                    demo_rows.append({
                        'country': country,
                        'city': city,
                        'date': date.strftime('%Y-%m-%d'),
                        'new_customers': customers,
                        'gmv': customers * 500,
                        'orders': int(customers * 2.1),
                        'media_spend': int(spend * (1 + np.random.uniform(-0.05, 0.05))),
                        'population': pop
                    })
            
            st.session_state.pretest_data = pd.DataFrame(demo_rows)
            st.session_state.current_step = 2
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### O subí tu archivo CSV o Excel")
        
        uploaded_file = st.file_uploader(
            "Arrastrá tu archivo aquí",
            type=['csv', 'xlsx', 'xls'],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            try:
                with st.spinner("🔄 Procesando archivo..."):
                    time.sleep(0.5)  # Small delay for UX
                    
                    # Detect file type and read accordingly
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    # Comprehensive validation
                    required = ['city', 'date', 'new_customers']
                    validation = validate_data(df, required)
                    st.session_state.data_validation = validation
                    
                    if not validation['is_valid']:
                        for error in validation['errors']:
                            st.error(f"❌ {error}")
                    else:
                        # Auto-detect and parse dates
                        try:
                            df, date_format = parse_dates_flexible(df, 'date')
                            st.info(f"📅 Formato de fecha detectado: `{date_format}`")
                        except Exception as date_err:
                            st.warning(f"⚠️ No se pudo parsear fechas automáticamente: {date_err}")
                        
                        st.session_state.pretest_data = df
                        
                        # Calculate data quality score
                        quality_score = calculate_data_quality_score(validation)
                        
                        # Show quality badge
                        if quality_score >= 90:
                            badge_class, badge_text = "quality-excellent", "Excelente"
                        elif quality_score >= 70:
                            badge_class, badge_text = "quality-good", "Buena"
                        elif quality_score >= 50:
                            badge_class, badge_text = "quality-fair", "Regular"
                        else:
                            badge_class, badge_text = "quality-poor", "Baja"
                        
                        # Show summary
                        n_cities = df['city'].nunique()
                        n_days = df.groupby('city').size().iloc[0] if len(df) > 0 else 0
                        
                        sum_col1, sum_col2 = st.columns([3, 1])
                        with sum_col1:
                            st.success(f"✅ **{len(df):,}** registros cargados de **{n_cities}** ciudades ({n_days} días)")
                        with sum_col2:
                            st.markdown(f'<span class="quality-badge {badge_class}">Calidad: {badge_text} ({quality_score}%)</span>', unsafe_allow_html=True)
                        
                        # Show warnings if any
                        if validation['warnings']:
                            with st.expander(f"⚠️ {len(validation['warnings'])} advertencias detectadas", expanded=True):
                                for warning in validation['warnings']:
                                    st.warning(warning)
                                
                                # Show outlier details if present
                                if validation.get('stats', {}).get('outliers', 0) > 0:
                                    st.markdown("**Detalle de outliers:**")
                                    outliers_df = get_outlier_details(df)
                                    if len(outliers_df) > 0:
                                        st.dataframe(
                                            outliers_df[['city', 'date', 'new_customers', 'outlier_type']].head(10),
                                            use_container_width=True
                                        )
                        
                        # Preview
                        with st.expander("👀 Ver preview de datos"):
                            st.dataframe(df.head(10), use_container_width=True)
                        
                        if st.button("Continuar →", type="primary"):
                            st.session_state.current_step = 2
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ Error al procesar: {e}")
                st.info("💡 Tip: Asegurate que el archivo tenga las columnas requeridas y esté en formato CSV o Excel válido.")
    
    with col2:
        st.markdown("#### 📋 Formato del archivo")
        
        with st.expander("ℹ️ ¿Qué columnas necesito?", expanded=True):
            st.markdown("""
            **Columnas requeridas:**
            - `city` → Nombre de la ciudad/región
            - `date` → Fecha (formato YYYY-MM-DD)
            - `new_customers` → Clientes nuevos ese día
            
            **Columnas opcionales (mejoran el análisis):**
            - `media_spend` → Inversión en medios ($)
            - `population` → Población de la ciudad
            - `country` → País
            - `gmv` → Valor bruto de ventas
            - `orders` → Cantidad de pedidos
            """)
        
        with st.expander("💡 ¿Cuántos datos necesito?"):
            st.markdown("""
            **Mínimo recomendado:**
            - **3+ ciudades** para poder comparar
            - **30+ días** de datos históricos
            - Datos **diarios** (no semanales)
            
            Más datos = análisis más confiable.
            """)
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'pretest_template.csv')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                st.download_button(
                    "⬇️ Descargar Template CSV",
                    f.read(),
                    "template_geolift.csv",
                    "text/csv",
                    use_container_width=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# STEP 2: SELECT CITIES
# ============================================
elif st.session_state.current_step == 2:
    df = st.session_state.pretest_data
    cities = sorted(df['city'].unique().tolist())
    
    # Data summary metrics
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Resumen de datos</div>', unsafe_allow_html=True)
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(cities)}</div>
            <div class="metric-label">Ciudades</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        days = df.groupby('city').size().iloc[0]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{days}</div>
            <div class="metric-label">Días de datos</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        total = df['new_customers'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total:,.0f}</div>
            <div class="metric-label">Total clientes</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        avg = df['new_customers'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg:.0f}</div>
            <div class="metric-label">Promedio/día</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # City selection
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏙️ Paso 2: Seleccioná las ciudades</div>', unsafe_allow_html=True)
    
    # Concept help
    with st.expander("ℹ️ ¿Qué es Tratamiento y Control?", expanded=False):
        st.markdown("""
        **🎯 Tratamiento (Test):** Ciudades donde **SÍ** ejecutarás la campaña de marketing.
        Acá es donde querés medir el impacto.
        
        **🔬 Control (Holdout):** Ciudades donde **NO** ejecutarás la campaña.
        Sirven como referencia para comparar y aislar el efecto real de tu campaña.
        
        ---
        
        **💡 Tips para elegir bien:**
        - Elegí ciudades de control **similares** a las de tratamiento (tamaño, comportamiento)
        - Evitá ciudades con eventos especiales durante el test
        - Más ciudades de control = análisis más robusto
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🤖 Recomendación automática")
        st.caption("El sistema analiza tus datos y sugiere la mejor configuración")
        
        rec_col1, rec_col2 = st.columns(2)
        n_treatment = rec_col1.number_input("# Tratamiento", 1, len(cities)-1, 1, key="n_treat")
        n_control = rec_col2.number_input("# Control", 1, len(cities)-1, min(2, len(cities)-1), key="n_ctrl")
        
        if st.button("🎲 Generar Recomendación", use_container_width=True):
            with st.spinner("Analizando la mejor combinación..."):
                pa = PowerAnalysis(df)
                rec = pa.recommend_cities(n_treatment, n_control)
                
                if 'error' not in rec:
                    st.session_state.pending_recommendation = rec
                    st.rerun()
        
        # Show pending recommendation with APPLY button
        if 'pending_recommendation' in st.session_state and st.session_state.pending_recommendation:
            rec = st.session_state.pending_recommendation
            
            st.markdown("""
            <div class="gold-box">
                <strong>🎯 Recomendación generada:</strong><br>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**Tratamiento:** {', '.join(rec['treatment'])}")
            st.markdown(f"**Control:** {', '.join(rec['control'])}")
            
            if 'rationale' in rec:
                with st.expander("📖 ¿Por qué esta selección?"):
                    st.markdown(rec['rationale'])
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            apply_col1, apply_col2 = st.columns(2)
            
            with apply_col1:
                if st.button("✅ APLICAR RECOMENDACIÓN", type="primary", use_container_width=True, key="apply_rec"):
                    st.session_state.treatment_cities = rec['treatment']
                    st.session_state.control_cities = rec['control']
                    st.session_state.pending_recommendation = None
                    st.rerun()
            
            with apply_col2:
                if st.button("❌ Descartar", use_container_width=True, key="discard_rec"):
                    st.session_state.pending_recommendation = None
                    st.rerun()
    
    with col2:
        st.markdown("##### ✏️ Selección manual")
        
        st.session_state.treatment_cities = st.multiselect(
            "🎯 Ciudades TRATAMIENTO (campaña activa)",
            cities,
            default=st.session_state.treatment_cities,
            help="Donde ejecutarás la campaña de marketing"
        )
        
        available = [c for c in cities if c not in st.session_state.treatment_cities]
        st.session_state.control_cities = st.multiselect(
            "🔬 Ciudades CONTROL (sin campaña)",
            available,
            default=[c for c in st.session_state.control_cities if c in available],
            help="Ciudades que no recibirán la campaña"
        )
    
    # Show current selection
    if st.session_state.treatment_cities and st.session_state.control_cities:
        st.markdown("---")
        
        st.markdown("""
        <div class="success-box">
            <strong>✅ Selección completa</strong> — Podés continuar al análisis de poder
        </div>
        """, unsafe_allow_html=True)
        
        sel_col1, sel_col2 = st.columns(2)
        
        with sel_col1:
            st.markdown("**🎯 Tratamiento:**")
            chips_html = ""
            for city in st.session_state.treatment_cities:
                avg = df[df['city'] == city]['new_customers'].mean()
                chips_html += f'<span class="city-chip">{city} ({avg:.0f}/día)</span>'
            st.markdown(chips_html, unsafe_allow_html=True)
        
        with sel_col2:
            st.markdown("**🔬 Control:**")
            chips_html = ""
            for city in st.session_state.control_cities:
                avg = df[df['city'] == city]['new_customers'].mean()
                chips_html += f'<span class="city-chip city-chip-control">{city} ({avg:.0f}/día)</span>'
            st.markdown(chips_html, unsafe_allow_html=True)
        
        # Prominent CONTINUE button
        st.markdown("<br>", unsafe_allow_html=True)
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            if st.button("🚀 CONTINUAR AL ANÁLISIS DE PODER →", type="primary", use_container_width=True, key="go_to_analysis"):
                st.session_state.current_step = 3
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # SCENARIO COMPARISON
    # =========================================
    if st.session_state.saved_scenarios:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Escenarios Guardados</div>', unsafe_allow_html=True)
        
        comparison_df = create_scenario_comparison(st.session_state.saved_scenarios)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Limpiar todos los escenarios"):
            st.session_state.saved_scenarios = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.button("← Volver", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with nav_col3:
        can_continue = st.session_state.treatment_cities and st.session_state.control_cities
        if st.button("Continuar →", type="primary", use_container_width=True, disabled=not can_continue):
            st.session_state.current_step = 3
            st.rerun()

# ============================================
# STEP 3: POWER ANALYSIS
# ============================================
elif st.session_state.current_step == 3:
    df = st.session_state.pretest_data
    treatment = st.session_state.treatment_cities
    control = st.session_state.control_cities
    
    pa = PowerAnalysis(df)
    
    # Concept explanations
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📚 Conceptos clave</div>', unsafe_allow_html=True)
    
    concept_col1, concept_col2, concept_col3 = st.columns(3)
    
    with concept_col1:
        with st.expander("🎯 ¿Qué es el Poder Estadístico?"):
            st.markdown("""
            Es la **probabilidad de detectar un efecto real** cuando existe.
            
            - **80%+ = Bueno** ✅
            - **60-80% = Aceptable** ⚠️
            - **<60% = Bajo** ❌
            
            *Si tu poder es 80%, hay 80% de chances de detectar el lift si realmente existe.*
            """)
    
    with concept_col2:
        with st.expander("📏 ¿Qué es el MDE?"):
            st.markdown("""
            **Minimum Detectable Effect** (Efecto Mínimo Detectable)
            
            Es el **lift mínimo** que tu test puede detectar con confianza.
            
            - Si esperás 15% de lift, tu MDE debe ser **menor a 15%**
            - MDE alto = necesitás más días o más datos
            
            *Ejemplo: MDE de 10% significa que solo detectarás lifts ≥10%*
            """)
    
    with concept_col3:
        with st.expander("📈 ¿Qué es el Lift?"):
            st.markdown("""
            Es el **incremento porcentual** que esperas obtener con tu campaña.
            
            - Lift 15% = esperas 15% más clientes que sin campaña
            
            **¿Cómo estimarlo?**
            - Basate en campañas anteriores
            - Sé conservador (mejor subestimar)
            - 10-20% es típico para campañas de performance
            """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Configuration
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚙️ Configuración del test</div>', unsafe_allow_html=True)
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        test_duration = st.slider(
            "⏱️ Duración del test (días)",
            7, 90, st.session_state.config['test_duration'], 7,
            help="Más días = más datos = mayor poder estadístico. Mínimo recomendado: 14 días."
        )
        st.session_state.config['test_duration'] = test_duration
        if test_duration < 14:
            st.caption("⚠️ Tests <14 días tienen mayor variabilidad")
    
    with config_col2:
        expected_lift = st.slider(
            "📈 Lift esperado (%)",
            5, 50, int(st.session_state.config['expected_lift'] * 100), 5,
            help="Incremento que esperas obtener. Sé conservador: es mejor subestimar que sobreestimar."
        ) / 100
        st.session_state.config['expected_lift'] = expected_lift
        if expected_lift > 0.25:
            st.caption("💡 Lifts >25% son poco comunes")
    
    with config_col3:
        confidence = st.selectbox(
            "🎯 Nivel de confianza",
            [0.90, 0.95],
            index=1,
            format_func=lambda x: f"{int(x*100)}%",
            help="95% es el estándar de la industria. 90% es más permisivo."
        )
        st.session_state.config['confidence_level'] = confidence
        st.caption("📊 95% = estándar de industria")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculate power with loading spinner
    with st.spinner("🔄 Calculando poder estadístico..."):
        result = pa.calculate_test_power(
            treatment, control, expected_lift, test_duration, confidence
        )
    st.session_state.power_results = result
    
    # Results
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Resultados del análisis</div>', unsafe_allow_html=True)
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    power_class = "metric-good" if result['power_percent'] >= 80 else "metric-warning" if result['power_percent'] >= 60 else "metric-bad"
    mde_ok = result['mde_percent'] < expected_lift * 100
    mde_class = "metric-good" if mde_ok else "metric-warning"
    
    with m_col1:
        st.markdown(f"""
        <div class="metric-card {power_class}">
            <div class="metric-value">{result['power_percent']:.0f}%</div>
            <div class="metric-label">Poder Estadístico</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("💡 Objetivo: ≥80%")
    
    with m_col2:
        st.markdown(f"""
        <div class="metric-card {mde_class}">
            <div class="metric-value">{result['mde_percent']:.1f}%</div>
            <div class="metric-label">MDE (Lift mínimo)</div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("💡 Debe ser < lift esperado")
    
    with m_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result['treatment_mean']:.0f}</div>
            <div class="metric-label">Clientes/día (Trat.)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with m_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{result['control_mean']:.0f}</div>
            <div class="metric-label">Clientes/día (Ctrl.)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Interpretation
    st.markdown("<br>", unsafe_allow_html=True)
    
    if result['is_powered'] and mde_ok:
        st.markdown(f"""
        <div class="success-box">
            <strong>✅ ¡Diseño viable!</strong><br>
            Con {test_duration} días y {int(expected_lift*100)}% de lift esperado, tenés 
            <strong>{result['power_percent']:.0f}%</strong> de probabilidad de detectar el efecto.
        </div>
        """, unsafe_allow_html=True)
    else:
        issues = []
        if not result['is_powered']:
            issues.append("El poder es menor al 80% recomendado")
        if not mde_ok:
            issues.append(f"El MDE ({result['mde_percent']:.1f}%) supera el lift esperado ({int(expected_lift*100)}%)")
        
        st.markdown(f"""
        <div class="warning-box">
            <strong>⚠️ Ajustes recomendados:</strong><br>
            {'<br>'.join(['• ' + i for i in issues])}<br><br>
            <em>Sugerencia: aumentá la duración o el lift esperado</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Save scenario button
    st.markdown("<br>", unsafe_allow_html=True)
    save_col1, save_col2 = st.columns([3, 1])
    with save_col2:
        scenario_name = st.text_input("Nombre del escenario", value=f"Escenario {len(st.session_state.saved_scenarios)+1}", label_visibility="collapsed", placeholder="Nombre del escenario")
    with save_col1:
        if st.button("💾 Guardar este escenario para comparar", use_container_width=True):
            new_scenario = {
                'name': scenario_name,
                'treatment': treatment,
                'control': control,
                'duration': test_duration,
                'expected_lift': expected_lift,
                'power': result['power_percent'],
                'mde': result['mde_percent']
            }
            st.session_state.saved_scenarios.append(new_scenario)
            st.success(f"✅ Escenario '{scenario_name}' guardado! Tenés {len(st.session_state.saved_scenarios)} escenarios para comparar.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Power curve chart
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📉 Poder vs Duración del Test</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Cómo leer este gráfico?"):
        st.markdown("""
        Este gráfico muestra cómo cambia el **poder estadístico** según la duración del test:
        
        - **Línea azul:** Tu poder estadístico para cada duración
        - **Línea verde punteada (80%):** El objetivo mínimo recomendado
        - **Línea dorada:** La duración que configuraste
        
        **Interpretación:**
        - Si la línea azul está **por encima** de la verde = ✅ Viable
        - Si está **por debajo** = ⚠️ Necesitás más días
        
        *Tip: Buscá el punto donde la curva cruza el 80%*
        """)
    
    optimal = pa.find_optimal_duration(treatment, control, expected_lift, 0.80, confidence)
    power_df = pd.DataFrame(optimal['power_curve'])
    
    fig = go.Figure()
    
    # Add power curve
    fig.add_trace(go.Scatter(
        x=power_df['days'],
        y=power_df['power'] * 100,
        mode='lines+markers',
        name='Poder Estadístico',
        line=dict(color='#002F6C', width=3),
        marker=dict(size=8, color='#002F6C'),
        hovertemplate='%{x} días: %{y:.1f}%<extra></extra>'
    ))
    
    # Reference lines
    fig.add_hline(y=80, line_dash="dash", line_color="#2E7D32", 
                  annotation_text="80% objetivo", annotation_position="right")
    fig.add_vline(x=test_duration, line_dash="dash", line_color="#C6A34F",
                  annotation_text=f"Tu test: {test_duration}d", annotation_position="top")
    
    fig.update_layout(
        xaxis_title="Duración (días)",
        yaxis_title="Poder Estadístico (%)",
        height=380,
        margin=dict(l=50, r=50, t=30, b=50),
        yaxis=dict(range=[0, 100], gridcolor='#f0f0f0'),
        xaxis=dict(gridcolor='#f0f0f0'),
        plot_bgcolor='white',
        font=dict(family='Montserrat')
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    if optimal['achievable']:
        st.markdown(f"""
        <div class="gold-box">
            💡 <strong>Recomendación:</strong> Con {optimal['optimal_days']} días alcanzás 80% de poder estadístico.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: Market Matching Score
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎯 Market Matching Score</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Qué es el Market Matching Score?"):
        st.markdown("""
        Mide qué tan **similares** son las ciudades de control respecto al tratamiento.
        
        Un buen match (≥60%) significa que las ciudades tienen:
        - **Comportamiento histórico similar** (correlación)
        - **Volumen comparable** (tamaño)
        - **Tendencias paralelas** (crecimiento/decrecimiento)
        
        Esto es crítico para que el test sea válido.
        """)
    
    match_result = pa.calculate_market_matching_score(treatment, control)
    
    match_col1, match_col2, match_col3 = st.columns(3)
    
    with match_col1:
        score = match_result['overall_score']
        score_class = "metric-good" if score >= 60 else "metric-warning" if score >= 40 else "metric-bad"
        st.markdown(f"""
        <div class="metric-card {score_class}">
            <div class="metric-value">{match_result['rating_emoji']} {score:.0f}%</div>
            <div class="metric-label">Score General</div>
        </div>
        """, unsafe_allow_html=True)
    
    with match_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{match_result['correlation']:.0f}%</div>
            <div class="metric-label">Correlación</div>
        </div>
        """, unsafe_allow_html=True)
    
    with match_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{match_result['volume_ratio']:.0f}%</div>
            <div class="metric-label">Similitud Volumen</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"<br>{match_result['interpretation']}", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: Pre-test Balance Check
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚖️ Balance Pre-Test (Tendencias Paralelas)</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Qué son las Tendencias Paralelas?"):
        st.markdown("""
        Es el **supuesto clave** de Diferencias en Diferencias (DiD).
        
        Significa que tratamiento y control deben tener **tendencias similares** 
        ANTES del test. Si no se cumple, los resultados pueden ser inválidos.
        
        - **Tendencias paralelas** ✅ = DiD es válido
        - **Tendencias divergentes** ⚠️ = Considerar Synthetic Control
        """)
    
    balance = pa.check_pretest_balance(treatment, control)
    
    bal_col1, bal_col2 = st.columns(2)
    
    with bal_col1:
        status = "✅ Balanceado" if balance['is_balanced'] else "⚠️ Revisar"
        status_class = "metric-good" if balance['is_balanced'] else "metric-warning"
        st.markdown(f"""
        <div class="metric-card {status_class}">
            <div class="metric-value">{status}</div>
            <div class="metric-label">Status Pre-Test</div>
        </div>
        """, unsafe_allow_html=True)
    
    with bal_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{balance['changes_correlation']*100:.0f}%</div>
            <div class="metric-label">Correlación Cambios Diarios</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"<br>{balance['interpretation']}", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: ROI Projection
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💰 Proyección de ROI</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Qué es el iROAS?"):
        st.markdown("""
        **iROAS** = Incremental Return on Ad Spend (Retorno Incremental sobre Inversión)
        
        Mide cuántos $ de revenue incremental generás por cada $1 invertido en medios.
        
        - **iROAS > 1** = Rentable ✅
        - **iROAS < 1** = No rentable ❌
        
        *Esta es una proyección basada en el lift esperado.*
        """)
    
    roi_col1, roi_col2 = st.columns(2)
    
    with roi_col1:
        customer_value = st.number_input(
            "💵 Valor promedio por cliente ($)",
            min_value=100, max_value=10000, value=500, step=50,
            help="Customer Lifetime Value o valor promedio del primer pedido"
        )
    
    roi_result = pa.calculate_roi_projection(treatment, expected_lift, test_duration, customer_value)
    
    roi_m1, roi_m2, roi_m3 = st.columns(3)
    
    with roi_m1:
        roi_class = "metric-good" if roi_result['roi_percent'] > 0 else "metric-bad"
        st.markdown(f"""
        <div class="metric-card {roi_class}">
            <div class="metric-value">{roi_result['roi_percent']:.0f}%</div>
            <div class="metric-label">ROI Proyectado</div>
        </div>
        """, unsafe_allow_html=True)
    
    with roi_m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{roi_result['iroas']:.2f}x</div>
            <div class="metric-label">iROAS</div>
        </div>
        """, unsafe_allow_html=True)
    
    with roi_m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{roi_result['total_incremental_customers']:.0f}</div>
            <div class="metric-label">Clientes Incrementales Est.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"<br>{roi_result['interpretation']}", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: Power Evolution by Week
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📅 Evolución del Poder por Semana</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Para qué sirve esto?"):
        st.markdown("""
        Te muestra **semana a semana** cómo evoluciona el poder estadístico.
        
        Útil para:
        - Planificar cuándo revisar el test
        - Decidir si extender o cortar antes
        - Comunicar timeline a stakeholders
        """)
    
    power_weeks = pa.calculate_power_over_time(treatment, control, expected_lift, confidence)
    power_weeks_df = pd.DataFrame(power_weeks)
    
    # Display as table
    st.dataframe(
        power_weeks_df[['week', 'days', 'power', 'mde', 'recommendation']].rename(columns={
            'week': 'Semana',
            'days': 'Días',
            'power': 'Poder (%)',
            'mde': 'MDE (%)',
            'recommendation': 'Recomendación'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: Bootstrap Confidence Intervals
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Intervalos de Confianza Bootstrap</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Qué es Bootstrap CI?"):
        st.markdown("""
        El método **Bootstrap** es una técnica estadística robusta que:
        
        - Simula miles de escenarios posibles
        - Proporciona intervalos de confianza más realistas
        - No asume distribución normal de los datos
        
        Es el estándar de oro en geo-experimentación (usado por GeoLift de Meta).
        """)
    
    with st.spinner("Calculando Bootstrap CI (1000 iteraciones)..."):
        bootstrap_result = pa.calculate_bootstrap_ci(treatment, control, n_bootstrap=1000, confidence_level=confidence)
    
    boot_col1, boot_col2, boot_col3 = st.columns(3)
    
    with boot_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{bootstrap_result['point_estimate']:.1f}%</div>
            <div class="metric-label">Lift Estimado (Baseline)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with boot_col2:
        ci_text = f"[{bootstrap_result['ci_lower']:.1f}%, {bootstrap_result['ci_upper']:.1f}%]"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.3rem;">{ci_text}</div>
            <div class="metric-label">IC {int(confidence*100)}% Bootstrap</div>
        </div>
        """, unsafe_allow_html=True)
    
    with boot_col3:
        se_text = f"±{bootstrap_result['standard_error']:.1f}%"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{se_text}</div>
            <div class="metric-label">Error Estándar</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"<br>{bootstrap_result['interpretation']}", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: Auto Location Selection
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 Selección Automática de Ciudades</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Qué hace esto?"):
        st.markdown("""
        Busca automáticamente la **combinación óptima** de ciudades que:
        
        - Alcanza el poder estadístico objetivo (80%)
        - Usa el mínimo número de ciudades necesarias
        - Maximiza la calidad del match
        
        Equivalente a `GeoLiftMarketSelection()` de Meta.
        """)
    
    if st.button("🔍 Buscar configuración óptima", use_container_width=True):
        with st.spinner("Analizando todas las combinaciones posibles..."):
            auto_result = pa.auto_select_locations(
                expected_lift=expected_lift,
                test_duration=test_duration,
                target_power=0.80,
                confidence_level=confidence
            )
        
        if 'error' not in auto_result:
            st.markdown(f"<div class='gold-box'>{auto_result['recommendation']}</div>", unsafe_allow_html=True)
            
            # Show optimal
            opt = auto_result['optimal']
            st.markdown(f"""
            **Configuración Óptima:**
            - **Tratamiento:** {', '.join(opt['treatment_cities'])} ({opt['n_treatment']} ciudades)
            - **Control:** {', '.join(opt['control_cities'])} ({opt['n_control']} ciudades)
            - **Poder:** {opt['power']:.0f}% | **MDE:** {opt['mde']:.1f}%
            """)
            
            # Show alternatives
            if auto_result['alternatives']:
                with st.expander("Ver alternativas"):
                    for i, alt in enumerate(auto_result['alternatives'], 1):
                        st.markdown(f"""
                        **Alternativa {i}:** {alt['n_treatment']}T + {alt['n_control']}C = {alt['power']:.0f}% poder
                        """)
        else:
            st.warning(auto_result['error'])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: Budget Allocator
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💰 Asignación de Presupuesto</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Cómo funciona?"):
        st.markdown("""
        Sugiere cómo **distribuir tu presupuesto** de medios entre las ciudades de tratamiento:
        
        - **Igualitario:** Mismo presupuesto para todas
        - **Proporcional:** Más presupuesto a ciudades más grandes
        - **Optimizado:** Más presupuesto a ciudades más eficientes (mejor ROI histórico)
        """)
    
    budget_col1, budget_col2 = st.columns(2)
    
    with budget_col1:
        total_budget = st.number_input(
            "💵 Presupuesto total ($)",
            min_value=1000, max_value=10000000, value=50000, step=5000,
            help="Presupuesto total de medios para el período del test"
        )
    
    with budget_col2:
        allocation_method = st.selectbox(
            "📊 Método de asignación",
            ['proportional', 'equal', 'optimized'],
            format_func=lambda x: {'proportional': '📊 Proporcional (por volumen)', 
                                   'equal': '💰 Igualitario', 
                                   'optimized': '🎯 Optimizado (por eficiencia)'}[x]
        )
    
    if st.button("📋 Calcular distribución", use_container_width=True):
        budget_result = pa.allocate_budget(treatment, total_budget, allocation_method, expected_lift)
        
        if 'error' not in budget_result:
            st.markdown(f"<div class='info-box'>{budget_result['method_description']}</div>", unsafe_allow_html=True)
            
            # Show allocation table
            st.dataframe(budget_result['summary_table'], use_container_width=True, hide_index=True)
            
            st.markdown(f"""
            **Proyección:** ~{budget_result['expected_incremental_customers_daily']:.0f} clientes incrementales/día 
            | Costo por cliente: ${budget_result['expected_cost_per_incremental']:.0f}
            """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================================
    # NEW: What-If Simulator
    # =========================================
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔮 Simulador What-If</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ ¿Qué es esto?"):
        st.markdown("""
        Simula **múltiples escenarios** para comparar rápidamente:
        
        - ¿Qué pasa si el lift es menor al esperado?
        - ¿Qué pasa si extiendo el test?
        - ¿Cuál es el escenario pesimista vs optimista?
        """)
    
    sim_col1, sim_col2, sim_col3 = st.columns(3)
    
    with sim_col1:
        sim_lift_low = st.number_input("Lift pesimista (%)", 5, 50, 10, key="sim_low") / 100
    with sim_col2:
        sim_lift_mid = st.number_input("Lift esperado (%)", 5, 50, int(expected_lift*100), key="sim_mid") / 100
    with sim_col3:
        sim_lift_high = st.number_input("Lift optimista (%)", 5, 50, 25, key="sim_high") / 100
    
    if st.button("🚀 Simular escenarios", use_container_width=True):
        scenarios = [
            {'name': '📉 Pesimista', 'lift': sim_lift_low, 'duration': test_duration},
            {'name': '📊 Esperado', 'lift': sim_lift_mid, 'duration': test_duration},
            {'name': '📈 Optimista', 'lift': sim_lift_high, 'duration': test_duration},
            {'name': '⏱️ Test extendido (+2 sem)', 'lift': sim_lift_mid, 'duration': test_duration + 14},
        ]
        
        with st.spinner("Simulando escenarios..."):
            sim_results = pa.simulate_what_if(treatment, control, scenarios)
        
        # Display results
        sim_df = pd.DataFrame([{
            'Escenario': r['scenario_name'],
            'Lift': f"{r['config']['lift']:.0f}%",
            'Duración': f"{r['config']['duration']}d",
            'Poder': f"{r['power']:.0f}%",
            'MDE': f"{r['mde']:.1f}%",
            'Viable': '✅' if r['is_viable'] else '⚠️',
            'Recomendación': r['recommendation']
        } for r in sim_results])
        
        st.dataframe(sim_df, use_container_width=True, hide_index=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.button("← Volver", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    with nav_col3:
        if st.button("Continuar →", type="primary", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()

# ============================================
# STEP 4: EXPORT
# ============================================
elif st.session_state.current_step == 4:
    result = st.session_state.power_results
    treatment = st.session_state.treatment_cities
    control = st.session_state.control_cities
    config = st.session_state.config
    
    st.markdown("""
    <div class="success-box">
        <strong>🎉 ¡Plan de test listo!</strong> — Descargá el resumen para compartir con tu equipo.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Configuración del Test</div>', unsafe_allow_html=True)
        st.markdown(f"""
        | Parámetro | Valor |
        |-----------|-------|
        | **Ciudades Tratamiento** | {', '.join(treatment)} |
        | **Ciudades Control** | {', '.join(control)} |
        | **Duración** | {config['test_duration']} días |
        | **Lift esperado** | {config['expected_lift']*100:.0f}% |
        | **Nivel de confianza** | {config['confidence_level']*100:.0f}% |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Resultados del Análisis</div>', unsafe_allow_html=True)
        
        power_status = "✅" if result['is_powered'] else "⚠️"
        mde_ok = result['mde_percent'] < config['expected_lift'] * 100
        mde_status = "✅" if mde_ok else "⚠️"
        
        st.markdown(f"""
        | Métrica | Valor | Status |
        |---------|-------|--------|
        | **Poder Estadístico** | {result['power_percent']:.0f}% | {power_status} |
        | **MDE** | {result['mde_percent']:.1f}% | {mde_status} |
        | **Clientes/día (Trat.)** | {result['treatment_mean']:.0f} | - |
        | **Clientes/día (Ctrl.)** | {result['control_mean']:.0f} | - |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Export section
    st.markdown("---")
    st.markdown("### 📥 Descargar documentos")
    
    # Generate report
    report = f"""# 📊 Plan de GeoLift Test

## Configuración del Experimento

| Parámetro | Valor |
|-----------|-------|
| **Ciudades Tratamiento** | {', '.join(treatment)} |
| **Ciudades Control** | {', '.join(control)} |
| **Duración planificada** | {config['test_duration']} días |
| **Lift esperado** | {config['expected_lift']*100:.0f}% |
| **Nivel de confianza** | {config['confidence_level']*100:.0f}% |

## Resultados del Análisis de Poder

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **Poder Estadístico** | {result['power_percent']:.1f}% | {'✅ Adecuado (≥80%)' if result['is_powered'] else '⚠️ Insuficiente (<80%)'} |
| **MDE** | {result['mde_percent']:.1f}% | {'✅ Menor al lift esperado' if mde_ok else '⚠️ Mayor al lift esperado'} |

## Métricas Base

- **Promedio Tratamiento:** {result['treatment_mean']:.0f} clientes/día
- **Promedio Control:** {result['control_mean']:.0f} clientes/día
- **Total ciudades:** {len(treatment)} tratamiento + {len(control)} control

## Recomendación

{'✅ **El diseño es viable.** Podés proceder con el test según lo planificado.' if result['is_powered'] and mde_ok else '⚠️ **Ajustes recomendados.** Considerá aumentar la duración del test o revisar el lift esperado.'}

---
*Generado con GeoLift Calculator*
"""
    
    exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)
    
    with exp_col1:
        st.download_button(
            "📄 Plan (Markdown)",
            report,
            "geolift_test_plan.md",
            "text/markdown",
            use_container_width=True
        )
    
    with exp_col2:
        cities_df = pd.DataFrame({
            'city': treatment + control,
            'group': ['treatment'] * len(treatment) + ['control'] * len(control),
            'daily_avg': [st.session_state.pretest_data[st.session_state.pretest_data['city'] == c]['new_customers'].mean() 
                         for c in treatment + control]
        })
        st.download_button(
            "📊 Ciudades (CSV)",
            cities_df.to_csv(index=False),
            "geolift_cities.csv",
            "text/csv",
            use_container_width=True
        )
    
    with exp_col3:
        # Excel with multiple sheets
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Config sheet
            config_df = pd.DataFrame({
                'Parámetro': ['Ciudades Tratamiento', 'Ciudades Control', 'Duración (días)', 
                             'Lift Esperado (%)', 'Nivel Confianza (%)', 'Poder Estadístico (%)', 
                             'MDE (%)', 'Promedio Trat.', 'Promedio Ctrl.'],
                'Valor': [', '.join(treatment), ', '.join(control), config['test_duration'],
                         config['expected_lift']*100, config['confidence_level']*100,
                         result['power_percent'], result['mde_percent'],
                         result['treatment_mean'], result['control_mean']]
            })
            config_df.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Cities sheet
            cities_df.to_excel(writer, sheet_name='Ciudades', index=False)
            
            # Scenarios comparison if available
            if st.session_state.saved_scenarios:
                scenarios_df = create_scenario_comparison(st.session_state.saved_scenarios)
                scenarios_df.to_excel(writer, sheet_name='Escenarios', index=False)
            
            # Historical data preview
            st.session_state.pretest_data.head(100).to_excel(writer, sheet_name='Datos Históricos', index=False)
        
        excel_buffer.seek(0)
        st.download_button(
            "📗 Reporte (Excel)",
            excel_buffer,
            "geolift_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with exp_col4:
        if st.button("🔄 Nuevo Test", use_container_width=True):
            st.session_state.current_step = 1
            st.session_state.pretest_data = None
            st.session_state.treatment_cities = []
            st.session_state.control_cities = []
            st.session_state.power_results = None
            st.session_state.saved_scenarios = []
            st.rerun()
    
    # Show saved scenarios if any
    if st.session_state.saved_scenarios:
        st.markdown("---")
        st.markdown("### 📊 Escenarios Comparados")
        comparison_df = create_scenario_comparison(st.session_state.saved_scenarios)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # =========================================
    # NEW: Save to History
    # =========================================
    st.markdown("---")
    st.markdown("### 💾 Guardar en Histórico")
    
    with st.expander("ℹ️ ¿Para qué sirve el histórico?"):
        st.markdown("""
        Guardar tus tests te permite:
        
        - **Comparar** con tests anteriores
        - **Aprender** de resultados pasados
        - **Benchmarking** de performance
        - **Trazabilidad** para stakeholders
        """)
    
    hist_col1, hist_col2 = st.columns([3, 1])
    
    with hist_col1:
        test_name = st.text_input(
            "Nombre del test",
            value=f"GeoLift {datetime.datetime.now().strftime('%Y-%m-%d')}",
            placeholder="Ej: Q1 2026 - Awareness Campaign"
        )
        test_notes = st.text_area(
            "Notas (opcional)",
            placeholder="Contexto adicional sobre el test...",
            height=80
        )
    
    with hist_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Guardar Test", type="primary", use_container_width=True):
            test_id = test_history.save_pretest(
                name=test_name,
                treatment_cities=treatment,
                control_cities=control,
                duration_days=config['test_duration'],
                expected_lift=config['expected_lift'],
                confidence_level=config['confidence_level'],
                power_result=result,
                notes=test_notes
            )
            st.success(f"✅ Test guardado! ID: `{test_id}`")
    
    # Show history stats
    benchmarks = test_history.get_benchmarks()
    if benchmarks['n_tests'] > 0:
        st.markdown(f"""
        **📊 Benchmarks históricos:** {benchmarks['n_tests']} tests guardados | 
        Lift promedio: {benchmarks['lift_stats']['mean']:.1f}% | 
        Tasa de significancia: {benchmarks['significance_rate']:.0f}%
        """)
    
    # Navigation
    st.markdown("---")
    if st.button("← Volver al Análisis", use_container_width=True):
        st.session_state.current_step = 3
        st.rerun()
