# 🚀 Guía de Usuario - GeoLift Calculator

## ¿Qué es GeoLift Calculator?

Una herramienta web para **diseñar y analizar tests de marketing geográficos**. Te ayuda a:

- 📊 **Pre-Test:** Planificar experimentos con poder estadístico adecuado
- 📈 **Post-Test:** Analizar resultados y medir el impacto incremental

---

## Acceso Rápido

🔗 **URL:** `http://localhost:8501` (local) o URL de producción

---

## Módulo 1: Pre-Test Calculator

### Paso 1: Cargar Datos

**¿Qué datos necesito?**

| Columna | Obligatoria | Ejemplo |
|---------|-------------|---------|
| `city` | ✅ Sí | Buenos_Aires |
| `date` | ✅ Sí | 2024-01-15 |
| `new_customers` | ✅ Sí | 150 |
| `country` | ⭕ Recomendada | Argentina |
| `media_spend` | ⭕ Recomendada | 5000 |
| `population` | ⭕ Recomendada | 3000000 |

**Formatos de fecha aceptados:**
- `2024-01-15` (YYYY-MM-DD) ✅ Preferido
- `15/01/2024` (DD/MM/YYYY)
- `15-01-2024` (DD-MM-YYYY)

**¿Cuántos días de datos?**
- Mínimo: 30 días
- Recomendado: 60+ días

**Opciones de carga:**
1. 📁 **Subir CSV** - Arrastra tu archivo
2. 🎯 **Demo Data** - Prueba con datos de ejemplo

---

### Paso 2: Contexto del Test

**Campos a completar:**

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Insights** | ¿De dónde viene la idea? | "TikTok conversión saturado, oportunidad en Jampp" |
| **Hipótesis** | ¿Qué esperas probar? | "Reasignar budget de TikTok a Jampp aumentará nuevos usuarios" |

💡 La herramienta valida si tu insight y tu hipótesis son coherentes.

---

### Paso 3: Seleccionar Ciudades

**Opciones:**

| Opción | Cuándo usar |
|--------|-------------|
| 🤖 **Recomendación Automática** | Primera vez, no estás seguro |
| ✋ **Selección Manual** | Sabes exactamente qué ciudades |
| 🔬 **Control Sintético** | No hay ciudad espejo perfecta |

**¿Qué es un Control Sintético?**

Cuando no existe una ciudad similar, la herramienta crea una "ciudad virtual" combinando varias ciudades con pesos optimizados.

> Ejemplo: Ciudad Sintética = 40% Córdoba + 35% Rosario + 25% Mendoza

---

### Paso 4: Configurar Test

**Parámetros clave:**

| Parámetro | Qué significa | Valor típico |
|-----------|---------------|--------------|
| **Lift Esperado** | % de incremento que esperas | 10-20% |
| **Duración** | Días del experimento | 21-42 días |
| **Confianza** | Nivel de certeza deseado | 95% |

---

### Paso 5: Análisis de Poder

**Métricas principales:**

| Métrica | ¿Qué significa? | ¿Qué valor buscar? |
|---------|-----------------|-------------------|
| **Poder Estadístico** | Probabilidad de detectar el efecto | ≥80% ✅ |
| **MDE** | Lift mínimo detectable | < Lift esperado |
| **Match Score** | Similitud entre ciudades | ≥60% |

**Interpretación del Poder:**

| Poder | Estado | Acción |
|-------|--------|--------|
| ≥80% | ✅ Excelente | Proceder con el test |
| 60-79% | ⚠️ Aceptable | Considerar más días |
| <60% | ❌ Bajo | Aumentar duración o ciudades |

---

### Paso 6: Exportar Plan

**Formatos disponibles:**
- 📄 **Excel** - Con múltiples hojas
- 📑 **PDF** - Reporte profesional

---

## Módulo 2: Post-Test Analyzer

### Paso 1: Cargar Resultados

**Formato del archivo:**

| Columna | Descripción |
|---------|-------------|
| `city` | Nombre de la ciudad |
| `date` | Fecha |
| `new_customers` | Nuevos clientes ese día |
| `group` | `treatment` o `control` |
| `period` | `pre` o `test` |

---

### Paso 2: Configurar Análisis

**Método de análisis:**

| Método | Cuándo usar |
|--------|-------------|
| **DiD** | Cuando tenés ciudades de control reales |
| **Synthetic** | Cuando usaste control sintético |

---

### Paso 3: Ver Resultados

**Métricas principales:**

| Métrica | Significado |
|---------|-------------|
| **Lift (%)** | Incremento atribuible a la campaña |
| **P-Value** | Significancia estadística (<0.05 = significativo) |
| **iROAS** | Retorno por peso invertido |
| **CI 95%** | Intervalo de confianza del lift |

**Interpretación de resultados:**

| P-Value | Significado |
|---------|-------------|
| <0.01 | ✅ Muy significativo |
| <0.05 | ✅ Significativo |
| 0.05-0.10 | ⚠️ Marginalmente significativo |
| >0.10 | ❌ No significativo |

---

## Glosario Rápido

| Término | Definición Simple |
|---------|-------------------|
| **GeoLift** | Test que compara ciudades con y sin campaña |
| **Tratamiento** | Ciudades donde se ejecuta la campaña |
| **Control** | Ciudades sin campaña (para comparar) |
| **DiD** | Método que compara cambios entre grupos |
| **Poder** | Probabilidad de detectar un efecto real |
| **MDE** | Efecto mínimo que podemos detectar |
| **Lift** | Incremento causado por la campaña |
| **P-Value** | ¿Qué tan probable es que sea azar? |
| **iROAS** | Retorno incremental por peso invertido |

---

## FAQ

### ¿Cuántas ciudades necesito?
- **Mínimo:** 3 (1 tratamiento + 2 control)
- **Recomendado:** 5+ para mayor robustez

### ¿Cuánto debe durar el test?
- **Mínimo:** 14 días
- **Recomendado:** 21-28 días
- **Máximo típico:** 42-56 días

### ¿Qué hago si el poder es bajo?
1. Aumentar duración del test
2. Agregar más ciudades
3. Aumentar el lift esperado (si es realista)

### ¿Cómo sé si el resultado es significativo?
- P-Value < 0.05 = estadísticamente significativo
- El intervalo de confianza no cruza el 0

### ¿Puedo guardar mis análisis?
Sí, la herramienta guarda automáticamente en el histórico. Podés comparar tests anteriores.

---

## Tips para Mejores Resultados

### ✅ Hacer

- Usar al menos 60 días de datos históricos
- Elegir ciudades con comportamiento similar
- Documentar insights e hipótesis
- Validar con placebo test

### ❌ Evitar

- Tests muy cortos (<14 días)
- Ciudades vecinas (spillover)
- Eventos especiales durante el test
- Ignorar el MDE

---

## Soporte

📧 **Contacto:** Marketing Intelligence Team  
📚 **Documentación completa:** Ver `TECHNICAL_DOCUMENTATION.md`

---

*Guía de Usuario v2.2.0 - GeoLift Calculator*
