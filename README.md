# Construcción de Recursos Léxicos para Quechua
## Trabajo de Fin de Unidad - Procesamiento de Lenguaje Natural

---

## 📋 Descripción del Proyecto

Este proyecto tiene como objetivo extraer, estructurar y enriquecer un diccionario bilingüe Quechua-Español disponible en formato PDF, transformándolo en un corpus léxico machine-readable que sirva como base para aplicaciones de Procesamiento de Lenguaje Natural (PLN) en quechua.

### Contexto
El quechua es una lengua indígena de los Andes centrales, hablada por millones de personas en Perú, Bolivia, Ecuador, Colombia, Argentina y Chile. A pesar de su vitalidad, carece de recursos computacionales adecuados para el PLN.

---

## 🎯 Objetivos

### Objetivo General
Desarrollar un sistema automatizado para extraer y estructurar información léxica de un diccionario PDF bilingüe, creando recursos digitales consultables y procesables.

### Objetivos Específicos
1. Extraer texto crudo del diccionario PDF preservando estructura básica
2. Separar y procesar las secciones Quechua-Español y Español-Quechua
3. Identificar y extraer metadatos (abreviaturas gramaticales, semánticas y dialectales)
4. Desarrollar parsers para estructurar entradas individuales del diccionario
5. Generar datasets estructurados en formato JSON
6. Crear una librería Python para consulta y manipulación de los datos
7. Validar la calidad y completitud de la extracción

---

## 🔧 Metodología

### Enfoque Técnico
- **Extracción**: Uso de librerías Python (PyMuPDF/pdfplumber) para procesamiento de PDF
- **Parsing**: Desarrollo de expresiones regulares para identificar patrones estructurales
- **Estructuración**: Conversión a formatos JSON para facilitar consulta y procesamiento
- **Validación**: Testing manual y automatizado de la calidad de extracción

### Estrategia de Colaboración
- **Desarrollo distribuido**: GitHub como repositorio central
- **Integración final**: Google Colab para entregable final
- **Comunicación**: Daily standups y revisiones de integración

---

## 👥 División de Roles y Responsabilidades

### 👨‍💻 **Rol 1: Data Engineer (Especialista en Extracción)**
**Responsable:** [Nombre]

**Tareas principales:**
- Extracción de texto crudo del PDF
- Identificación de estructura del documento
- Separación de secciones Quechua-Español y Español-Quechua
- Extracción de metadatos y abreviaturas

**Entregables:**
- `diccionario_raw.txt`
- Scripts de extracción (`pdf_extractor.py`)
- Documentación de patrones encontrados
- Mapeo de abreviaturas extraídas

### 🧠 **Rol 2: NLP Engineer (Especialista en Parsing)**
**Responsable:** [Nombre]

**Tareas principales:**
- Análisis de patrones de formato en entradas
- Desarrollo de expresiones regulares para parsing
- Implementación de parsers para ambas secciones
- Validación de extracción de campos

**Entregables:**
- Parsers modulares (`quechua_parser.py`, `spanish_parser.py`)
- Biblioteca de patrones regex (`patterns.py`)
- Scripts de validación
- Documentación de reglas de parsing

### ⚙️ **Rol 3: Software Engineer (Especialista en API/Librería)**
**Responsable:** [Nombre]

**Tareas principales:**
- Generación de archivos JSON estructurados
- Desarrollo de librería de utilidades
- Implementación de funciones de búsqueda
- Integración final y testing

**Entregables:**
- `quechua_espanol.json`, `espanol_quechua.json`
- `diccionario_utils.py`
- Suite de tests automatizados
- Notebook final de Colab

---

## 📅 Cronograma Detallado

### **Fase 1: Setup y Análisis (Días 1-2)**
- **Día 1:**
  - Configuración de repositorio GitHub
  - Setup de entornos de desarrollo
  - Análisis manual del PDF (muestra de 50 entradas)
  
- **Día 2:**
  - Definición de estructura de datos objetivo
  - Identificación de patrones preliminares
  - Diseño de arquitectura del sistema

### **Fase 2: Desarrollo Paralelo (Días 3-5)**
- **Data Engineer:**
  - Implementar extracción básica de PDF
  - Identificar límites de secciones
  - Extraer abreviaturas de páginas introductorias
  
- **NLP Engineer:**
  - Analizar patrones de formato en entradas
  - Desarrollar regex para campos principales
  - Implementar parser básico
  
- **Software Engineer:**
  - Diseñar esquema JSON
  - Estructurar librería base
  - Definir interfaces de funciones

### **Fase 3: Integración Primera (Días 6-8)**
- **Día 6:**
  - Combinar extracción con parsers
  - Primera generación de JSONs
  - Revisión cruzada de calidad
  
- **Días 7-8:**
  - Implementar funciones de búsqueda
  - Testing con dataset inicial
  - Refinamiento de parsers

### **Fase 4: Testing y Documentación (Días 9-10)**
- **Día 9:**
  - Validación con muestra manual (100+ entradas)
  - Testing de funciones con 10+ lemas
  - Documentación de código
  
- **Día 10:**
  - Preparación de notebook final
  - Redacción de informe PDF
  - Testing de integración completa

### **Fase 5: Entrega (Día 11)**
- **Día 11 (Viernes 26/09/2025):**
  - Integración final en Colab
  - Entrega de todos los componentes
  - Presentación de resultados

---

## 🏗️ Arquitectura del Sistema

### Estructura del Proyecto
```
quechua-lexicon/
├── 📁 data/
│   ├── 📁 raw/
│   │   ├── diccionario_original.pdf
│   │   └── diccionario_raw.txt
│   ├── 📁 processed/
│   │   ├── quechua_espanol.json
│   │   ├── espanol_quechua.json
│   │   └── abbreviations.json
│   └── 📁 samples/
│       └── manual_validation_sample.json
├── 📁 src/
│   ├── 📁 extraction/
│   │   ├── pdf_extractor.py
│   │   └── section_splitter.py
│   ├── 📁 parsing/
│   │   ├── quechua_parser.py
│   │   ├── spanish_parser.py
│   │   └── patterns.py
│   ├── 📁 utils/
│   │   ├── diccionario_utils.py
│   │   └── validation.py
│   └── 📁 models/
│       └── entry_models.py
├── 📁 tests/
│   ├── test_extraction.py
│   ├── test_parsing.py
│   └── test_utils.py
├── 📁 notebooks/
│   ├── exploratory_analysis.ipynb
│   └── final_colab_deliverable.ipynb
├── 📁 docs/
│   ├── project_plan.md
│   ├── patterns_documentation.md
│   └── api_reference.md
└── 📄 README.md
```

### Flujo de Datos
```
PDF → Extracción → Texto Crudo → Parsing → Estructuración → JSON → API/Consulta
```

---

## 🛠️ Tecnologías y Herramientas

### Librerías Python Principales
```python
# Extracción de PDF
PyMuPDF >= 1.23.0        # Extracción robusta de texto
pdfplumber >= 0.9.0      # Alternativa para análisis de layout

# Procesamiento de texto
re                       # Expresiones regulares
pandas >= 2.0.0         # Manipulación de datos
numpy >= 1.24.0         # Operaciones numéricas

# Serialización y persistencia
json                    # Formato de salida principal
pickle                  # Serialización de objetos Python

# Testing y validación
pytest >= 7.0.0         # Framework de testing
jsonschema >= 4.0.0     # Validación de esquemas JSON

# Documentación
jupyter >= 1.0.0        # Notebooks para análisis
```

### Herramientas de Desarrollo
- **Control de versiones:** Git + GitHub
- **Entorno de desarrollo:** VS Code / PyCharm
- **Colaboración:** Google Colab (entregable final)
- **Comunicación:** WhatsApp/Telegram + GitHub Issues

---

## 📊 Estructura de Datos

### Esquema de Entrada JSON
```json
{
  "lema": "achupalla",
  "categoria_gramatical": "s.",
  "campo_semantico": "Bot.",
  "definicion": "(Tillandsia struminea). Puya. De la familia de las bromeliáceas...",
  "variantes_dialectales": {
    "Pe.Aya.": "achupalla_aya",
    "Bol.": "qayara"
  },
  "sinonimos": ["qayara", "qheswa achupalla"],
  "ejemplos": [],
  "metadata": {
    "seccion": "quechua_espanol",
    "pagina_origen": 45,
    "confianza_extraccion": 0.95
  }
}
```

### API de Funciones Principales
```python
# Carga de datos
load_quechua_dictionary() -> Dict
load_spanish_dictionary() -> Dict

# Búsquedas básicas
buscar_por_quechua(lema: str) -> List[Dict]
buscar_por_espanol(lema: str) -> List[Dict]
obtener_variantes_dialectales(lema: str) -> List[str]

# Búsquedas por categorías
buscar_por_categoria_gramatical(categoria: str) -> List[Dict]
buscar_por_campo_semantico(campo: str) -> List[Dict]

# Utilidades estadísticas
contar_entradas() -> Dict[str, int]
listar_lemas() -> Dict[str, List[str]]
listar_categorias_gramaticales() -> List[str]
listar_campos_semanticos() -> List[str]
```

---

## ✅ Criterios de Validación

### Métricas de Calidad
1. **Completitud:** ≥95% de entradas extraídas correctamente
2. **Precisión:** ≥90% de campos identificados correctamente
3. **Cobertura de abreviaturas:** 100% de abreviaturas principales identificadas
4. **Consistencia:** Formato uniforme en todas las entradas

### Testing Strategy
- **Unit Tests:** Cada función individual
- **Integration Tests:** Flujo completo de procesamiento
- **Manual Validation:** Muestra aleatoria de 100+ entradas
- **Performance Tests:** Tiempo de respuesta de consultas

---

## 📦 Entregables Finales

### 1. **Código Fuente Completo**
- [ ] Repositorio GitHub con historial completo
- [ ] Código documentado y organizado
- [ ] Tests automatizados funcionando

### 2. **Datasets Estructurados**
- [ ] `quechua_espanol.json` - Sección Quechua→Español
- [ ] `espanol_quechua.json` - Sección Español→Quechua
- [ ] `abbreviations.json` - Metadatos de abreviaturas

### 3. **Librería Python**
- [ ] `diccionario_utils.py` - API completa de consulta
- [ ] Documentación de funciones
- [ ] Ejemplos de uso

### 4. **Notebook Final**
- [ ] Google Colab completamente ejecutado
- [ ] Celdas de documentación explicativas
- [ ] Demostraciones de funcionalidad

### 5. **Documentación**
- [ ] Informe PDF con proceso, resultados y conclusiones
- [ ] README.md con instrucciones de uso
- [ ] Documentación técnica de patrones

---

## 📈 Métricas de Éxito Esperadas

### Quantitative Goals
- **Entradas totales extraídas:** ~15,000-20,000 (estimación)
- **Categorías gramaticales identificadas:** ≥15
- **Campos semánticos identificados:** ≥20
- **Variantes dialectales mapeadas:** ≥19 (6 países + 13 regiones)
- **Tiempo de consulta promedio:** <100ms por búsqueda

### Qualitative Goals
- Sistema robusto y extensible
- Código limpio y mantenible
- Documentación clara y completa
- Funcionalidad demostrable end-to-end

---

## ⚠️ Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| PDF con formato inconsistente | Media | Alto | Análisis exhaustivo inicial + parsers flexibles |
| Patrones de entrada variables | Alta | Medio | Múltiples estrategias de parsing + validación manual |
| Abreviaturas ambiguas | Media | Medio | Extracción manual de tablas + validación cruzada |
| Problemas de integración | Baja | Alto | Reuniones de sincronización regulares |
| Timeframe ajustado | Media | Alto | Desarrollo paralelo + scope prioritizado |

---

## 📞 Información del Equipo

**Integrantes:** [Nombres a completar]
- **Data Engineer:** [Nombre] - [email]
- **NLP Engineer:** [Nombre] - [email]  
- **Software Engineer:** [Nombre] - [email]

**Fecha de inicio:** Lunes 16 de septiembre, 2025
**Fecha de entrega:** **Viernes 26 de septiembre, 2025 [IMPOSTERGABLE]**

---

*Cusco, septiembre de 2025*
*Universidad: [Nombre de la institución]*
*Curso: Procesamiento de Lenguaje Natural*