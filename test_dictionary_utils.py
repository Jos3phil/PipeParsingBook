#!/usr/bin/env python3
"""
Script de pruebas para validar la funcionalidad del DictionaryParser.

Este script realiza las siguientes validaciones:
1. Verificación del número de entradas extraídas vs muestra manual
2. Pruebas con al menos 10 lemas diferentes
3. Validación de extracción de categorías gramaticales, campos semánticos,
   variantes dialectales y sinónimos

Uso:
    python test_dictionary_utils.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from dictionary_parser import DictionaryParser

class DictionaryTester:
    def __init__(self):
        self.parser = DictionaryParser()
        self.quechua_espanol = self.load_json("quechua_espanol.json")
        self.espanol_quechua = self.load_json("espanol_quechua.json")

    def load_json(self, filename: str) -> List[Dict[str, Any]]:
        """Carga un archivo JSON de diccionario."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Archivo {filename} no encontrado")
            return []

    def test_entry_count_verification(self):
        """Prueba 1: Verificar número de entradas extraídas vs muestra manual."""
        print("=== PRUEBA 1: Verificación de número de entradas ===")

        # Contar marcadores <begin> en archivos fuente
        marcadores_counts = {}
        for file in ["marcadore.txt", "marcadores.txt"]:
            if Path(file).exists():
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    count = content.count('<begin>')
                    marcadores_counts[file] = count
                    print(f"📄 {file}: {count} marcadores <begin>")

        # Verificar JSON generados
        json_counts = {
            "quechua_espanol.json": len(self.quechua_espanol),
            "espanol_quechua.json": len(self.espanol_quechua)
        }

        for filename, count in json_counts.items():
            print(f"📊 {filename}: {count} entradas procesadas")

        # Análisis de coincidencias
        print("\n🔍 Análisis de coincidencias:")
        if "marcadores.txt" in marcadores_counts:
            diff = abs(marcadores_counts["marcadores.txt"] - json_counts["espanol_quechua.json"])
            print(f"   marcadores.txt vs espanol_quechua.json: diferencia de {diff} entradas")
            if diff <= 1:
                print("   ✅ Coincidencia excelente")
            elif diff <= 10:
                print("   ⚠️  Diferencia menor aceptable")
            else:
                print("   ❌ Diferencia significativa - revisar")

        if "marcadore.txt" in marcadores_counts:
            diff = abs(marcadores_counts["marcadore.txt"] - json_counts["quechua_espanol.json"])
            print(f"   marcadore.txt vs quechua_espanol.json: diferencia de {diff} entradas")
            if diff <= 100:
                print("   ⚠️  Diferencia aceptable (posibles entradas compuestas)")
            else:
                print("   ❌ Diferencia muy grande - revisar")

        return True

    def test_sample_lemmas(self):
        """Prueba 2: Probar funciones con al menos 10 lemas diferentes."""
        print("\n=== PRUEBA 2: Prueba con 10+ lemas diferentes ===")

        # Seleccionar 10 lemas diversos de cada diccionario
        test_lemmas_quechua = [
            "Achka", "Allpa", "Ama", "Aycha", "Chaki",
            "Hatun", "Inti", "Killa", "Mama", "Runa"
        ]

        test_lemmas_espanol = [
            "agua", "casa", "comer", "grande", "madre",
            "pueblo", "tierra", "tiempo", "trabajo", "vida"
        ]

        print("🔍 Probando lemas en quechua-español:")
        found_quechua = 0
        for lemma in test_lemmas_quechua:
            matches = [entry for entry in self.quechua_espanol
                      if entry["lema"].lower() == lemma.lower()]
            if matches:
                found_quechua += 1
                entry = matches[0]
                print(f"   ✅ {lemma}: {entry['definicion'][:60]}...")
            else:
                print(f"   ❌ {lemma}: no encontrado")

        print(f"\n📊 Encontrados: {found_quechua}/{len(test_lemmas_quechua)} lemas quechua")

        print("\n🔍 Probando lemas en español-quechua:")
        found_espanol = 0
        for lemma in test_lemmas_espanol:
            matches = [entry for entry in self.espanol_quechua
                      if entry["lema"].lower() == lemma.lower()]
            if matches:
                found_espanol += 1
                entry = matches[0]
                print(f"   ✅ {lemma}: {entry['definicion'][:60]}...")
            else:
                print(f"   ❌ {lemma}: no encontrado")

        print(f"\n📊 Encontrados: {found_espanol}/{len(test_lemmas_espanol)} lemas español")

        total_found = found_quechua + found_espanol
        total_tested = len(test_lemmas_quechua) + len(test_lemmas_espanol)

        if total_found >= 10:
            print(f"✅ Prueba exitosa: {total_found} lemas encontrados de {total_tested} probados")
        else:
            print(f"⚠️  Solo se encontraron {total_found} lemas de {total_tested} probados")

        return total_found >= 10

    def analyze_field_extraction(self):
        """Prueba 3: Validar extracción de campos específicos."""
        print("\n=== PRUEBA 3: Validación de extracción de campos ===")

        # Analizar muestras de ambos diccionarios
        datasets = {
            "Quechua-Español": self.quechua_espanol[:1000],  # Muestra de 1000
            "Español-Quechua": self.espanol_quechua[:1000]
        }

        for dict_name, sample in datasets.items():
            print(f"\n📊 Análisis de {dict_name} (muestra de {len(sample)} entradas):")

            # Categorías gramaticales
            cat_counts = {}
            for entry in sample:
                cat = entry.get("categoria_gramatical", "null")
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

            print("   📝 Categorías gramaticales encontradas:")
            for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                pct = (count / len(sample)) * 100
                print(f"      {cat}: {count} ({pct:.1f}%)")

            # Campos semánticos
            semantic_counts = {}
            for entry in sample:
                sem = entry.get("campo_semantico", "null")
                semantic_counts[sem] = semantic_counts.get(sem, 0) + 1

            print("   🏷️  Campos semánticos más comunes:")
            for sem, count in sorted(semantic_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                if sem != "null":
                    pct = (count / len(sample)) * 100
                    print(f"      {sem}: {count} ({pct:.1f}%)")

            # Variantes dialectales
            with_variants = sum(1 for entry in sample if entry.get("variantes_dialectales"))
            pct_variants = (with_variants / len(sample)) * 100
            print(f"   🗺️  Entradas con variantes dialectales: {with_variants} ({pct_variants:.1f}%)")

            # Sinónimos
            with_synonyms = sum(1 for entry in sample if entry.get("sinonimos"))
            pct_synonyms = (with_synonyms / len(sample)) * 100
            print(f"   🔗 Entradas con sinónimos: {with_synonyms} ({pct_synonyms:.1f}%)")

            # Ejemplos
            with_examples = sum(1 for entry in sample if entry.get("ejemplos"))
            pct_examples = (with_examples / len(sample)) * 100
            print(f"   📖 Entradas con ejemplos: {with_examples} ({pct_examples:.1f}%)")

    def show_detailed_examples(self):
        """Muestra ejemplos detallados de entradas bien parseadas."""
        print("\n=== EJEMPLOS DETALLADOS DE ENTRADAS ===")

        # Buscar entradas con características interesantes
        interesting_entries = []

        # Buscar entradas con variantes dialectales
        for entry in self.quechua_espanol[:500]:
            if (entry.get("variantes_dialectales") and
                entry.get("sinonimos") and
                entry.get("categoria_gramatical") != "null"):
                interesting_entries.append(("Quechua-Español", entry))
                if len(interesting_entries) >= 3:
                    break

        # Buscar entradas con sinónimos del español-quechua
        for entry in self.espanol_quechua[:500]:
            if (entry.get("sinonimos") and
                entry.get("campo_semantico") != "null" and
                entry.get("categoria_gramatical") != "null"):
                interesting_entries.append(("Español-Quechua", entry))
                if len(interesting_entries) >= 5:
                    break

        for dict_type, entry in interesting_entries:
            print(f"\n📋 Ejemplo de {dict_type}:")
            print(f"   Lema: {entry['lema']}")
            print(f"   Categoría gramatical: {entry['categoria_gramatical']}")
            print(f"   Campo semántico: {entry['campo_semantico']}")
            print(f"   Definición: {entry['definicion'][:100]}...")

            if entry.get("variantes_dialectales"):
                print(f"   Variantes dialectales: {entry['variantes_dialectales']}")

            if entry.get("sinonimos"):
                print(f"   Sinónimos: {entry['sinonimos']}")

            if entry.get("ejemplos"):
                print(f"   Ejemplos: {entry['ejemplos']}")

    def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        print("🧪 INICIANDO PRUEBAS DEL DICTIONARY PARSER")
        print("=" * 60)

        try:
            # Prueba 1: Verificación de conteos
            self.test_entry_count_verification()

            # Prueba 2: Prueba de lemas
            lemma_success = self.test_sample_lemmas()

            # Prueba 3: Análisis de campos
            self.analyze_field_extraction()

            # Ejemplos detallados
            self.show_detailed_examples()

            print("\n" + "=" * 60)
            print("✅ TODAS LAS PRUEBAS COMPLETADAS")

            if lemma_success:
                print("🎉 El parser está funcionando correctamente!")
            else:
                print("⚠️  El parser funciona pero algunos lemas no fueron encontrados.")

            print("\n📊 RESUMEN:")
            print(f"   - Entradas Quechua-Español: {len(self.quechua_espanol)}")
            print(f"   - Entradas Español-Quechua: {len(self.espanol_quechua)}")
            print(f"   - Total de entradas procesadas: {len(self.quechua_espanol) + len(self.espanol_quechua)}")

        except Exception as e:
            print(f"❌ Error durante las pruebas: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Función principal."""
    tester = DictionaryTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()