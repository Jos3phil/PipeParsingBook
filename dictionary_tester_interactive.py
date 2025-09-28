#!/usr/bin/env python3
'''
Entorno interactivo de pruebas para DictionaryParser.

Propósito
--------
Este módulo proporciona una clase (InteractiveDictionaryTester) y una función main()
que permiten ejecutar un conjunto de pruebas y verificaciones sobre dos ficheros
JSON de diccionarios bilingües (quechua <-> español). Está pensado para:
- Verificar manualmente entradas seleccionadas.
- Probar comportamientos del parser para lemas concretos.
- Analizar la calidad y cobertura de campos extraídos.
- Realizar búsquedas por patrón en diversos campos.

Uso
----
Ejecutar como script:

Al iniciarse intenta cargar dos ficheros en el directorio de trabajo:
- quechua_espanol.json
- espanol_quechua.json
Si no existen, la clase continúa pero con listas vacías y avisos por consola.

Estructura de datos esperada (formato JSON por entrada)
-------------------------------------------------------
Cada entrada del JSON debe ser un objeto/dict con, como mínimo, las siguientes claves:
- 'lema' (str) : lema de la entrada.
- 'categoria_gramatical' (str) : categoría gramatical o 'null'.
- 'campo_semantico' (str) : campo semántico o 'null'.
- 'definicion' (str) : texto de la definición.
- 'variantes_dialectales' (dict) : mapeo región -> variante (puede estar vacío).
- 'sinonimos' (list) : lista de sinónimos (puede estar vacía).
- 'ejemplos' (list) : lista de ejemplos de uso (puede estar vacía).

Comportamiento principal
-----------------------
Clase InteractiveDictionaryTester:
- __init__:
    - Inicializa un DictionaryParser (dependencia externa) y carga los JSON.
    - Imprime información sobre la carga de ficheros.
- load_data:
    - Intenta abrir y parsear los JSON con encoding 'utf-8'.
    - Si falta un fichero, crea la lista correspondiente vacía e informa.
- test_specific_lemmas:
    - Ejecuta una batería de comprobaciones sobre lemas predefinidos.
    - Para cada caso busca coincidencias exactas (case-insensitive) y muestra:
      lema, categoría, campo semántico, inicio de la definición.
    - Valida si coinciden valores esperados para categoría, campo semántico,
      presencia de variantes y sinónimos, emitiendo mensajes (✅/❌/⚠️).
- manual_entry_verification:
    - Muestra una muestra aleatoria (hasta 5) de entradas de cada diccionario.
    - Utiliza display_entry_details para mostrar campos completos para revisión manual.
- display_entry_details:
    - Formatea y muestra en consola los campos detallados de una entrada.
- analyze_extraction_quality:
    - Calcula estadísticas de cobertura sobre:
      categoría gramatical, campo semántico, variantes dialectales, sinónimos, ejemplos.
    - Informa porcentajes, y busca entradas problemáticas (lema o definición vacíos,
      ausencia simultánea de categoría y campo semántico) en una muestra de hasta 100 entradas.
- search_by_pattern:
    - Busca un patrón (substring, case-insensitive) en un campo dado de todas las entradas
      de los dos diccionarios y muestra hasta 3 coincidencias por diccionario.
- run_all_tests:
    - Orquesta la ejecución de las pruebas: lemas específicos, verificación manual,
      análisis de calidad y varias búsquedas por patrón.
- main:
    - Instancia InteractiveDictionaryTester y lanza run_all_tests cuando el módulo se
      ejecuta como script principal.

Salida y mensajes
-----------------
- El módulo imprime mensajes en consola indicando:
  - Éxito/fracaso en la carga de ficheros.
  - Resultado de cada prueba (coincidencias, validaciones, estadísticas).
  - Entradas problemáticas encontradas en la muestra.
- Usa emojis y símbolos (p. ej. ✅, ❌, ⚠️) para facilitar la lectura humana.

Consideraciones y limitaciones
------------------------------
- No realiza modificaciones sobre los ficheros JSON; solo lectura.
- Las comprobaciones de lemas son exactas (comparación de igualdad tras .lower()).
- Para el análisis solo revisa hasta las primeras 100 entradas para detectar problemas,
  lo cual está pensado como muestra rápida, no auditoría exhaustiva.
- Se asume que cada entrada contiene las claves esperadas; si faltan, se pueden
  producir KeyError en tiempo de ejecución. Puede ampliarse con validación previa.
- El módulo depende de una clase external llamada DictionaryParser importada desde
  dictionary_parser (no se usa explícitamente en las pruebas actuales, pero se
  instancia por compatibilidad/expansión).

Ejemplo de ejecución
--------------------
Al ejecutar, se mostrarán:
- Mensajes de carga de archivos y conteo de entradas.
- Resultados de las pruebas de lemas (encontrado/esperado).
- Muestras aleatorias detalladas de entradas.
- Estadísticas de cobertura por campo y lista corta de entradas problemáticas.
- Resultados de búsquedas por patrón en campos seleccionados.

Extensiones recomendadas
------------------------
- Añadir validación robusta del esquema de cada entrada y manejo de claves faltantes.
- Permitir modo interactivo (pedir lemas/patrones al usuario) en lugar de únicamente
  pruebas preconfiguradas.
- Volcar resultados y estadísticas a un fichero CSV/JSON para análisis posterior.
- Integrar directamente con DictionaryParser para generar entradas desde fuentes
  crudas y comparar antes/después de la normalización.
  '''
"""
Entorno de pruebas interactivo para el DictionaryParser.

Este script permite probar específicamente los elementos requeridos:
- Verificación manual de entradas
- Pruebas de funciones con lemas específicos
- Validación detallada de categorías, campos semánticos, variantes y sinónimos

Uso:
    python dictionary_tester_interactive.py
"""

import json
import re
from typing import Dict, List, Any, Optional
from dictionary_parser import DictionaryParser

class InteractiveDictionaryTester:
    def __init__(self):
        self.parser = DictionaryParser()
        print("🔧 Inicializando tester...")
        self.load_data()

    def load_data(self):
        """Carga los datos JSON del diccionario."""
        try:
            with open("quechua_espanol.json", 'r', encoding='utf-8') as f:
                self.quechua_espanol = json.load(f)
            print(f"✅ Cargado quechua_espanol.json: {len(self.quechua_espanol)} entradas")
        except FileNotFoundError:
            self.quechua_espanol = []
            print("❌ No se encontró quechua_espanol.json")

        try:
            with open("espanol_quechua.json", 'r', encoding='utf-8') as f:
                self.espanol_quechua = json.load(f)
            print(f"✅ Cargado espanol_quechua.json: {len(self.espanol_quechua)} entradas")
        except FileNotFoundError:
            self.espanol_quechua = []
            print("❌ No se encontró espanol_quechua.json")

    def test_specific_lemmas(self):
        """Prueba funciones del parser con lemas específicos diseñados."""
        print("\n" + "="*60)
        print("PRUEBA DE LEMAS ESPECÍFICOS")
        print("="*60)

        # Lemas específicos para probar diferentes características
        test_cases = [
            # Lemas con categorías gramaticales variadas
            {"lemma": "Runa", "expected_cat": "s.", "dict": "quechua"},
            {"lemma": "Hatun", "expected_cat": "adj.", "dict": "quechua"},
            {"lemma": "Puriy", "expected_cat": "v.", "dict": "quechua"},
            {"lemma": "agua", "expected_cat": "s.", "dict": "espanol"},
            {"lemma": "comer", "expected_cat": "v.", "dict": "espanol"},

            # Lemas con campos semánticos específicos
            {"lemma": "Inti", "expected_semantic": "Astron.", "dict": "quechua"},
            {"lemma": "tiempo", "expected_semantic": "Astron.", "dict": "espanol"},

            # Lemas que deberían tener variantes dialectales
            {"lemma": "achacha", "should_have_variants": True, "dict": "quechua"},
            {"lemma": "achallqo", "should_have_variants": True, "dict": "quechua"},

            # Lemas que deberían tener sinónimos
            {"lemma": "achacha", "should_have_synonyms": True, "dict": "quechua"},
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Prueba {i}: {test_case['lemma']} ---")

            # Seleccionar diccionario
            data = self.quechua_espanol if test_case['dict'] == 'quechua' else self.espanol_quechua
            dict_name = "Quechua-Español" if test_case['dict'] == 'quechua' else "Español-Quechua"

            # Buscar entrada
            matches = [entry for entry in data if entry["lema"].lower() == test_case['lemma'].lower()]

            if not matches:
                print(f"❌ Lema '{test_case['lemma']}' no encontrado en {dict_name}")
                continue

            entry = matches[0]
            print(f"✅ Encontrado en {dict_name}")
            print(f"   Lema: {entry['lema']}")
            print(f"   Categoría: {entry['categoria_gramatical']}")
            print(f"   Campo semántico: {entry['campo_semantico']}")
            print(f"   Definición: {entry['definicion'][:80]}...")

            # Validar categoría gramatical esperada
            if 'expected_cat' in test_case:
                if entry['categoria_gramatical'] == test_case['expected_cat']:
                    print(f"   ✅ Categoría gramatical correcta: {test_case['expected_cat']}")
                else:
                    print(f"   ❌ Categoría esperada: {test_case['expected_cat']}, obtenida: {entry['categoria_gramatical']}")

            # Validar campo semántico esperado
            if 'expected_semantic' in test_case:
                if entry['campo_semantico'] == test_case['expected_semantic']:
                    print(f"   ✅ Campo semántico correcto: {test_case['expected_semantic']}")
                else:
                    print(f"   ⚠️  Campo esperado: {test_case['expected_semantic']}, obtenido: {entry['campo_semantico']}")

            # Validar presencia de variantes dialectales
            if test_case.get('should_have_variants'):
                if entry['variantes_dialectales']:
                    print(f"   ✅ Tiene variantes dialectales: {entry['variantes_dialectales']}")
                else:
                    print(f"   ❌ Se esperaban variantes dialectales pero no se encontraron")

            # Validar presencia de sinónimos
            if test_case.get('should_have_synonyms'):
                if entry['sinonimos']:
                    print(f"   ✅ Tiene sinónimos: {entry['sinonimos']}")
                else:
                    print(f"   ❌ Se esperaban sinónimos pero no se encontraron")

    def manual_entry_verification(self):
        """Permite verificación manual de entradas específicas."""
        print("\n" + "="*60)
        print("VERIFICACIÓN MANUAL DE ENTRADAS")
        print("="*60)

        # Mostrar algunas entradas aleatorias para verificación manual
        import random

        print("🔍 Muestra aleatoria de entradas para verificación manual:")

        # Seleccionar 5 entradas aleatorias de cada diccionario
        sample_quechua = random.sample(self.quechua_espanol, min(5, len(self.quechua_espanol)))
        sample_espanol = random.sample(self.espanol_quechua, min(5, len(self.espanol_quechua)))

        print("\n--- Muestra Quechua-Español ---")
        for i, entry in enumerate(sample_quechua, 1):
            print(f"\nEntrada {i}:")
            self.display_entry_details(entry)

        print("\n--- Muestra Español-Quechua ---")
        for i, entry in enumerate(sample_espanol, 1):
            print(f"\nEntrada {i}:")
            self.display_entry_details(entry)

    def display_entry_details(self, entry: Dict[str, Any]):
        """Muestra los detalles de una entrada de forma estructurada."""
        print(f"   Lema: '{entry['lema']}'")
        print(f"   Categoría gramatical: '{entry['categoria_gramatical']}'")
        print(f"   Campo semántico: '{entry['campo_semantico']}'")
        print(f"   Definición: '{entry['definicion']}'")

        if entry['variantes_dialectales']:
            print(f"   Variantes dialectales:")
            for region, variant in entry['variantes_dialectales'].items():
                print(f"      {region}: {variant}")
        else:
            print(f"   Variantes dialectales: Ninguna")

        if entry['sinonimos']:
            print(f"   Sinónimos: {entry['sinonimos']}")
        else:
            print(f"   Sinónimos: Ninguno")

        if entry['ejemplos']:
            print(f"   Ejemplos: {entry['ejemplos']}")
        else:
            print(f"   Ejemplos: Ninguno")

    def analyze_extraction_quality(self):
        """Analiza la calidad de la extracción de diferentes campos."""
        print("\n" + "="*60)
        print("ANÁLISIS DE CALIDAD DE EXTRACCIÓN")
        print("="*60)

        datasets = {
            "Quechua-Español": self.quechua_espanol,
            "Español-Quechua": self.espanol_quechua
        }

        for dict_name, data in datasets.items():
            print(f"\n--- Análisis de {dict_name} ---")

            # Estadísticas de categorías gramaticales
            total_entries = len(data)
            cats_with_content = sum(1 for entry in data if entry['categoria_gramatical'] != 'null')
            cat_percentage = (cats_with_content / total_entries) * 100
            print(f"Entradas con categoría gramatical: {cats_with_content}/{total_entries} ({cat_percentage:.1f}%)")

            # Estadísticas de campos semánticos
            sem_with_content = sum(1 for entry in data if entry['campo_semantico'] != 'null')
            sem_percentage = (sem_with_content / total_entries) * 100
            print(f"Entradas con campo semántico: {sem_with_content}/{total_entries} ({sem_percentage:.1f}%)")

            # Estadísticas de variantes dialectales
            var_with_content = sum(1 for entry in data if entry['variantes_dialectales'])
            var_percentage = (var_with_content / total_entries) * 100
            print(f"Entradas con variantes dialectales: {var_with_content}/{total_entries} ({var_percentage:.1f}%)")

            # Estadísticas de sinónimos
            syn_with_content = sum(1 for entry in data if entry['sinonimos'])
            syn_percentage = (syn_with_content / total_entries) * 100
            print(f"Entradas con sinónimos: {syn_with_content}/{total_entries} ({syn_percentage:.1f}%)")

            # Estadísticas de ejemplos
            ex_with_content = sum(1 for entry in data if entry['ejemplos'])
            ex_percentage = (ex_with_content / total_entries) * 100
            print(f"Entradas con ejemplos: {ex_with_content}/{total_entries} ({ex_percentage:.1f}%)")

            # Buscar entradas problemáticas
            problematic = []
            for entry in data[:100]:  # Solo revisar las primeras 100
                issues = []
                if not entry['lema'].strip():
                    issues.append("lema vacío")
                if not entry['definicion'].strip():
                    issues.append("definición vacía")
                if entry['categoria_gramatical'] == 'null' and entry['campo_semantico'] == 'null':
                    issues.append("sin categoría ni campo semántico")

                if issues:
                    problematic.append((entry['lema'], issues))

            if problematic:
                print(f"\nEntradas problemáticas encontradas (muestra de 100):")
                for lemma, issues in problematic[:5]:  # Mostrar solo las primeras 5
                    print(f"   '{lemma}': {', '.join(issues)}")
            else:
                print(f"\n✅ No se encontraron entradas problemáticas en la muestra")

    def search_by_pattern(self, pattern: str, field: str = "lema"):
        """Busca entradas que coincidan con un patrón."""
        print(f"\n🔍 Buscando patrón '{pattern}' en campo '{field}':")

        datasets = {
            "Quechua-Español": self.quechua_espanol,
            "Español-Quechua": self.espanol_quechua
        }

        for dict_name, data in datasets.items():
            matches = []
            for entry in data:
                if field in entry and pattern.lower() in str(entry[field]).lower():
                    matches.append(entry)

            print(f"\n{dict_name}: {len(matches)} coincidencias")
            for match in matches[:3]:  # Mostrar solo las primeras 3
                print(f"   {match['lema']}: {match[field]}")

    def run_all_tests(self):
        """Ejecuta todas las pruebas del entorno interactivo."""
        print("🧪 ENTORNO DE PRUEBAS INTERACTIVO")
        print("="*60)

        # Prueba 1: Verificación con lemas específicos
        self.test_specific_lemmas()

        # Prueba 2: Verificación manual
        self.manual_entry_verification()

        # Prueba 3: Análisis de calidad
        self.analyze_extraction_quality()

        # Pruebas adicionales de búsqueda
        print("\n" + "="*60)
        print("PRUEBAS DE BÚSQUEDA ADICIONALES")
        print("="*60)

        # Buscar entradas con características específicas
        self.search_by_pattern("NEOL", "campo_semantico")
        self.search_by_pattern("Pe.Aya", "variantes_dialectales")
        self.search_by_pattern("Bot.", "campo_semantico")

        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)

def main():
    """Función principal."""
    tester = InteractiveDictionaryTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()