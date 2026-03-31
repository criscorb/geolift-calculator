# 🎯 GeoLift Calculator

**Versión:** 2.2.0  
**Estado:** ✅ Producción

---

## ¿Qué es?

Una herramienta web para diseñar y analizar **tests de marketing geográficos (GeoLift)**. Permite a los marketing managers:

- 📊 **Pre-Test Calculator:** Planificar experimentos con poder estadístico adecuado
- 📈 **Post-Test Analyzer:** Analizar resultados y medir impacto incremental

---

## Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
streamlit run app.py --server.headless true
```

### 3. Abrir en el navegador

```
http://localhost:8501
```

---

## Estructura del Proyecto

```
├── app.py                    # Homepage
├── pages/                    # Módulos principales
│   ├── 1_📊_Pre_Test_Calculator.py
│   └── 2_📈_Post_Test_Analyzer.py
├── engine/                   # Motor de cálculos
├── templates/                # Plantillas CSV
├── docs/                     # Documentación
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── BITACORA.md
│   └── USER_GUIDE.md
└── requirements.txt
```

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Guía de usuario paso a paso |
| [TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md) | Documentación técnica completa |
| [BITACORA.md](docs/BITACORA.md) | Historial de desarrollo |

---

## Features Principales

### Pre-Test Calculator
- ✅ Recomendación automática de ciudades
- ✅ Cálculo de poder estadístico
- ✅ MDE (Minimum Detectable Effect)
- ✅ Control sintético
- ✅ Auto-selección de geos
- ✅ Budget allocator
- ✅ What-if simulator
- ✅ Bootstrap confidence intervals

### Post-Test Analyzer
- ✅ Diferencias en Diferencias (DiD)
- ✅ Control sintético
- ✅ Lift acumulado
- ✅ Placebo test
- ✅ ROI / iROAS calculator
- ✅ Insights automáticos

---

## Requisitos

- Python 3.12+
- Streamlit 1.28+
- Ver `requirements.txt` para lista completa

---

## Licencia

Uso interno.

---

*Marketing Intelligence - 2026*
