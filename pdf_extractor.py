# filepath: /media/kingston-apps/PNL/pdf_extractor.py
"""
Extracción de texto crudo desde PDF preservando estructura básica y manejando páginas a 3 columnas.

- Usa PyMuPDF (fitz) para extraer texto dentro de rectángulos (clips) por columna.
- A partir de una página configurable, divide el área de contenido en 3 columnas iguales.
- Recorta márgenes y bandas de encabezado/pie para evitar mezclar encabezados con el contenido léxico.
- Escribe la salida en diccionario_raw.txt (por defecto en el directorio actual) preservando saltos de línea.

Requisitos:
    pip install pymupdf

Ejemplo de uso:
    python pdf_extractor.py \
        --input diccionario-qeswa-academia-mayor.pdf \
        --output diccionario_raw.txt \
        --margin-cm 2 --header-cm 2 --footer-cm 2 \
        --three-cols-start-page 13
"""
from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as e:
    print("[ERROR] No se pudo importar PyMuPDF (fitz). Instale con: pip install pymupdf", file=sys.stderr)
    raise


def cm_to_pt(cm: float) -> float:
    """Convierte centímetros a puntos (1 cm ≈ 28.3464567 pt)."""
    return cm * 28.3464567


def extract_page_text_by_clip(page: "fitz.Page", clip: "fitz.Rect", preserve_ws: bool = False) -> str:
    """Extrae texto de una página dentro de un rectángulo (clip).
    Si preserve_ws es True, preserva espacios en blanco tal cual el PDF.
    """
    try:
        if preserve_ws:
            return page.get_text("text", clip=clip, flags=fitz.TEXT_PRESERVE_WHITESPACE) or ""
        return page.get_text("text", clip=clip) or ""
    except TypeError:
        # Compatibilidad con versiones antiguas de PyMuPDF sin parámetro flags
        return page.get_text("text", clip=clip) or ""


def parse_pages_csv(pages_csv: str) -> set[int]:
    """Parsea una lista CSV de números de página (1-based) a un set[int]."""
    if not pages_csv:
        return set()
    result: set[int] = set()
    for part in pages_csv.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except ValueError:
            # Ignorar entradas inválidas
            continue
    return result


_HEADER_PATTERNS = [
    r"^\s*(DICCIONARIO|Diccionario)\s*$",
    r"^\s*SIMI\s+TAQE\s*$",
    r"^\s*QUECHUA\s*-\s*ESPA(?:Ñ|N)OL(?:\s*-\s*QUECHUA)?\s*$",
    r"^\s*QHESWA\s*-\s*ESPA(?:Ñ|N)OL(?:\s*-\s*QHESWA)?\s*$",
    r"^[\s◄●►·•*-]*$",
    r"^\s*\d+\s*$",
]
_HEADER_REGEXES = [re.compile(p) for p in _HEADER_PATTERNS]


def remove_known_header_lines(text: str) -> str:
    """Elimina, desde el inicio del texto de página, líneas típicas de encabezado si aparecen."""
    if not text:
        return text
    lines = text.splitlines()
    i = 0
    # Solo limpiar al inicio; detenernos cuando encontramos la primera línea que no parece encabezado
    while i < len(lines) and any(rx.match(lines[i]) for rx in _HEADER_REGEXES):
        i += 1
    return "\n".join(lines[i:]).lstrip("\n")


def extract_pdf_to_text(
    input_pdf: Path,
    output_txt: Path,
    margin_cm: float = 2.0,
    header_cm: float = 2.0,
    footer_cm: float = 2.0,
    three_cols_start_page: int = 13,
    # Nuevos parámetros
    preserve_spaces_until_page: int | None = None,
    special_header_pages: set[int] | None = None,
    special_header_cm: float | None = None,
    remove_header_lines: bool = False,
) -> None:
    """
    Extrae texto desde un PDF, preservando estructura básica y, desde una página dada, en 3 columnas.

    Parámetros:
    - input_pdf: ruta al PDF de entrada.
    - output_txt: ruta del archivo de texto de salida.
    - margin_cm: margen a recortar en todos los lados (cm).
    - header_cm: banda superior adicional a recortar como encabezado (cm).
    - footer_cm: banda inferior adicional a recortar como pie (cm).
    - three_cols_start_page: número de página (1-based) a partir del cual el contenido está en 3 columnas.
    - preserve_spaces_until_page: si se indica, preserva espacios en blanco tal cual hasta esa página (1-based).
    - special_header_pages: set de páginas (1-based) que usan un encabezado especial con altura special_header_cm.
    - special_header_cm: altura (cm) del encabezado especial para páginas en special_header_pages.
    - remove_header_lines: si es True, intenta eliminar líneas de encabezado conocidas al inicio del texto de cada página.
    """
    input_pdf = Path(input_pdf)
    output_txt = Path(output_txt)

    if not input_pdf.exists():
        raise FileNotFoundError(f"No se encontró el archivo PDF: {input_pdf}")

    # Convertir a puntos
    margin_pt = cm_to_pt(margin_cm)
    base_header_pt = cm_to_pt(header_cm)
    footer_pt = cm_to_pt(footer_cm)
    special_header_pt = cm_to_pt(special_header_cm) if special_header_cm is not None else None

    three_cols_start_idx = max(0, three_cols_start_page - 1)  # convertir a índice 0-based

    doc = fitz.open(input_pdf)
    try:
        all_pages_text: list[str] = []
        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            width, height = page.rect.width, page.rect.height
            page_no = page_idx + 1  # 1-based

            # Escoger altura de encabezado dinámica por página
            header_pt_this_page = base_header_pt
            if special_header_pages and (page_no in special_header_pages) and (special_header_pt is not None):
                header_pt_this_page = special_header_pt

            # Área de contenido (recorta márgenes y bandas de encabezado/pie)
            x0 = margin_pt
            y0 = margin_pt + header_pt_this_page
            x1 = width - margin_pt
            y1 = height - margin_pt - footer_pt
            content_rect = fitz.Rect(x0, y0, x1, y1)

            if content_rect.width <= 0 or content_rect.height <= 0:
                # Si los parámetros dejan un área inválida, extraer toda la página como fallback
                page_text = page.get_text("text") or ""
                if remove_header_lines:
                    page_text = remove_known_header_lines(page_text)
                all_pages_text.append(page_text.strip())
                continue

            preserve_ws = (preserve_spaces_until_page is not None) and (page_no <= preserve_spaces_until_page)

            if page_idx >= three_cols_start_idx:
                # Dividir en 3 columnas iguales dentro del área de contenido
                col_w = content_rect.width / 3.0
                col1 = fitz.Rect(content_rect.x0, content_rect.y0, content_rect.x0 + col_w, content_rect.y1)
                col2 = fitz.Rect(content_rect.x0 + col_w, content_rect.y0, content_rect.x0 + 2 * col_w, content_rect.y1)
                col3 = fitz.Rect(content_rect.x0 + 2 * col_w, content_rect.y0, content_rect.x1, content_rect.y1)

                t1 = extract_page_text_by_clip(page, col1, preserve_ws=preserve_ws).rstrip()
                t2 = extract_page_text_by_clip(page, col2, preserve_ws=preserve_ws).rstrip()
                t3 = extract_page_text_by_clip(page, col3, preserve_ws=preserve_ws).rstrip()

                # Unir columnas en orden de lectura: izquierda -> derecha
                page_text = "\n\n".join([t1, t2, t3]).strip()
            else:
                # Páginas iniciales: extraer como una sola columna (texto corrido)
                page_text = extract_page_text_by_clip(page, content_rect, preserve_ws=preserve_ws).strip()

            if remove_header_lines and page_text:
                page_text = remove_known_header_lines(page_text)

            all_pages_text.append(page_text)

        # Separar páginas con dos saltos de línea
        final_text = "\n\n".join(all_pages_text).rstrip() + "\n"
        output_txt.write_text(final_text, encoding="utf-8")

    finally:
        doc.close()


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Extrae texto crudo desde un PDF (manejo de 3 columnas desde una página dada)")
    p.add_argument("--input", required=True, help="Ruta al PDF de entrada")
    p.add_argument("--output", default="/media/kingston-apps/PNL/data/diccionario_raw.txt", help="Ruta del archivo .txt de salida (por defecto diccionario_raw.txt)")
    p.add_argument("--margin-cm", type=float, default=2.0, help="Margen (cm) a recortar en todos los lados (por defecto 2.0)")
    p.add_argument("--header-cm", type=float, default=2.0, help="Altura (cm) adicional de encabezado a recortar (por defecto 2.0)")
    p.add_argument("--footer-cm", type=float, default=2.0, help="Altura (cm) adicional de pie de página a recortar (por defecto 2.0)")
    p.add_argument(
        "--three-cols-start-page",
        type=int,
        default=13,
        help="Página (1-based) desde la cual el PDF está en 3 columnas (por defecto 13)",
    )
    # Nuevos flags
    p.add_argument(
        "--preserve-spaces-until-page",
        type=int,
        default=None,
        help="Hasta qué página (1-based) preservar espacios en blanco exactamente (por ejemplo 12)",
    )
    p.add_argument(
        "--special-header-pages",
        default="",
        help="Páginas (CSV) con encabezado especial (por ejemplo '13,249')",
    )
    p.add_argument(
        "--special-header-cm",
        type=float,
        default=None,
        help="Altura (cm) del encabezado especial para las páginas indicadas",
    )
    p.add_argument(
        "--remove-header-lines",
        action="store_true",
        help="Si se indica, elimina líneas típicas de encabezado detectadas al inicio del texto de la página",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        extract_pdf_to_text(
            input_pdf=Path(args.input),
            output_txt=Path(args.output),
            margin_cm=args.margin_cm,
            header_cm=args.header_cm,
            footer_cm=args.footer_cm,
            three_cols_start_page=args.three_cols_start_page,
            preserve_spaces_until_page=args.preserve_spaces_until_page,
            special_header_pages=parse_pages_csv(args.special_header_pages),
            special_header_cm=args.special_header_cm,
            remove_header_lines=args.remove_header_lines,
        )
        print(f"[OK] Texto extraído en: {args.output}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
