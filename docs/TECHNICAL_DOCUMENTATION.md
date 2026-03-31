# 📘 Documentación Técnica - GeoLift Calculator AB InBev

## 1. Información General

| Campo | Valor |
|-------|-------|
| **Nombre del Producto** | GeoLift Test Calculator |
| **Versión** | 2.2.0 |
| **Organización** | AB InBev - Marketing Intelligence |
| **Framework** | Python + Streamlit |
| **Fecha de Desarrollo** | Marzo 2026 |
| **Estado** | Producción |

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      CAPA DE PRESENTACIÓN                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │     app.py      │  │  Pre-Test Calc  │  │  Post-Test  │  │
│  │   (Homepage)    │  │    (Page 1)     │  │  (Page 2)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      CAPA DE LÓGICA (ENGINE)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ PowerAnalysis│  │IncrementCalc │  │ SyntheticControl │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   DiD        │  │  Statistics  │  │  Visualizations  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    Utils     │  │   History    │                         │
│  └──────────────┘  └──────────────┘                         │
├─────────────────────────────────────────────────────────────┤
│                      CAPA DE DATOS                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  CSV Upload  │  │  Templates   │  │  JSON History    │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Estructura de Carpetas

```
GeoLift Test Pre Set Calculator/
├── app.py                          # Aplicación principal (Homepage)
├── requirements.txt                # Dependencias Python
├── README.md                       # Documentación básica
│
├── pages/                          # Páginas de Streamlit
│   ├── 1_📊_Pre_Test_Calculator.py # Módulo Pre-Test
│   └── 2_📈_Post_Test_Analyzer.py  # Módulo Post-Test
│
├── engine/                         # Motor de cálculos
│   ├── __init__.py                 # Exports del módulo
│   ├── power_analysis.py           # Análisis de poder estadístico
│   ├── increment_calc.py           # Cálculo de incrementos
│   ├── difference_in_diff.py       # Método DiD
│   ├── synthetic_control.py        # Control sintético
│   ├── statistics.py               # Funciones estadísticas base
│   ├── utils.py                    # Utilidades y validación
│   ├── visualizations.py           # Gráficos y exports
│   └── history.py                  # Gestión de histórico
│
├── templates/                      # Plantillas CSV
│   ├── pretest_template.csv
│   └── posttest_template.csv
│
├── data/                           # Datos persistentes
│   └── test_history.json
│
├── logs/                           # Logs de producción
│   └── geolift_YYYYMMDD.log
│
└── docs/                           # Documentación
    ├── TECHNICAL_DOCUMENTATION.md
    ├── BITACORA.md
    └── USER_GUIDE.md
```

---

## 3. Módulos del Sistema

### 3.1 PowerAnalysis (`engine/power_analysis.py`)

**Propósito:** Calcular poder estadístico, MDE, y recomendar configuraciones de test.

**Clase Principal:** `PowerAnalysis`

**Métodos Clave:**

| Método | Descripción | Parámetros |
|--------|-------------|------------|
| `calculate_test_power()` | Calcula poder estadístico | treatment_cities, control_cities, expected_lift, test_duration_days, confidence_level |
| `recommend_cities()` | Recomienda ciudades óptimas | n_treatment, n_control |
| `auto_select_locations()` | Selección automática de geos | expected_lift, test_duration, target_power |
| `find_optimal_duration()` | Encuentra duración óptima | treatment_cities, control_cities, expected_lift, target_power |
| `calculate_market_matching_score()` | Score de similitud entre ciudades | treatment_cities, control_cities |
| `calculate_bootstrap_ci()` | Intervalos de confianza bootstrap | treatment_cities, control_cities, n_bootstrap |
| `allocate_budget()` | Asigna presupuesto óptimo | treatment_cities, total_budget, method |
| `simulate_what_if()` | Simulador de escenarios | treatment_cities, control_cities, scenarios |
| `create_synthetic_control()` | Crea control sintético | treatment_cities, control_cities |
| `calculate_mde_heatmap()` | Heatmap de MDE | test_duration, confidence_level |

**Fórmula de Poder Estadístico:**

```python
# Cálculo base
base_power = 1 - beta  # donde beta = prob. error tipo II

# Ajustes aplicados:
- Autocorrelation penalty (tests cortos)
- Geo-level clustering factor
- Investment efficiency adjustment
- Population coverage adjustment

# Power final capped at 95%
power = min(base_power * adjustments, 0.95)
```

### 3.2 IncrementCalculator (`engine/increment_calc.py`)

**Propósito:** Analizar resultados post-test y calcular incrementos.

**Clase Principal:** `IncrementCalculator`

**Métodos Clave:**

| Método | Descripción |
|--------|-------------|
| `calculate_increment()` | Calcula incremento con método DiD o Synthetic |
| `calculate_cumulative_lift()` | Lift acumulado por día |
| `generate_counterfactual()` | Proyección sin campaña |
| `run_placebo_test()` | Validación del diseño |
| `calculate_roi()` | ROI e iROAS |
| `generate_insights()` | Insights automáticos |
| `calculate_bootstrap_lift_ci()` | Bootstrap CI para lift |

### 3.3 DifferenceInDiff (`engine/difference_in_diff.py`)

**Propósito:** Implementar metodología Diferencias en Diferencias.

**Fórmula DiD:**

```
Lift = (Treatment_post - Treatment_pre) - (Control_post - Control_pre)
```

### 3.4 SyntheticControl (`engine/synthetic_control.py`)

**Propósito:** Crear controles sintéticos cuando no hay ciudades espejo.

**Algoritmo:**
1. Minimizar RMSE pre-tratamiento
2. Encontrar pesos óptimos para ciudades donantes
3. Validar con placebo test

### 3.5 Utils (`engine/utils.py`)

**Funciones de Utilidad:**

| Función | Descripción |
|---------|-------------|
| `validate_data()` | Validación completa de datos |
| `detect_date_format()` | Detecta formato de fecha |
| `parse_dates_flexible()` | Parsea fechas automáticamente |
| `detect_and_handle_outliers()` | Detección y manejo de outliers |
| `interpolate_missing_days()` | Interpolación de días faltantes |
| `get_faq_content()` | Contenido FAQ |
| `get_metric_tooltip()` | Tooltips de métricas |
| `setup_logger()` | Configuración de logging |

### 3.6 Visualizations (`engine/visualizations.py`)

**Funciones de Visualización:**

| Función | Output |
|---------|--------|
| `create_sparkline()` | SVG base64 |
| `create_power_gauge()` | Plotly Figure |
| `create_comparison_chart()` | Plotly Figure |
| `create_lift_waterfall()` | Plotly Figure |
| `create_mde_heatmap_chart()` | Plotly Figure |
| `generate_pdf_report()` | PDF bytes |
| `export_to_excel_with_charts()` | Excel bytes |

---

## 4. Tecnologías Utilizadas

### 4.1 Stack Principal

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.12+ | Lenguaje principal |
| Streamlit | ≥1.28.0 | Framework web |
| Pandas | ≥2.0.0 | Manipulación de datos |
| NumPy | ≥1.24.0 | Operaciones numéricas |
| SciPy | ≥1.11.0 | Funciones estadísticas |
| Plotly | ≥5.18.0 | Visualizaciones interactivas |

### 4.2 Dependencias Adicionales

| Librería | Propósito |
|----------|-----------|
| openpyxl | Lectura de Excel |
| xlsxwriter | Escritura de Excel |
| reportlab | Generación de PDF |
| kaleido | Export de gráficos |

---

## 5. Metodologías Estadísticas

### 5.1 Diferencias en Diferencias (DiD)

**Supuestos:**
- Tendencias paralelas entre tratamiento y control
- No anticipación del tratamiento
- No spillover entre grupos

**Implementación:**
```python
# Pre-period
pre_treatment = treatment_data[period == 'pre'].mean()
pre_control = control_data[period == 'pre'].mean()

# Post-period
post_treatment = treatment_data[period == 'test'].mean()
post_control = control_data[period == 'test'].mean()

# DiD Estimate
did = (post_treatment - pre_treatment) - (post_control - pre_control)
```

### 5.2 Control Sintético

**Algoritmo:**
1. Definir ciudades donantes (pool de control)
2. Minimizar distancia pre-tratamiento
3. Encontrar pesos w₁, w₂, ..., wₙ tal que:
   - Σwᵢ = 1
   - wᵢ ≥ 0
4. Ciudad sintética = Σwᵢ × ciudadᵢ

### 5.3 Cálculo de Poder

**Fórmula Base:**
```
Power = 1 - β = 1 - Φ(z_{1-α/2} - δ/σ × √n)

Donde:
- α = nivel de significancia (1 - confidence_level)
- δ = efecto esperado (expected_lift × mean)
- σ = desviación estándar pooled
- n = tamaño de muestra (días × ciudades)
```

### 5.4 Bootstrap Confidence Intervals

**Implementación:**
1. Resamplear datos B veces (default: 1000)
2. Calcular estadístico de interés en cada muestra
3. Obtener percentiles 2.5 y 97.5

---

## 6. Seguridad y Privacidad

### 6.1 Manejo de Datos

- Los datos se procesan en memoria
- No se envían a servidores externos
- El histórico se guarda localmente en JSON
- Los logs no contienen datos sensibles

### 6.2 Validación de Inputs

- Validación de tipos de datos
- Sanitización de nombres de archivo
- Límites en tamaño de uploads
- Manejo de errores graceful

---

## 7. Performance

### 7.1 Optimizaciones

| Técnica | Implementación |
|---------|----------------|
| Caching | `@st.cache_data` para cálculos pesados |
| Lazy loading | Carga de datos bajo demanda |
| Vectorización | NumPy para operaciones |
| Sampling | Bootstrap con muestras limitadas |

### 7.2 Límites Recomendados

| Recurso | Límite Recomendado |
|---------|-------------------|
| Filas de datos | < 100,000 |
| Ciudades | < 50 |
| Bootstrap iterations | 500-1000 |
| Test duration | ≤ 90 días |

---

## 8. Logging y Monitoreo

### 8.1 Sistema de Logs

```python
# Ubicación: logs/geolift_YYYYMMDD.log
# Formato: TIMESTAMP | LEVEL | MODULE | MESSAGE

# Niveles disponibles:
- DEBUG: Información detallada
- INFO: Operaciones normales
- WARNING: Situaciones anómalas
- ERROR: Errores recuperables
- CRITICAL: Errores fatales
```

### 8.2 Métricas Clave

- Tiempo de cálculo de poder
- Errores de validación
- Exports generados
- Sesiones de usuario

---

## 9. Despliegue

### 9.1 Local

```bash
cd "GeoLift Test Pre Set Calculator"
pip install -r requirements.txt
streamlit run app.py --server.headless true
```

### 9.2 Streamlit Cloud

1. Subir repositorio a GitHub
2. Conectar con Streamlit Cloud
3. Configurar `requirements.txt`
4. Deploy automático

### 9.3 Docker (Opcional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.headless", "true"]
```

---

## 10. Testing

### 10.1 Tests Ejecutados

| Categoría | Tests | Estado |
|-----------|-------|--------|
| Imports | 8 | ✅ |
| Dependencias | 8 | ✅ |
| Validación | 9 | ✅ |
| Power Analysis | 14 | ✅ |
| Post-Test | 8 | ✅ |
| Visualizaciones | 4 | ✅ |
| Utilidades | 3 | ✅ |
| Edge Cases | 7 | ✅ |
| Logging | 1 | ✅ |
| **TOTAL** | **67** | **100%** |

---

## 11. Mantenimiento

### 11.1 Actualizaciones Recomendadas

- Verificar dependencias mensualmente
- Revisar logs semanalmente
- Backup de histórico quincenal
- Update de FAQ según feedback

### 11.2 Troubleshooting Común

| Problema | Solución |
|----------|----------|
| Error de import | `pip install -r requirements.txt` |
| Fechas no parseadas | Verificar formato (YYYY-MM-DD preferido) |
| Poder siempre 100% | Revisar variabilidad de datos |
| PDF vacío | Instalar `pip install reportlab` |

---

## 12. Contacto y Soporte

**Equipo:** AB InBev Marketing Intelligence  
**Versión:** 2.2.0  
**Última actualización:** Marzo 2026

---

*Documento generado automáticamente - GeoLift Calculator v2.2.0*
