# filepath: /media/kingston-apps/PNL/parse_metadata.py
"""
Parsea metadatos (países andinos, regiones lingüísticas peruanas y abreviaturas)
desde un archivo de texto crudo extraído del PDF y lo guarda en un JSON.

Uso:
    python parse_metadata.py \
        --input data/diccionario_raw_mejorado.txt \
        --output abbreviations.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


HEADING_COUNTRIES = re.compile(r"^\s*PA[IÍ]SES\s+DEL\s+[ÁA]REA\s+ANDINA\s*$", re.IGNORECASE)
HEADING_PERU_REGIONS = re.compile(r"^\s*REGIONES\s+LING[ÜU][ÍI]STICAS\s+PERUANAS\s*$", re.IGNORECASE)
HEADING_ABBREVIATIONS = re.compile(r"^\s*ABREVIATURAS\s*$", re.IGNORECASE)
# Posibles headings de cierre para secciones introductorias
HEADING_AUTHORS = re.compile(r"^\s*Autores\s+consultados\s*$", re.IGNORECASE)
HEADING_AMLQ = re.compile(r"^\s*Miembros\s+de\s+la\s+AMLQ\s*$", re.IGNORECASE)
HEADING_DICTIONARY = re.compile(r"^\s*Diccionario\s+quechua\s*-\s*castellano\s*$", re.IGNORECASE)


def read_lines(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Normaliza saltos de línea y recortes a la derecha
    return [ln.rstrip("\n\r") for ln in text.splitlines()]


def find_heading_index(lines: List[str], rx: re.Pattern) -> int | None:
    for i, ln in enumerate(lines):
        if rx.match(ln.strip()):
            return i
    return None


def find_last_heading_index(lines: List[str], rx: re.Pattern) -> int | None:
    idx = None
    for i, ln in enumerate(lines):
        if rx.match(ln.strip()):
            idx = i
    return idx


def find_heading_index_with_numbered_list(lines: List[str], rx: re.Pattern, lookahead: int = 8) -> int | None:
    """Devuelve el índice del primer heading cuya vecindad contiene un ítem '1.' en las
    siguientes 'lookahead' líneas. Evita confundir con el índice del contenido (TOC).
    """
    n = len(lines)
    for i, ln in enumerate(lines):
        if not rx.match(ln.strip()):
            continue
        end = min(n, i + 1 + lookahead)
        if any(re.match(r"^\s*1\.\s+", lines[j]) for j in range(i + 1, end)):
            return i
    return None


def parse_numbered_pairs(lines: List[str], start_idx: int, stop_regexes: List[re.Pattern]) -> Tuple[Dict[str, str], int]:
    """Parsea bloques del estilo:
        1. Arg.
        Argentina
        2. Bol.
        Bolivia
    Devuelve mapping {"Arg.": "Argentina", ...} y el índice donde terminó.
    """
    mapping: Dict[str, str] = {}
    i = start_idx + 1
    n = len(lines)
    while i < n:
        cur = lines[i].strip()
        # ¿Llegamos al siguiente heading?
        if not cur:
            i += 1
            continue
        if any(rx.match(cur) for rx in stop_regexes):
            break
        # Espera patrón "n. abreviatura"
        m = re.match(r"^(\d+)\.\s*(.+?)\s*$", cur)
        if m:
            abbr = m.group(2).strip()
            # Busca el siguiente no vacío como valor
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n:
                name = lines[j].strip()
                # Si el valor parece otro heading, detenemos
                if any(rx.match(name) for rx in stop_regexes):
                    break
                mapping[abbr] = name
                i = j + 1
                continue
            else:
                break
        else:
            # Si no coincide, puede ser que el bloque haya terminado
            if any(rx.match(cur) for rx in stop_regexes):
                break
            # Si hay líneas de ruido, saltarlas
            i += 1
    return mapping, i


def parse_abbreviations(lines: List[str], start_idx: int, stop_regexes: List[re.Pattern]) -> Tuple[Dict[str, str], int]:
    """Parsea la sección ABREVIATURAS, asumiendo formato lineal de pares:
        Acust.
        Acústica
        adj.
        adjetivo
    Devuelve mapping y el índice final.
    """
    mapping: Dict[str, str] = {}
    i = start_idx + 1
    n = len(lines)
    while i < n:
        cur = lines[i].strip()
        if any(rx.match(cur) for rx in stop_regexes):
            break
        if not cur:
            i += 1
            continue
        key = cur
        # Próxima línea no vacía como valor
        j = i + 1
        while j < n and not lines[j].strip():
            j += 1
        if j >= n:
            break
        val = lines[j].strip()
        if any(rx.match(val) for rx in stop_regexes):
            break
        mapping[key] = val
        i = j + 1
    return mapping, i


def strip_trailing_punct(s: str) -> str:
    return re.sub(r"[\s\.;:,]+$", "", s).strip()


def parse_country_dialects(lines: List[str], start_idx: int, stop_regexes: List[re.Pattern]) -> Tuple[Dict[str, List[str]], int]:
    """Parsea variaciones dialectales por país, con formato similar a:
        1. Argentina:
        Santiago del Estero, Catamarca y 
        Jujuy.
        2. Bolivia:
        La Paz (Charasani), Cochabamba, 
        Oruro y Sucre - Potosí.
    Devuelve mapping {"Argentina": ["Santiago del Estero", "Catamarca", "Jujuy"], ...}
    """
    result: Dict[str, List[str]] = {}
    i = start_idx
    n = len(lines)

    country_names = {"Argentina", "Bolivia", "Colombia", "Chile", "Ecuador", "Perú"}
    # Acepta encabezados con o sin numeración previa
    country_item_rx = re.compile(r"^\s*(?:\d+\.)?\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)\s*:\s*$")

    while i < n:
        cur = lines[i].strip()
        if not cur:
            i += 1
            continue
        if any(rx.match(cur) for rx in stop_regexes):
            break
        m = country_item_rx.match(cur)
        if not m:
            # Si no es un ítem válido, avanzar
            i += 1
            continue
        country = m.group(1)
        if country not in country_names:
            i += 1
            continue
        # Acumular líneas hasta el próximo ítem o heading
        j = i + 1
        acc: List[str] = []
        while j < n:
            nxt = lines[j].strip()
            if not nxt:
                j += 1
                continue
            if country_item_rx.match(nxt) or any(rx.match(nxt) for rx in stop_regexes):
                break
            acc.append(nxt)
            j += 1
        # Unir y normalizar delimitadores
        joined = " ".join(acc)
        joined = re.sub(r"\s+", " ", joined).strip()
        joined = strip_trailing_punct(joined)
        # Separar por comas y conectores " y "
        parts: List[str] = []
        if joined:
            # Primero separar por coma
            for seg in joined.split(','):
                seg = seg.strip()
                # Luego separar por ' y '
                subparts = [s.strip() for s in re.split(r"\s+y\s+", seg) if s.strip()]
                parts.extend(subparts)
        result[country] = parts
        i = j
    return result, i


def extract_metadata(input_path: Path) -> Dict[str, Dict[str, str]]:
    lines = read_lines(input_path)

    # Buscar headings con heurísticas
    countries_idx = find_heading_index_with_numbered_list(lines, HEADING_COUNTRIES)
    if countries_idx is None:
        countries_idx = find_heading_index(lines, HEADING_COUNTRIES)

    peru_regions_idx = find_heading_index_with_numbered_list(lines, HEADING_PERU_REGIONS)
    if peru_regions_idx is None:
        peru_regions_idx = find_heading_index(lines, HEADING_PERU_REGIONS)

    # Para abreviaturas, elegir la ÚLTIMA ocurrencia (evita 'Abreviaturas' en el índice)
    abbreviations_idx = find_last_heading_index(lines, HEADING_ABBREVIATIONS)

    stop_regexes = [HEADING_PERU_REGIONS, HEADING_ABBREVIATIONS, HEADING_AUTHORS, HEADING_AMLQ, HEADING_DICTIONARY]

    countries: Dict[str, str] = {}
    peru_regions: Dict[str, str] = {}
    abbreviations: Dict[str, str] = {}
    country_dialects: Dict[str, List[str]] = {}

    # Países
    end_idx = None
    if countries_idx is not None:
        countries, end_idx = parse_numbered_pairs(lines, countries_idx, stop_regexes)

    # Regiones peruanas y dialectos
    end_regions_idx = None
    if peru_regions_idx is not None:
        # para regiones peruanas, detener ante abreviaturas o autores, etc.
        stop_after_regions = [HEADING_ABBREVIATIONS, HEADING_AUTHORS, HEADING_AMLQ, HEADING_DICTIONARY]
        peru_regions_all, end_regions_idx = parse_numbered_pairs(lines, peru_regions_idx, stop_after_regions)
        # Filtrar solo las claves con prefijo 'Pe.' y normalizar valores
        peru_regions = {k: strip_trailing_punct(v) for k, v in peru_regions_all.items() if k.startswith("Pe.")}
        # Intentar parsear variaciones dialectales a continuación
        if end_regions_idx is not None:
            dialect_stop = [HEADING_ABBREVIATIONS, HEADING_AUTHORS, HEADING_AMLQ, HEADING_DICTIONARY]
            country_dialects, _ = parse_country_dialects(lines, end_regions_idx, dialect_stop)

    # Abreviaturas
    if abbreviations_idx is not None:
        stop_after_abbrs = [HEADING_AUTHORS, HEADING_AMLQ, HEADING_DICTIONARY]
        abbreviations, _ = parse_abbreviations(lines, abbreviations_idx, stop_after_abbrs)

    return {
        "countries": countries,
        "peru_regions": peru_regions,
        "country_dialects": country_dialects,
        "abbreviations": abbreviations,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extrae metadatos (países, regiones y abreviaturas) del texto crudo")
    parser.add_argument("--input", default="/media/kingston-apps/PNL/data/diccionario_raw_mejorado.txt", help="Ruta del archivo de texto crudo")
    parser.add_argument("--output", default="/media/kingston-apps/PNL/abbreviations.json", help="Ruta del JSON de salida")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    meta = extract_metadata(input_path)
    # Guardar con pretty print y UTF-8
    output_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Metadatos guardados en: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
