"""
GeoLift Calculator - Main Application
Marketing Intelligence Tool
"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="GeoLift Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Font Stack */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif;
    }
    
    /* Color Palette */
    :root {
        --primary-navy: #002F6C;
        --primary-gold: #C6A34F;
        --primary-red: #E31837;
        --primary-light-gold: #F5EBD7;
        --primary-cream: #FAF8F3;
        --primary-dark: #1A1A2E;
    }
    
    /* Page background */
    .stApp {
        background: linear-gradient(180deg, var(--primary-cream) 0%, #ffffff 100%);
    }
    
    /* Main Hero */
    .main-hero {
        text-align: center;
        padding: 50px 20px;
        position: relative;
    }
    
    .hero-badge {
        display: inline-block;
        background: var(--primary-gold);
        color: var(--primary-navy);
        font-size: 0.75rem;
        font-weight: 700;
        padding: 6px 16px;
        border-radius: 20px;
        margin-bottom: 20px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        color: var(--primary-navy);
        margin-bottom: 12px;
        letter-spacing: -1px;
    }
    
    .hero-title span {
        background: linear-gradient(135deg, var(--primary-gold) 0%, #E8D5A3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        color: #555;
        max-width: 600px;
        margin: 0 auto 40px auto;
        line-height: 1.7;
        font-weight: 400;
    }
    
    /* Module Cards */
    .module-card {
        background: white;
        border-radius: 16px;
        padding: 36px;
        box-shadow: 0 4px 24px rgba(0, 47, 108, 0.08);
        border: 1px solid rgba(198, 163, 79, 0.2);
        transition: all 0.3s ease;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .module-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-navy) 0%, var(--primary-gold) 100%);
    }
    
    .module-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(0, 47, 108, 0.15);
    }
    
    .module-icon {
        font-size: 2.8rem;
        margin-bottom: 20px;
    }
    
    .module-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--primary-navy);
        margin-bottom: 12px;
    }
    
    .module-desc {
        color: #666;
        font-size: 0.95rem;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    
    .module-features {
        text-align: left;
        margin: 24px 0;
        padding: 0;
        list-style: none;
    }
    
    .module-features li {
        padding: 10px 0;
        color: #444;
        font-size: 0.9rem;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .module-features li:last-child {
        border-bottom: none;
    }
    
    .feature-check {
        color: var(--primary-gold);
        font-weight: bold;
    }
    
    /* Steps Section */
    .steps-section {
        background: var(--primary-navy);
        padding: 60px 20px;
        margin: 60px -100vw;
        padding-left: calc(100vw - 50%);
        padding-right: calc(100vw - 50%);
    }
    
    .steps-title {
        text-align: center;
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 40px;
    }
    
    .step-item {
        text-align: center;
        padding: 20px;
    }
    
    .step-number {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: var(--primary-gold);
        color: var(--primary-navy);
        font-size: 1.4rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 16px;
        box-shadow: 0 4px 15px rgba(198, 163, 79, 0.4);
    }
    
    .step-title {
        font-weight: 600;
        color: white;
        margin-bottom: 8px;
        font-size: 1.05rem;
    }
    
    .step-desc {
        color: rgba(255,255,255,0.7);
        font-size: 0.85rem;
    }
    
    /* Info Banner */
    .info-banner {
        background: linear-gradient(135deg, var(--primary-light-gold) 0%, #F8F3E8 100%);
        border-radius: 12px;
        padding: 24px 28px;
        margin: 40px 0;
        border-left: 4px solid var(--primary-gold);
    }
    
    .info-banner strong {
        color: var(--primary-navy);
    }
    
    /* Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-navy) 0%, #004494 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 14px 28px;
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #003d80 0%, var(--primary-navy) 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 47, 108, 0.3);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 40px 20px;
        color: #888;
        font-size: 0.85rem;
    }
    
    .footer-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 12px;
    }
    
    .footer-logo span {
        font-weight: 700;
        color: var(--primary-navy);
        font-size: 1rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.2rem;
        }
        .module-card {
            padding: 24px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Hero section
st.markdown("""
<div class="main-hero">
    <div class="hero-badge">Marketing Intelligence</div>
    <div class="hero-title">📊 GeoLift <span>Calculator</span></div>
    <div class="hero-subtitle">
        Planificá y analizá experimentos de incrementalidad geográfica 
        para medir el impacto real de tus campañas de marketing
    </div>
</div>
""", unsafe_allow_html=True)

# Module cards
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <div class="module-card">
        <div class="module-icon">📊</div>
        <div class="module-title">Pre-Test Calculator</div>
        <div class="module-desc">Diseñá tu experimento con poder estadístico óptimo</div>
        <ul class="module-features">
            <li><span class="feature-check">✓</span> Calculá el poder estadístico</li>
            <li><span class="feature-check">✓</span> Determiná la duración óptima</li>
            <li><span class="feature-check">✓</span> Seleccioná ciudades tratamiento/control</li>
            <li><span class="feature-check">✓</span> Validá tu hipótesis de lift</li>
            <li><span class="feature-check">✓</span> Exportá el plan completo</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Comenzar Pre-Test", type="primary", use_container_width=True, key="pretest"):
        st.switch_page("pages/1_📊_Pre_Test_Calculator.py")

with col2:
    st.markdown("""
    <div class="module-card">
        <div class="module-icon">📈</div>
        <div class="module-title">Post-Test Analyzer</div>
        <div class="module-desc">Analizá los resultados y medí el incremento real</div>
        <ul class="module-features">
            <li><span class="feature-check">✓</span> Calculá el incremento causal</li>
            <li><span class="feature-check">✓</span> Evaluá significancia estadística</li>
            <li><span class="feature-check">✓</span> Compará ciudades/regiones</li>
            <li><span class="feature-check">✓</span> Generá insights automáticos</li>
            <li><span class="feature-check">✓</span> Exportá el reporte ejecutivo</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Comenzar Post-Test", type="primary", use_container_width=True, key="posttest"):
        st.switch_page("pages/2_📈_Post_Test_Analyzer.py")

# How it works
st.markdown("---")

st.markdown("""
<div style="text-align: center; margin: 40px 0 20px 0;">
    <h2 style="color: #002F6C; font-weight: 700;">🎯 ¿Cómo funciona?</h2>
</div>
""", unsafe_allow_html=True)

step_col1, step_col2, step_col3 = st.columns(3)

with step_col1:
    st.markdown("""
    <div class="step-item" style="background: #002F6C; border-radius: 12px; padding: 32px 20px;">
        <div class="step-number">1</div>
        <div class="step-title">Prepará tus datos</div>
        <div class="step-desc">Usá el template CSV o cargá datos demo para empezar rápido</div>
    </div>
    """, unsafe_allow_html=True)

with step_col2:
    st.markdown("""
    <div class="step-item" style="background: #002F6C; border-radius: 12px; padding: 32px 20px;">
        <div class="step-number">2</div>
        <div class="step-title">Configurá el test</div>
        <div class="step-desc">Definí ciudades, duración y validá el poder estadístico</div>
    </div>
    """, unsafe_allow_html=True)

with step_col3:
    st.markdown("""
    <div class="step-item" style="background: #002F6C; border-radius: 12px; padding: 32px 20px;">
        <div class="step-number">3</div>
        <div class="step-title">Analizá resultados</div>
        <div class="step-desc">Medí el incremento real y exportá el reporte ejecutivo</div>
    </div>
    """, unsafe_allow_html=True)

# Info banner
st.markdown("""
<div class="info-banner">
    <strong>💡 ¿Qué es GeoLift?</strong><br><br>
    <strong>GeoLift</strong> es una metodología de medición de incrementalidad que compara 
    regiones donde se ejecuta la campaña (tratamiento) contra regiones donde no (control), 
    permitiendo medir el <strong>impacto causal</strong> de las acciones de marketing, 
    aislando el efecto real de factores externos.
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <div class="footer-logo">
        <span>📊 GeoLift Calculator</span>
    </div>
    <div>GeoLift Calculator v2.0 | Marketing Intelligence Tool</div>
</div>
""", unsafe_allow_html=True)
