#!/usr/bin/env python3
"""
Parser para generar diccionarios estructurados en JSON a partir de archivos marcados.
Procesa tanto quechua-español como español-quechua y genera JSONs estructurados.

Uso:
    python dictionary_parser.py marcadore.txt --output quechua_espanol.json
    python dictionary_parser.py marcadores.txt --output espanol_quechua.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class DictionaryParser:
    def __init__(self, abbreviations_path: str = "abbreviations.json"):
        """Inicializa el parser con las abreviaciones."""
        self.load_abbreviations(abbreviations_path)

    def load_abbreviations(self, path: str):
        """Carga las abreviaciones desde el archivo JSON y prepara alias de búsqueda."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.countries: Dict[str, str] = data.get('countries', {})
                self.peru_regions: Dict[str, str] = data.get('peru_regions', {})
                self.abbreviations: Dict[str, str] = data.get('abbreviations', {})
        except FileNotFoundError:
            print(f"Warning: No se encontró {path}, usando abreviaciones por defecto")
            self.countries = {}
            self.peru_regions = {}
            self.abbreviations = {}

        # Conjuntos útiles (categorías gramaticales reconocidas)
        # Usar solo las abreviaturas canónicas en minúsculas para evitar confusión con "S." (Siglo)
        canonical_cats = {'s.', 'v.', 'adj.', 'adv.', 'interj.', 'alfab.'}
        self.grammatical_cats = {k for k in self.abbreviations.keys() if k in canonical_cats}
        # Etiquetas morfológicas que no son campos semánticos
        self.morphological_tags = {
            'm.', 'f.', 'pl.', 'sing.', 'imper.', 'negat.', 'diminut.', 'pref.', 'loc.', 'loc.adv.', 'por ext.', 'gen.', 'fam.',
            # Evitar confundir "S." (Siglo) con campo semántico o categoría
            'S.'
        }
        # Campos semánticos candidatos (todas las abreviaciones que no son categorías gramaticales ni morfológicas)
        self.semantic_candidates = [
            abbr for abbr in self.abbreviations.keys()
            if abbr not in self.grammatical_cats and abbr not in self.morphological_tags
        ]

        # Aliases para países y regiones: aceptar variantes sin punto, con ':' y nombres completos; y mapear a abreviatura canónica
        def base_key(k: str) -> str:
            return k.rstrip('.').lower()

        # Invertidos por nombre completo -> abreviatura
        self.country_full_to_abbr: Dict[str, str] = {v.lower(): k for k, v in self.countries.items()}
        self.peru_region_full_to_abbr: Dict[str, str] = {v.lower(): k for k, v in self.peru_regions.items()}

        # Mapas alias -> abrev. canónica (p.ej., 'arg' -> 'Arg.')
        self.country_alias_to_canonical: Dict[str, str] = {}
        for abbr, fullname in self.countries.items():
            b = base_key(abbr)
            self.country_alias_to_canonical[b] = abbr
            self.country_alias_to_canonical[b + ':'] = abbr
            self.country_alias_to_canonical[b + '.'] = abbr
            self.country_alias_to_canonical[b + '.:'] = abbr
            # nombres completos
            self.country_alias_to_canonical[fullname.lower()] = abbr
            self.country_alias_to_canonical[fullname.lower() + ':'] = abbr

        self.peru_region_alias_to_canonical: Dict[str, str] = {}
        for abbr, fullname in self.peru_regions.items():
            b = base_key(abbr)
            self.peru_region_alias_to_canonical[b] = abbr
            self.peru_region_alias_to_canonical[b + ':'] = abbr
            self.peru_region_alias_to_canonical[b + '.'] = abbr
            self.peru_region_alias_to_canonical[b + '.:'] = abbr
            # nombres completos
            self.peru_region_alias_to_canonical[fullname.lower()] = abbr
            self.peru_region_alias_to_canonical[fullname.lower() + ':'] = abbr

        # NUEVO: alias abreviados de regiones del Perú sin prefijo 'Pe.' (p.ej., 'Anc', 'Caj', 'Aya', 'S.Mar')
        self.peru_region_short_alias_to_canonical: Dict[str, str] = {}
        for abbr in self.peru_regions.keys():
            # Remover 'Pe.' del inicio y el punto final
            short = abbr
            if short.startswith('Pe.'):
                short = short[3:]
            short = short.rstrip('.')
            # Registrar alias en minúsculas
            k = short.lower()
            self.peru_region_short_alias_to_canonical[k] = abbr
            self.peru_region_short_alias_to_canonical[k + ':'] = abbr
            self.peru_region_short_alias_to_canonical[k + '.'] = abbr
            self.peru_region_short_alias_to_canonical[k + '.:'] = abbr

        # Construir una unión de etiquetas posibles para variantes dialectales
        label_parts: List[str] = []
        # Países abreviados (con o sin punto)
        for abbr in self.countries.keys():
            core = re.escape(abbr.rstrip('.'))
            label_parts.append(rf"{core}\.?")
        # Países por nombre completo (ELIMINADO para evitar falsos positivos como 'Perú: ...')
        # for name in self.countries.values():
        #     label_parts.append(re.escape(name))
        # Regiones Perú abreviadas (Pe.Xxx. -> aceptar con o sin punto final)
        for abbr in self.peru_regions.keys():
            core = re.escape(abbr.rstrip('.'))
            label_parts.append(rf"{core}\.?")
        # NUEVO: alias cortos de regiones (sin 'Pe.') con o sin punto final
        for abbr in self.peru_regions.keys():
            short = abbr[3:].rstrip('.') if abbr.startswith('Pe.') else abbr.rstrip('.')
            core = re.escape(short)
            label_parts.append(rf"{core}\.?")
        # Regiones Perú por nombre completo (ELIMINADO para evitar falsos positivos)
        # for name in self.peru_regions.values():
        #     label_parts.append(re.escape(name))
        # También aceptar variantes comunes cortas de países (ec, chil, col)
        for short in ['Arg', 'Bol', 'Ec', 'Chil', 'Col']:
            label_parts.append(rf"{short}\.?")

        # Unión completa (no-capturante)
        labels_union = "(?:" + "|".join(sorted(set(label_parts))) + ")"
        # Guardar para uso interno
        self._labels_union = labels_union
        # Par etiqueta(s):valor con lookahead hasta siguiente etiqueta(s)/||/fin
        # Acepta cadenas de etiquetas encadenadas tipo "Pe.Aya:Anc:Caj: valor"
        self.variants_group_rx = re.compile(
            rf"(?P<labels>(?:\b{labels_union}\b\s*:)+)\s*(?P<value>.+?)(?=(?:\s*(?:\b{labels_union}\b\s*:)+|\s*\|\||$))",
            re.IGNORECASE
        )

    def determine_dictionary_type(self, filename: str) -> str:
        """Determina si es quechua-español o español-quechua basado en el nombre del archivo."""
        filename = filename.lower()
        if 'marcadore.txt' in filename:
            return 'quechua_espanol'
        elif 'marcadores.txt' in filename:
            return 'espanol_quechua'
        else:
            return 'unknown'

    def extract_entries(self, content: str) -> List[str]:
        """Extrae las entradas individuales entre marcadores <begin> y <end>."""
        entries = []
        blocks = re.split(r'<begin>|<end>', content)
        for block in blocks:
            block = block.strip()
            if block and not block.startswith('<'):
                entries.append(block)
        return entries

    @staticmethod
    def _match_abbrev(text: str, abbr: str) -> Optional[re.Match]:
        """Busca una abreviatura tolerando punto opcional al final y delimitadores comunes.
        Devuelve el match o None. No es sensible a mayúsculas/minúsculas.
        """
        core = re.escape(abbr.rstrip('.'))
        pattern = rf"(?:(?<=^)|(?<=\s)|(?<=['\(\[]))({core}\.?)($|(?=\s|[,;:])|(?=[\)\]']))"
        return re.search(pattern, text, flags=re.IGNORECASE)

    def parse_grammatical_category(self, text: str) -> Tuple[Optional[str], str]:
        """Extrae la categoría gramatical del texto y retorna (categoría_abrev, texto_restante).
        Mantiene la cadena tal como aparece (incluye combinaciones "adj. y s.").
        """
        # Primero, detectar combinaciones tipo "adj. y s.", "s. y adj.", "v. y s.", "s. y v."
        combo_rx = re.compile(r"^\s*(adj\.\s*y\s*s\.|s\.\s*y\s*adj\.|v\.\s*y\s*s\.|s\.\s*y\s*v\.)", re.IGNORECASE)
        m_combo = combo_rx.match(text)
        if m_combo:
            cat_txt = m_combo.group(1)
            remaining = text[m_combo.end():].strip()
            remaining = re.sub(r"\s+", " ", remaining)
            return cat_txt, remaining
        # Luego, detectar una sola categoría conocida y devolverla como está en el texto
        for cat in sorted(self.grammatical_cats, key=len, reverse=True):
            m = self._match_abbrev(text, cat)
            if m:
                cat_txt = m.group(1)  # conserva la forma en el texto
                start, end = m.span(1)
                remaining = (text[:start] + text[end:]).strip()
                remaining = re.sub(r"\s+", " ", remaining)
                return cat_txt, remaining
        return None, text

    def parse_semantic_field(self, text: str) -> Tuple[Optional[str], str]:
        """Extrae el campo semántico (abreviado) y retorna (campo, texto_restante)."""
        if not self.semantic_candidates:
            return None, text
        earliest: Optional[Tuple[int, str, Tuple[int, int]]] = None  # (start_idx, abbr, span)
        for abbr in self.semantic_candidates:
            m = self._match_abbrev(text, abbr)
            if not m:
                continue
            start = m.start(1)
            if earliest is None or start < earliest[0]:
                earliest = (start, m.group(1), m.span(1))  # conservar forma en texto
        if earliest is None:
            return None, text
        _, abbr_txt, (s, e) = earliest
        new_text = (text[:s] + text[e:]).strip()
        new_text = re.sub(r"\s+", " ", new_text)
        return abbr_txt, new_text

    def parse_dialectal_variants(self, text: str) -> Tuple[Dict[str, str], str]:
        """Extrae variantes dialectales, incluyendo etiquetas encadenadas como "Pe.Aya:Anc:Caj: valor".
        Las claves se devuelven como abreviaturas canónicas (p.ej., "Arg.", "Pe.Aya.").
        """
        variants: Dict[str, str] = {}
        matches = list(self.variants_group_rx.finditer(text))
        # Función de normalización de etiqueta -> canónica
        def to_canonical(raw_label: str) -> str:
            key_norm = raw_label.rstrip('.').lower()
            canon: Optional[str] = None
            # Región Perú estilo Pe.Xxx
            if key_norm.startswith('pe.'):
                canon = self.peru_region_alias_to_canonical.get(key_norm) or \
                        self.peru_region_alias_to_canonical.get(key_norm + ':')
            # Región Perú por alias corto sin 'Pe.'
            if canon is None:
                canon = self.peru_region_short_alias_to_canonical.get(key_norm) or \
                        self.peru_region_short_alias_to_canonical.get(key_norm + ':') or \
                        self.peru_region_short_alias_to_canonical.get(key_norm + '.') or \
                        self.peru_region_short_alias_to_canonical.get(key_norm + '.:')
            # Región Perú por nombre completo
            if canon is None and key_norm in self.peru_region_full_to_abbr:
                canon = self.peru_region_full_to_abbr[key_norm]
            # País por abreviatura corta
            if canon is None:
                canon = self.country_alias_to_canonical.get(key_norm) or \
                        self.country_alias_to_canonical.get(key_norm + ':') or \
                        self.country_alias_to_canonical.get(key_norm + '.') or \
                        self.country_alias_to_canonical.get(key_norm + '.:')
            # País por nombre completo
            if canon is None and key_norm in self.country_full_to_abbr:
                canon = self.country_full_to_abbr[key_norm]
            # Si no se pudo normalizar, usar tal cual
            canon = canon or raw_label
            # Asegurar punto final si la canónica está catalogada
            if canon in self.countries or canon in self.peru_regions:
                if not canon.endswith('.'):
                    canon = canon + '.'
            return canon
        # Procesar matches
        for m in matches:
            labels_chunk = m.group('labels')
            value = m.group('value').strip()
            # Extraer etiquetas individuales de forma robusta: dividir por ':' y normalizar
            # Evita capturas solapadas como 'Pe.' + 'Aya' cuando la etiqueta real es 'Pe.Aya.'
            raw_tokens = [tok.strip() for tok in re.split(r":", labels_chunk) if tok.strip()]
            for raw_label in raw_tokens:
                canon = to_canonical(raw_label.rstrip(':').strip())
                variants[canon] = value
        # Eliminar del texto los segmentos de variantes ya capturados
        for m in reversed(matches):
            s, e = m.span()
            text = text[:s] + text[e:]
        text = re.sub(r"\s+", " ", text).strip()
        return variants, text

    def parse_synonyms(self, text: str) -> Tuple[List[str], str]:
        """Extrae sinónimos y retorna (lista_sinonimos, texto_restante). Acepta SINÓN:, SINON:, SINÓNIMOS:"""
        synonyms: List[str] = []
        pattern = r'(?:SIN[ÓO]N(?:IMOS)?\.?)\s*:\s*([^|]+?)(?=(?:\s+EJEM\s*:|\s+VARIEDADES\s*:|\s+[^:]+\s*:\s*|\s*\|\||$))'
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            syn_text = m.group(1).strip()
            parts = [s.strip().strip('.') for s in re.split(r"[;,/]", syn_text) if s.strip()]
            # Deduplicar preservando primer aparición (insensible a mayúsculas)
            seen = set()
            for s in parts:
                key = s.lower()
                if key and key not in seen:
                    seen.add(key)
                    synonyms.append(s)
            text = re.sub(re.escape(m.group(0)), '', text, flags=re.IGNORECASE).strip()
        return synonyms, text

    def parse_varieties(self, text: str) -> Tuple[List[str], str]:
        """Extrae VARIEDADES y retorna (lista_variedades, texto_restante)."""
        varieties: List[str] = []
        pattern = r'VARIEDADES\s*:\s*([^|]+?)(?=(?:\s+EJEM\s*:|\s+SIN[ÓO]N(?:IMOS)?\s*:|\s+[^:]+\s*:\s*|\s*\|\||$))'
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            var_text = m.group(1).strip()
            varieties = [v.strip().strip('.') for v in re.split(r",|;", var_text) if v.strip()]
            text = re.sub(re.escape(m.group(0)), '', text, flags=re.IGNORECASE).strip()
        return varieties, text

    def parse_examples(self, text: str) -> Tuple[List[str], str]:
        """Extrae ejemplos y retorna (lista_ejemplos, texto_restante)."""
        examples: List[str] = []
        pattern = r'EJEM\s*:\s*([^|]+?)(?=(?:\s+[^:]+\s*:\s*|\s*\|\||$))'
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            example_text = m.group(1).strip()
            if ';' in example_text:
                examples = [e.strip() for e in example_text.split(';') if e.strip()]
            else:
                examples = [example_text]
            text = re.sub(re.escape(m.group(0)), '', text, flags=re.IGNORECASE).strip()
        return examples, text

    def extract_lemma(self, text: str) -> str:
        """Extrae el lema (primera palabra) del texto."""
        match = re.match(r'^([A-Za-záéíóúñüÁÉÍÓÚÑÜ]+[!]?)', text.strip())
        if match:
            return match.group(1)
        return ""

    def clean_definition(self, text: str) -> str:
        """Limpia la definición removiendo elementos ya procesados, conservando '||' como separador de acepciones."""
        # Remover referencias "V. ..."
        text = re.sub(r"\bV\.\s*[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'\- ]*\.?", '', text)
        # Normalizar espacios alrededor de '||'
        text = re.sub(r'\s*\|\|\s*', ' || ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Normalizar punto inicial/final
        text = re.sub(r'^\.,?\s*', '', text)
        text = re.sub(r'\s*\.\s*$', '.', text)
        return text

    def parse_entry(self, entry_text: str) -> Dict[str, Any]:
        """Parsea una entrada individual y retorna un diccionario estructurado."""
        original_text = entry_text.strip()

        # Extraer lema
        lemma = self.extract_lemma(original_text)

        # Parsear componentes en orden (sinónimos y ejemplos primero para no perderlos en variantes)
        tmp_text = original_text
        synonyms, tmp_text = self.parse_synonyms(tmp_text)
        # Ya no extraemos VARIEDADES como campo separado; dejamos el texto en la definición
        examples, tmp_text = self.parse_examples(tmp_text)
        category, tmp_text = self.parse_grammatical_category(tmp_text)
        semantic_field, tmp_text = self.parse_semantic_field(tmp_text)
        # Detectar marcador de neologismo "NEOL."
        neol_present = False
        m_neol = re.search(r'\bNEOL\.?\b', tmp_text, flags=re.IGNORECASE)
        if m_neol:
            neol_present = True
            tmp_text = (tmp_text[:m_neol.start()] + tmp_text[m_neol.end():]).strip()

        variants, tmp_text = self.parse_dialectal_variants(tmp_text)

        # Lo que queda es la definición
        definition = self.clean_definition(tmp_text)

        # Remover el lema y categoría de la definición si están presentes al inicio
        if lemma:
            definition = re.sub(rf'^\s*{re.escape(lemma)}[!\.]?\s*', '', definition, flags=re.IGNORECASE)
        if category:
            cat_core = re.escape(category.rstrip('.'))
            definition = re.sub(rf'^\s*{cat_core}\.?(\s+|$)', ' ', definition, flags=re.IGNORECASE).strip()
        # Limpieza especial para entradas de letras: "A, a." al inicio
        if lemma and len(lemma.strip('!.')) == 1:
            definition = re.sub(r'^\s*,\s*[A-Za-z]\.?\s*', '', definition)
        definition = definition.strip()

        # Aplicar regla para NEOL.: si no hay campo semántico, usar "NEOL."; de lo contrario, anteponer a la definición
        if neol_present:
            if not semantic_field or semantic_field == 'null':
                semantic_field = 'NEOL.'
            else:
                definition = f"NEOL. {definition}" if not definition.startswith('NEOL.') else definition

        return {
            "lema": lemma,
            "categoria_gramatical": category or "null",
            "campo_semantico": semantic_field or "null",
            "definicion": definition,
            "variantes_dialectales": variants,
            "sinonimos": synonyms,
            "ejemplos": examples
        }

    def parse_file(self, input_path: str, output_path: str = None) -> List[Dict[str, Any]]:
        """Parsea un archivo completo y genera el JSON estructurado."""
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        dict_type = self.determine_dictionary_type(input_path)
        entries = self.extract_entries(content)

        parsed_entries: List[Dict[str, Any]] = []
        for entry in entries:
            if entry.strip():
                parsed_entry = self.parse_entry(entry)
                parsed_entries.append(parsed_entry)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_entries, f, ensure_ascii=False, indent=2)
            print(f"Diccionario {dict_type} guardado en: {output_path}")
            print(f"Total de entradas procesadas: {len(parsed_entries)}")

        return parsed_entries

def main():
    parser = argparse.ArgumentParser(description="Parser de diccionario marcado a JSON estructurado")
    parser.add_argument("input_file", help="Archivo de entrada (marcadore.txt o marcadores.txt)")
    parser.add_argument("--output", "-o", help="Archivo de salida JSON")
    parser.add_argument("--abbreviations", "-a", default="abbreviations.json",
                      help="Archivo de abreviaciones (default: abbreviations.json)")

    args = parser.parse_args()

    if not args.output:
        input_name = Path(args.input_file).stem
        if 'marcadore' in input_name.lower():
            args.output = "quechua_espanol.json"
        elif 'marcadores' in input_name.lower():
            args.output = "espanol_quechua.json"
        else:
            args.output = f"{input_name}_parsed.json"

    dict_parser = DictionaryParser(args.abbreviations)
    dict_parser.parse_file(args.input_file, args.output)

if __name__ == "__main__":
    main()