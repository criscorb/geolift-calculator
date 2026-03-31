"""
Post-Test Analyzer - Analyze your GeoLift experiment results
AB InBev Marketing Intelligence Tool
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
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.increment_calc import IncrementCalculator
from engine.difference_in_diff import DifferenceInDiff, prepare_did_data
from engine.synthetic_control import SyntheticControl
from engine.utils import (
    validate_data, parse_dates_flexible, calculate_data_quality_score,
    get_faq_content
)
from engine.history import TestHistory
import datetime

# Initialize history
test_history = TestHistory()

st.set_page_config(page_title="Post-Test Analyzer | AB InBev", page_icon="🍺", layout="wide")

# ============================================
# AB InBev CUSTOM CSS
# ============================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* AB InBev Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    :root {
        --abi-navy: #002F6C;
        --abi-gold: #C6A34F;
        --abi-red: #E31837;
        --abi-light-gold: #F5EBD7;
        --abi-cream: #FAF8F3;
        --abi-success: #2E7D32;
        --abi-warning: #F57C00;
    }
    
    .stApp {
        background: linear-gradient(180deg, var(--abi-cream) 0%, #ffffff 100%);
    }
    
    /* Headers */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--abi-navy);
        margin-bottom: 4px;
    }
    
    .main-title span {
        color: var(--abi-gold);
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
        background: var(--abi-success);
        color: white;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }
    
    .step-active {
        background: var(--abi-navy);
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
    
    .step-label-done { color: var(--abi-success); }
    .step-label-active { color: var(--abi-navy); }
    .step-label-pending { color: #999; }
    
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
        color: var(--abi-navy);
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
        color: var(--abi-navy);
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #888;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-good { border-left: 4px solid var(--abi-success); }
    .metric-warning { border-left: 4px solid var(--abi-warning); }
    .metric-bad { border-left: 4px solid var(--abi-red); }
    
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
        border-left: 4px solid var(--abi-success);
        margin: 16px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid var(--abi-warning);
        margin: 16px 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid var(--abi-red);
        margin: 16px 0;
    }
    
    .gold-box {
        background: linear-gradient(135deg, var(--abi-light-gold) 0%, #F8F3E8 100%);
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid var(--abi-gold);
        margin: 16px 0;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--abi-navy) 0%, #004494 100%);
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #003d80 0%, var(--abi-navy) 100%);
        box-shadow: 0 4px 15px rgba(0, 47, 108, 0.3);
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
        background: var(--abi-success);
    }
    
    .progress-step-item.active:not(:last-child)::after {
        background: linear-gradient(90deg, var(--abi-navy) 50%, #e0e0e0 50%);
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
        background: var(--abi-success);
        color: white;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }
    
    .progress-circle.active {
        background: var(--abi-navy);
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
    
    .progress-label.completed { color: var(--abi-success); }
    .progress-label.active { color: var(--abi-navy); }
    .progress-label.pending { color: #999; }
</style>
""", unsafe_allow_html=True)

# ============================================
# DARK MODE CSS (applied conditionally)
# ============================================
if 'post_dark_mode' in st.session_state and st.session_state.post_dark_mode:
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
            color: var(--abi-gold) !important;
        }
        
        .metric-value {
            color: var(--abi-gold) !important;
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
if 'posttest_data' not in st.session_state:
    st.session_state.posttest_data = None
if 'increment_results' not in st.session_state:
    st.session_state.increment_results = None
if 'post_step' not in st.session_state:
    st.session_state.post_step = 1
if 'analysis_method' not in st.session_state:
    st.session_state.analysis_method = 'did'
if 'post_dark_mode' not in st.session_state:
    st.session_state.post_dark_mode = False
if 'post_show_faq' not in st.session_state:
    st.session_state.post_show_faq = False

# ============================================
# HEADER WITH CONTROLS
# ============================================
header_col1, header_col2, header_col3, header_col4 = st.columns([1, 7, 2, 2])

with header_col1:
    if st.button("← Home"):
        st.switch_page("app.py")

with header_col3:
    dark_mode = st.toggle("🌙 Dark", value=st.session_state.post_dark_mode, help="Modo oscuro")
    if dark_mode != st.session_state.post_dark_mode:
        st.session_state.post_dark_mode = dark_mode
        st.rerun()

with header_col4:
    if st.button("❓ FAQ", use_container_width=True):
        st.session_state.post_show_faq = not st.session_state.post_show_faq
        st.rerun()

# Title
st.markdown('<h1 class="main-title">📈 Post-Test <span>Analyzer</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analizá los resultados de tu experimento GeoLift</p>', unsafe_allow_html=True)

# ============================================
# VISUAL PROGRESS BAR
# ============================================
steps = [
    ("1", "Datos", 1),
    ("2", "Análisis", 2),
    ("3", "Export", 3)
]

progress_html = '<div class="progress-bar-container">'
for num, label, step_num in steps:
    if step_num < st.session_state.post_step:
        status = "completed"
        icon = "✓"
    elif step_num == st.session_state.post_step:
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
if st.session_state.post_show_faq:
    st.markdown("---")
    st.markdown("### ❓ Preguntas Frecuentes (FAQ)")
    
    faq_items = get_faq_content()
    # Filter FAQs relevant to post-test
    post_test_faqs = [f for f in faq_items if any(k in f['question'].lower() for k in ['did', 'lift', 'p-value', 'iroas', 'sintética'])]
    
    for item in post_test_faqs:
        with st.expander(f"**{item['question']}**"):
            st.markdown(item['answer'])
    
    if st.button("Cerrar FAQ", type="primary"):
        st.session_state.post_show_faq = False
        st.rerun()
    
    st.markdown("---")

# ============================================
# PROGRESS INDICATOR
# ============================================
steps = [
    ("1", "Cargar Resultados"),
    ("2", "Ver Análisis"),
    ("3", "Exportar Reporte")
]

cols = st.columns(len(steps))
for i, (num, name) in enumerate(steps):
    if st.session_state.post_step > i + 1:
        status = "done"
        icon = "✓"
    elif st.session_state.post_step == i + 1:
        status = "active"
        icon = num
    else:
        status = "pending"
        icon = num
    
    with cols[i]:
        st.markdown(f"""
        <div class="progress-step">
            <div class="step-circle step-{status}">{icon}</div>
            <div class="step-label step-label-{status}">{name}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# STEP 1: LOAD RESULTS
# ============================================
if st.session_state.post_step == 1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📁 Paso 1: Cargá los resultados del test</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="gold-box">
            <strong>🚀 ¿Primera vez?</strong> Probá con datos de ejemplo que simulan un test exitoso con ~15% de lift.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ Cargar Resultados Demo", type="primary", use_container_width=True):
            # Create demo data with ~15% lift
            demo_rows = []
            
            # Buenos Aires (treatment) - 15% lift in test period
            for day in range(1, 15):
                period = 'pre' if day <= 7 else 'test'
                base = 150 if period == 'pre' else 173
                customers = int(base * (1 + np.random.uniform(-0.03, 0.03)))
                demo_rows.append({
                    'city': 'Buenos_Aires',
                    'date': f'2024-01-{day:02d}',
                    'new_customers': customers,
                    'group': 'treatment',
                    'period': period
                })
            
            # Córdoba (control) - stable
            for day in range(1, 15):
                period = 'pre' if day <= 7 else 'test'
                customers = int(80 * (1 + np.random.uniform(-0.03, 0.03)))
                demo_rows.append({
                    'city': 'Córdoba',
                    'date': f'2024-01-{day:02d}',
                    'new_customers': customers,
                    'group': 'control',
                    'period': period
                })
            
            df = pd.DataFrame(demo_rows)
            df['date'] = pd.to_datetime(df['date'])
            st.session_state.posttest_data = df
            st.session_state.post_step = 2
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### O subí tu archivo CSV")
        
        uploaded_file = st.file_uploader("Arrastrá tu archivo aquí", type=['csv'], label_visibility="collapsed")
        
        if uploaded_file:
            try:
                with st.spinner("🔄 Procesando archivo..."):
                    time.sleep(0.3)
                    
                    # Support both CSV and Excel
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    required = ['city', 'date', 'new_customers', 'group', 'period']
                    validation = validate_data(df, required)
                    
                    if not validation['is_valid']:
                        for error in validation['errors']:
                            st.error(f"❌ {error}")
                    else:
                        # Parse dates
                        try:
                            df, date_format = parse_dates_flexible(df, 'date')
                            st.info(f"📅 Formato de fecha detectado: `{date_format}`")
                        except:
                            df['date'] = pd.to_datetime(df['date'])
                        
                        st.session_state.posttest_data = df
                        
                        # Quality score
                        quality_score = calculate_data_quality_score(validation)
                        if quality_score >= 90:
                            badge_class, badge_text = "quality-excellent", "Excelente"
                        elif quality_score >= 70:
                            badge_class, badge_text = "quality-good", "Buena"
                        elif quality_score >= 50:
                            badge_class, badge_text = "quality-fair", "Regular"
                        else:
                            badge_class, badge_text = "quality-poor", "Baja"
                        
                        n_cities = df['city'].nunique()
                        n_rows = len(df)
                        
                        sum_col1, sum_col2 = st.columns([3, 1])
                        with sum_col1:
                            st.success(f"✅ **{n_rows:,}** registros cargados de **{n_cities}** ciudades")
                        with sum_col2:
                            st.markdown(f'<span class="quality-badge {badge_class}">Calidad: {badge_text}</span>', unsafe_allow_html=True)
                        
                        # Show warnings
                        if validation['warnings']:
                            with st.expander(f"⚠️ {len(validation['warnings'])} advertencias"):
                                for warning in validation['warnings']:
                                    st.warning(warning)
                        
                        if st.button("Continuar →", type="primary"):
                            st.session_state.post_step = 2
                            st.rerun()
                            
            except Exception as e:
                st.error(f"❌ Error al procesar: {e}")
                st.info("💡 Asegurate que el archivo tenga las columnas requeridas.")
    
    with col2:
        st.markdown("#### 📋 Formato requerido")
        
        with st.expander("ℹ️ ¿Qué columnas necesito?", expanded=True):
            st.markdown("""
            | Columna | Descripción |
            |---------|-------------|
            | `city` | Nombre de la ciudad |
            | `date` | Fecha (YYYY-MM-DD) |
            | `new_customers` | Clientes nuevos ese día |
            | `group` | **treatment** o **control** |
            | `period` | **pre** o **test** |
            """)
        
        with st.expander("💡 ¿Qué es 'pre' y 'test'?"):
            st.markdown("""
            - **pre:** Período ANTES de la campaña (baseline)
            - **test:** Período DURANTE la campaña
            
            *Necesitás datos de ambos períodos para calcular el incremento real.*
            """)
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'posttest_template.csv')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                st.download_button(
                    "⬇️ Descargar Template",
                    f.read(),
                    "posttest_template.csv",
                    "text/csv",
                    use_container_width=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# STEP 2: ANALYSIS
# ============================================
elif st.session_state.post_step == 2:
    df = st.session_state.posttest_data
    
    treatment_cities = df[df['group'] == 'treatment']['city'].unique().tolist()
    control_cities = df[df['group'] == 'control']['city'].unique().tolist()
    
    # Summary
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Resumen del test</div>', unsafe_allow_html=True)
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(treatment_cities)}</div>
            <div class="metric-label">Ciudades Trat.</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(control_cities)}</div>
            <div class="metric-label">Ciudades Ctrl.</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        pre_days = len(df[(df['group'] == 'treatment') & (df['period'] == 'pre')]['date'].unique())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{pre_days}</div>
            <div class="metric-label">Días Pre-test</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        test_days = len(df[(df['group'] == 'treatment') & (df['period'] == 'test')]['date'].unique())
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{test_days}</div>
            <div class="metric-label">Días Test</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Method selection
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚙️ Metodología de análisis</div>', unsafe_allow_html=True)
    
    # Method explanation
    method_col1, method_col2 = st.columns(2)
    
    with method_col1:
        with st.expander("📊 ¿Qué es DiD (Diferencias en Diferencias)?"):
            st.markdown("""
            Es el método más común y robusto. Compara:
            
            1. **Cambio en Tratamiento:** (Test - Pre)
            2. **Cambio en Control:** (Test - Pre)
            3. **Diferencia = Efecto causal**
            
            ✅ **Ventajas:** Simple, robusto, funciona con múltiples ciudades
            
            ⚠️ **Requiere:** Tendencias paralelas antes del test
            """)
    
    with method_col2:
        with st.expander("🧪 ¿Qué es Synthetic Control?"):
            st.markdown("""
            Crea una "ciudad virtual" combinando ciudades de control para imitar el tratamiento.
            
            ✅ **Ventajas:** Más preciso cuando tenés 1 sola ciudad de tratamiento
            
            ⚠️ **Requiere:** Buen ajuste pre-período, múltiples ciudades de control
            
            *Ideal para: 1 ciudad de tratamiento vs varias de control*
            """)
    
    method = st.radio(
        "Seleccioná el método:",
        ['did', 'synthetic'],
        format_func=lambda x: '📊 Diferencias en Diferencias (DiD) — Recomendado' if x == 'did' else '🧪 Synthetic Control',
        horizontal=True
    )
    st.session_state.analysis_method = method
    
    if method == 'did':
        st.caption("✅ DiD es el estándar de la industria para GeoLift tests")
    else:
        st.caption("🧪 Synthetic Control es ideal cuando tenés 1 sola ciudad de tratamiento")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculate
    calc = IncrementCalculator(df)
    
    try:
        result = calc.calculate_increment(method=method)
        st.session_state.increment_results = result
        
        # Main results
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Resultado principal</div>', unsafe_allow_html=True)
        
        # Help with concepts
        with st.expander("ℹ️ ¿Cómo interpretar estos resultados?"):
            help_col1, help_col2 = st.columns(2)
            with help_col1:
                st.markdown("""
                **📈 Lift:** El incremento porcentual causado por tu campaña.
                - Lift +15% = 15% más clientes que sin campaña
                
                **👥 Clientes Incrementales:** La cantidad absoluta de clientes adicionales que obtuviste gracias a la campaña.
                """)
            with help_col2:
                st.markdown("""
                **✅ Significativo:** ¿El resultado es confiable o puede ser por azar?
                - **Sí** = Podés confiar en el resultado
                - **No** = El resultado puede ser aleatorio
                
                **📊 IC 95%:** Rango donde está el lift real con 95% de certeza.
                """)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        lift_class = "metric-good" if result['lift_percent'] > 0 and result['is_significant'] else "metric-warning" if result['lift_percent'] > 0 else "metric-bad"
        sig_class = "metric-good" if result['is_significant'] else "metric-warning"
        
        with m_col1:
            st.markdown(f"""
            <div class="metric-card {lift_class}">
                <div class="metric-value">{result['lift_percent']:+.1f}%</div>
                <div class="metric-label">Lift</div>
            </div>
            """, unsafe_allow_html=True)
        
        with m_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{result['total_incremental']:,.0f}</div>
                <div class="metric-label">Clientes Incrementales</div>
            </div>
            """, unsafe_allow_html=True)
        
        with m_col3:
            sig_text = "✅ Sí" if result['is_significant'] else "❌ No"
            st.markdown(f"""
            <div class="metric-card {sig_class}">
                <div class="metric-value">{sig_text}</div>
                <div class="metric-label">Significativo</div>
            </div>
            """, unsafe_allow_html=True)
        
        with m_col4:
            ci_text = f"{result['ci_lower_percent']:.1f}% a {result['ci_upper_percent']:.1f}%"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="font-size: 1.1rem;">{ci_text}</div>
                <div class="metric-label">IC 95%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Interpretation
        st.markdown("<br>", unsafe_allow_html=True)
        
        if result['is_significant'] and result['lift_percent'] > 0:
            st.markdown(f"""
            <div class="success-box">
                <strong>🎉 ¡Éxito!</strong> La campaña generó un incremento estadísticamente significativo.<br>
                Lift de <strong>{result['lift_percent']:.1f}%</strong> con <strong>{result['total_incremental']:,.0f}</strong> clientes adicionales.
            </div>
            """, unsafe_allow_html=True)
        elif result['lift_percent'] > 0 and not result['is_significant']:
            st.markdown(f"""
            <div class="warning-box">
                <strong>⚠️ Resultado positivo pero no significativo</strong><br>
                Hay un lift de {result['lift_percent']:.1f}% pero no podemos confirmar que no sea por azar.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-box">
                <strong>📉 Sin incremento detectado</strong><br>
                La campaña no mostró un efecto positivo. Revisá la estrategia antes de escalar.
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Charts
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📈 Visualizaciones</div>', unsafe_allow_html=True)
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Time series
            ts_data = df.groupby(['date', 'group'])['new_customers'].sum().reset_index()
            
            fig1 = px.line(
                ts_data, x='date', y='new_customers', color='group',
                title='Evolución temporal',
                color_discrete_map={'treatment': '#002F6C', 'control': '#C6A34F'}
            )
            
            test_start = df[df['period'] == 'test']['date'].min()
            fig1.add_vline(x=test_start, line_dash="dash", line_color="#2E7D32", 
                          annotation_text="Inicio test")
            fig1.update_layout(
                height=350,
                plot_bgcolor='white',
                font=dict(family='Montserrat'),
                legend_title_text='Grupo'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with chart_col2:
            # Lift with CI
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=[result['lift_percent']],
                y=['Lift'],
                orientation='h',
                marker_color='#002F6C' if result['is_significant'] else '#F57C00',
                error_x=dict(
                    type='data',
                    symmetric=False,
                    array=[result['ci_upper_percent'] - result['lift_percent']],
                    arrayminus=[result['lift_percent'] - result['ci_lower_percent']],
                    color='#333'
                )
            ))
            
            fig2.add_vline(x=0, line_dash="dash", line_color="#E31837")
            fig2.update_layout(
                title='Lift con Intervalo de Confianza 95%',
                xaxis_title='Lift (%)',
                height=350,
                showlegend=False,
                plot_bgcolor='white',
                font=dict(family='Montserrat')
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # City breakdown
        st.markdown("#### 🏙️ Desglose por Ciudad")
        
        city_breakdown = calc.city_breakdown()
        
        fig3 = px.bar(
            city_breakdown,
            x='city',
            y=['pre_daily_avg', 'test_daily_avg'],
            barmode='group',
            title='Comparación Pre vs Test',
            color_discrete_map={'pre_daily_avg': '#B0BEC5', 'test_daily_avg': '#002F6C'},
            labels={'value': 'Clientes/día', 'city': 'Ciudad', 'variable': 'Período'}
        )
        fig3.update_layout(
            height=350,
            plot_bgcolor='white',
            font=dict(family='Montserrat')
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # =========================================
        # NEW: Cumulative Lift Chart
        # =========================================
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📈 Lift Acumulado día a día</div>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ ¿Qué muestra este gráfico?"):
            st.markdown("""
            Muestra cómo **evoluciona el lift acumulado** durante el período de test.
            
            - **Línea azul:** Clientes reales acumulados
            - **Línea punteada:** Lo que hubieras tenido SIN campaña (counterfactual)
            - **Área verde:** El incremento acumulado
            
            Útil para ver si el efecto es consistente o hay picos específicos.
            """)
        
        cumulative_df = calc.calculate_cumulative_lift()
        
        fig_cum = go.Figure()
        
        fig_cum.add_trace(go.Scatter(
            x=cumulative_df['date'],
            y=cumulative_df['actual_treatment'],
            name='Real (con campaña)',
            line=dict(color='#002F6C', width=3),
            mode='lines'
        ))
        
        fig_cum.add_trace(go.Scatter(
            x=cumulative_df['date'],
            y=cumulative_df['expected_treatment'],
            name='Esperado (sin campaña)',
            line=dict(color='#C6A34F', width=2, dash='dash'),
            mode='lines'
        ))
        
        fig_cum.update_layout(
            xaxis_title='Fecha',
            yaxis_title='Clientes Acumulados',
            height=350,
            plot_bgcolor='white',
            font=dict(family='Montserrat'),
            legend=dict(orientation='h', y=-0.2)
        )
        
        st.plotly_chart(fig_cum, use_container_width=True)
        
        # Show final cumulative lift
        final_lift = cumulative_df['cumulative_lift'].iloc[-1]
        final_lift_pct = cumulative_df['cumulative_lift_pct'].iloc[-1]
        st.markdown(f"""
        <div class="gold-box">
            📊 <strong>Lift acumulado total:</strong> {final_lift:,.0f} clientes ({final_lift_pct:+.1f}%)
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # =========================================
        # NEW: Counterfactual Projection
        # =========================================
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔮 Counterfactual: ¿Qué hubiera pasado sin campaña?</div>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ ¿Qué es el Counterfactual?"):
            st.markdown("""
            El **counterfactual** es una proyección de lo que hubiera pasado 
            en las ciudades de tratamiento **si NO hubieras hecho la campaña**.
            
            Se calcula usando el comportamiento de las ciudades de control 
            y la relación histórica con el tratamiento.
            
            La diferencia entre lo real y el counterfactual = **efecto causal** de la campaña.
            """)
        
        counterfactual_df = calc.generate_counterfactual()
        
        fig_cf = go.Figure()
        
        fig_cf.add_trace(go.Scatter(
            x=counterfactual_df['date'],
            y=counterfactual_df['actual'],
            name='Real',
            line=dict(color='#002F6C', width=2),
            mode='lines'
        ))
        
        fig_cf.add_trace(go.Scatter(
            x=counterfactual_df['date'],
            y=counterfactual_df['counterfactual'],
            name='Counterfactual (sin campaña)',
            line=dict(color='#E31837', width=2, dash='dot'),
            mode='lines'
        ))
        
        # Add vertical line at test start
        test_start = counterfactual_df[counterfactual_df['period'] == 'test']['date'].min()
        fig_cf.add_vline(x=test_start, line_dash="dash", line_color="#2E7D32", 
                        annotation_text="Inicio Test")
        
        fig_cf.update_layout(
            xaxis_title='Fecha',
            yaxis_title='Clientes/día',
            height=350,
            plot_bgcolor='white',
            font=dict(family='Montserrat'),
            legend=dict(orientation='h', y=-0.2)
        )
        
        st.plotly_chart(fig_cf, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # =========================================
        # NEW: Placebo Test
        # =========================================
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🧪 Placebo Test (Validación)</div>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ ¿Qué es un Placebo Test?"):
            st.markdown("""
            El **Placebo Test** verifica que tu diseño experimental sea válido.
            
            Simula un "test falso" usando solo datos del período PRE 
            (donde NO debería haber ningún efecto).
            
            - **PASA** ✅ = No detecta efecto falso. Tu diseño es válido.
            - **FALLA** ⚠️ = Detecta efecto donde no debería. Hay problemas.
            
            Es como un "control de calidad" del experimento.
            """)
        
        placebo_result = calc.run_placebo_test()
        
        if 'error' not in placebo_result:
            placebo_col1, placebo_col2 = st.columns(2)
            
            with placebo_col1:
                placebo_class = "metric-good" if placebo_result['is_valid'] else "metric-warning"
                placebo_text = "✅ PASÓ" if placebo_result['is_valid'] else "⚠️ REVISAR"
                st.markdown(f"""
                <div class="metric-card {placebo_class}">
                    <div class="metric-value">{placebo_text}</div>
                    <div class="metric-label">Resultado Placebo</div>
                </div>
                """, unsafe_allow_html=True)
            
            with placebo_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{placebo_result['placebo_lift_pct']:.1f}%</div>
                    <div class="metric-label">Lift Placebo (debería ser ~0)</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"<br>{placebo_result['interpretation']}", unsafe_allow_html=True)
        else:
            st.warning(placebo_result['error'])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # =========================================
        # NEW: ROI Calculator
        # =========================================
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💰 Calculadora de ROI</div>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ ¿Cómo se calcula el ROI?"):
            st.markdown("""
            **ROI** = (Revenue Incremental - Inversión) / Inversión × 100
            
            **iROAS** = Revenue Incremental / Inversión
            
            - iROAS > 1 = Rentable ✅
            - iROAS < 1 = No rentable ❌
            """)
        
        roi_col1, roi_col2 = st.columns(2)
        
        with roi_col1:
            media_spend = st.number_input(
                "💵 Inversión en medios durante el test ($)",
                min_value=1000, max_value=10000000, value=50000, step=5000,
                help="Total invertido en medios durante el período de test"
            )
        
        with roi_col2:
            customer_value = st.number_input(
                "👤 Valor promedio por cliente ($)",
                min_value=100, max_value=10000, value=500, step=50,
                help="Customer Lifetime Value o valor del primer pedido"
            )
        
        roi_calc = calc.calculate_roi(media_spend, customer_value)
        
        roi_m1, roi_m2, roi_m3 = st.columns(3)
        
        with roi_m1:
            roi_class = "metric-good" if roi_calc['roi_percent'] > 0 else "metric-bad"
            st.markdown(f"""
            <div class="metric-card {roi_class}">
                <div class="metric-value">{roi_calc['roi_percent']:.0f}%</div>
                <div class="metric-label">ROI</div>
            </div>
            """, unsafe_allow_html=True)
        
        with roi_m2:
            iroas_class = "metric-good" if roi_calc['iroas'] > 1 else "metric-warning"
            st.markdown(f"""
            <div class="metric-card {iroas_class}">
                <div class="metric-value">{roi_calc['iroas']:.2f}x</div>
                <div class="metric-label">iROAS</div>
            </div>
            """, unsafe_allow_html=True)
        
        with roi_m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">${roi_calc['cost_per_incremental_customer']:,.0f}</div>
                <div class="metric-label">Costo por Cliente Incr.</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"<br>{roi_calc['interpretation']}", unsafe_allow_html=True)
        
        # Break-even info
        st.markdown(f"""
        <div class="gold-box">
            📊 <strong>Break-even:</strong> Necesitabas al menos {roi_calc['break_even_lift_pct']:.1f}% de lift para ser rentable.
            {'✅ Lo superaste!' if result['lift_percent'] > roi_calc['break_even_lift_pct'] else ''}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # =========================================
        # NEW: Bootstrap Confidence Intervals
        # =========================================
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Intervalos de Confianza Bootstrap</div>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ ¿Por qué Bootstrap?"):
            st.markdown("""
            El método **Bootstrap** es más robusto que los intervalos tradicionales:
            
            - No asume distribución normal
            - Funciona mejor con pocos datos
            - Captura la incertidumbre real del experimento
            - Es el estándar usado por Meta en GeoLift
            
            Si el intervalo NO incluye el cero, el efecto es **estadísticamente robusto**.
            """)
        
        with st.spinner("Calculando Bootstrap CI (1000 iteraciones)..."):
            bootstrap_result = calc.calculate_bootstrap_lift_ci(n_bootstrap=1000, confidence_level=0.95)
        
        if 'error' not in bootstrap_result:
            boot_col1, boot_col2, boot_col3 = st.columns(3)
            
            with boot_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{bootstrap_result['point_estimate']:.1f}%</div>
                    <div class="metric-label">Lift (DiD)</div>
                </div>
                """, unsafe_allow_html=True)
            
            with boot_col2:
                ci_text = f"[{bootstrap_result['ci_lower']:.1f}%, {bootstrap_result['ci_upper']:.1f}%]"
                ci_class = "metric-good" if bootstrap_result['is_significant'] else "metric-warning"
                st.markdown(f"""
                <div class="metric-card {ci_class}">
                    <div class="metric-value" style="font-size:1.3rem;">{ci_text}</div>
                    <div class="metric-label">IC 95% Bootstrap</div>
                </div>
                """, unsafe_allow_html=True)
            
            with boot_col3:
                sig_text = "✅ Sí" if bootstrap_result['is_significant'] else "⚠️ No"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{sig_text}</div>
                    <div class="metric-label">Robusto?</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"<br>{bootstrap_result['interpretation']}", unsafe_allow_html=True)
        else:
            st.warning(bootstrap_result['error'])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        
        with nav_col1:
            if st.button("← Volver", use_container_width=True):
                st.session_state.post_step = 1
                st.rerun()
        
        with nav_col3:
            if st.button("Continuar →", type="primary", use_container_width=True):
                st.session_state.post_step = 3
                st.rerun()
                
    except Exception as e:
        st.error(f"Error en el análisis: {e}")
        if st.button("← Volver a cargar datos"):
            st.session_state.post_step = 1
            st.rerun()

# ============================================
# STEP 3: EXPORT
# ============================================
elif st.session_state.post_step == 3:
    result = st.session_state.increment_results
    df = st.session_state.posttest_data
    calc = IncrementCalculator(df)
    
    treatment_cities = df[df['group'] == 'treatment']['city'].unique().tolist()
    control_cities = df[df['group'] == 'control']['city'].unique().tolist()
    
    st.markdown("""
    <div class="success-box">
        <strong>🎉 ¡Análisis completo!</strong> Descargá el reporte para compartir con tu equipo.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 Resumen de resultados</div>', unsafe_allow_html=True)
        
        lift_status = "✅" if result['is_significant'] and result['lift_percent'] > 0 else "⚠️" if result['lift_percent'] > 0 else "❌"
        
        st.markdown(f"""
        | Métrica | Valor | Status |
        |---------|-------|--------|
        | **Lift** | {result['lift_percent']:+.1f}% | {lift_status} |
        | **Clientes incrementales** | {result['total_incremental']:,.0f} | - |
        | **Significativo** | {'Sí' if result['is_significant'] else 'No'} | {'✅' if result['is_significant'] else '⚠️'} |
        | **IC 95%** | {result['ci_lower_percent']:.1f}% a {result['ci_upper_percent']:.1f}% | - |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚙️ Configuración del test</div>', unsafe_allow_html=True)
        st.markdown(f"""
        | Parámetro | Valor |
        |-----------|-------|
        | **Tratamiento** | {', '.join(treatment_cities)} |
        | **Control** | {', '.join(control_cities)} |
        | **Metodología** | {result['method'].upper()} |
        | **Días de test** | {result.get('test_days', 'N/A')} |
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Insights
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💡 Insights automáticos</div>', unsafe_allow_html=True)
    insights = calc.generate_insights(result)
    st.markdown(insights)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Downloads
    st.markdown("### 📥 Descargar documentos")
    
    # Generate executive report
    verdict = "✅ ÉXITO" if result['is_significant'] and result['lift_percent'] > 0 else "⚠️ NO CONCLUYENTE" if result['lift_percent'] > 0 else "❌ SIN EFECTO"
    
    report = f"""# 📈 Reporte de Resultados - GeoLift Test | AB InBev

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Lift** | {result['lift_percent']:+.1f}% |
| **Clientes Incrementales** | {result['total_incremental']:,.0f} |
| **Estadísticamente Significativo** | {'Sí ✅' if result['is_significant'] else 'No ⚠️'} |
| **Intervalo de Confianza 95%** | {result['ci_lower_percent']:.1f}% a {result['ci_upper_percent']:.1f}% |

## Veredicto: {verdict}

{'La campaña generó un incremento estadísticamente significativo. Se recomienda escalar la inversión.' if result['is_significant'] and result['lift_percent'] > 0 else 'Los resultados no son concluyentes. Se recomienda optimizar antes de escalar.' if result['lift_percent'] > 0 else 'La campaña no mostró efecto positivo. Se recomienda revisar la estrategia.'}

## Configuración del Test

- **Ciudades Tratamiento:** {', '.join(treatment_cities)}
- **Ciudades Control:** {', '.join(control_cities)}
- **Metodología:** {result['method']}
- **Días de test:** {result.get('test_days', 'N/A')}

## Insights

{insights}

---
*Generado con GeoLift Calculator | AB InBev Marketing Intelligence*
"""
    
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
    with dl_col1:
        st.download_button(
            "📄 Reporte Ejecutivo (Markdown)",
            report,
            "geolift_results.md",
            "text/markdown",
            use_container_width=True
        )
    
    with dl_col2:
        city_breakdown = calc.city_breakdown()
        st.download_button(
            "📊 Datos por Ciudad (CSV)",
            city_breakdown.to_csv(index=False),
            "geolift_city_data.csv",
            "text/csv",
            use_container_width=True
        )
    
    with dl_col3:
        if st.button("🔄 Nuevo Análisis", use_container_width=True):
            st.session_state.post_step = 1
            st.session_state.posttest_data = None
            st.session_state.increment_results = None
            st.rerun()
    
    # =========================================
    # NEW: Save to History
    # =========================================
    st.markdown("---")
    st.markdown("### 💾 Guardar en Histórico")
    
    with st.expander("ℹ️ ¿Para qué sirve?"):
        st.markdown("""
        Guardar tus resultados permite:
        
        - **Comparar** con tests anteriores
        - **Benchmarking** de performance
        - **Aprendizaje** continuo
        - **Trazabilidad** para stakeholders
        """)
    
    hist_col1, hist_col2 = st.columns([3, 1])
    
    with hist_col1:
        test_name = st.text_input(
            "Nombre del test",
            value=f"GeoLift Results {datetime.datetime.now().strftime('%Y-%m-%d')}",
            placeholder="Ej: Q1 2026 - Awareness Results",
            key="posttest_name"
        )
        test_notes = st.text_area(
            "Notas (opcional)",
            placeholder="Learnings, contexto, próximos pasos...",
            height=80,
            key="posttest_notes"
        )
    
    with hist_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Guardar Resultados", type="primary", use_container_width=True):
            # Calculate ROI if available
            try:
                roi_result = calc.calculate_roi(50000, 500)  # Default values
            except:
                roi_result = None
            
            test_id = test_history.save_posttest(
                name=test_name,
                treatment_cities=treatment_cities,
                control_cities=control_cities,
                actual_duration=result.get('test_days'),
                lift_result=result,
                roi_result=roi_result,
                notes=test_notes
            )
            st.success(f"✅ Resultados guardados! ID: `{test_id}`")
    
    # Show history stats
    benchmarks = test_history.get_benchmarks()
    if benchmarks['n_tests'] > 0:
        st.markdown(f"""
        **📊 Benchmarks históricos:** {benchmarks['n_tests']} tests completados | 
        Lift promedio: {benchmarks['lift_stats']['mean']:.1f}% | 
        Tasa de significancia: {benchmarks['significance_rate']:.0f}%
        """)
        
        # Compare to benchmarks
        if result['lift_percent'] > benchmarks['lift_stats']['mean']:
            st.markdown(f"""
            <div class="gold-box">
                🏆 <strong>Este test supera el promedio histórico!</strong> 
                ({result['lift_percent']:.1f}% vs {benchmarks['lift_stats']['mean']:.1f}% promedio)
            </div>
            """, unsafe_allow_html=True)
    
    # Navigation
    st.markdown("---")
    if st.button("← Volver al Análisis", use_container_width=True):
        st.session_state.post_step = 2
        st.rerun()
