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


def _dehyphenate(text: str) -> str:
    """Une palabras cortadas por salto de línea con guion duro o blando.
    Regla básica: "palabra-\ncontinuacion" -> "palabracontinuacion" si la continuación inicia en minúscula o acentuada.
    También elimina guiones suaves (\xad) al final de línea.
    """
    if not text:
        return text
    # quitar guion suave (soft hyphen) antes de saltos de línea
    text = re.sub(r"\xad\n", "\n", text)
    # casos como "palabra-\ncontinuacion" => "palabracontinuacion"
    # incluye letras acentuadas y ñ
    continuation = "a-záéíóúñäëïöüàèìòùç"  # minúsculas comunes en español
    pattern = re.compile(rf"([A-Za-zÁÉÍÓÚÑÄËÏÖÜÀÈÌÒÙÇ]+)-\n([{continuation}])")
    # aplicar repetidamente hasta que no haya más coincidencias
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(r"\1\2", text)
    return text


# === Auto detección del rectángulo de contenido por página ===
# Usa los bloques de texto reales para delimitar dinámicamente el contenido y evitar
# recortes superiores/inferiores que corten palabras.

def _get_text_blocks(page: "fitz.Page") -> list[tuple]:
    """Devuelve bloques de texto (x0, y0, x1, y1, text, ...)."""
    try:
        return page.get_text("blocks") or []
    except Exception:
        return []

def _is_header_footer_block(text: str) -> bool:
    """Heurística para identificar bloques que son encabezado/pie conocidos o números de página."""
    if not text:
        return False
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    def is_page_num(s: str) -> bool:
        return bool(re.fullmatch(r"\d{1,4}", s))
    for ln in lines:
        if any(rx.match(ln) for rx in _HEADER_REGEXES):
            continue
        if is_page_num(ln):
            continue
        return False
    return True

def _auto_content_rect(page: "fitz.Page", margin_pt: float, pad_top_pt: float, pad_bottom_pt: float) -> "fitz.Rect":
    """Detecta dinámicamente el rectángulo de contenido a partir de los bloques de texto.
    Aplica padding superior/inferior y respeta un margen horizontal mínimo.
    """
    page_rect = page.rect
    blocks = _get_text_blocks(page)

    candidates: list[tuple[float, float, float, float]] = []
    for b in blocks:
        if len(b) < 5:
            continue
        x0, y0, x1, y1, txt = b[:5]
        if not (isinstance(txt, str) and txt.strip()):
            continue
        if _is_header_footer_block(txt):
            continue
        # descartar bloques extremadamente pequeños (ruido)
        if (x1 - x0) < 2 or (y1 - y0) < 2:
            continue
        candidates.append((x0, y0, x1, y1))

    if not candidates:
        # fallback: usar márgenes uniformes
        x0 = margin_pt
        x1 = page_rect.width - margin_pt
        y0 = margin_pt
        y1 = page_rect.height - margin_pt
        return fitz.Rect(x0, y0, x1, y1)

    min_x = min(x0 for x0, _, _, _ in candidates)
    max_x = max(x1 for _, _, x1, _ in candidates)
    min_y = min(y0 for _, y0, _, _ in candidates)
    max_y = max(y1 for _, _, _, y1 in candidates)

    # Ampliar con padding y limitar por los márgenes horizontales
    x0 = max(margin_pt, min_x - 2)
    x1 = min(page_rect.width - margin_pt, max_x + 2)
    y0 = max(margin_pt, min_y - pad_top_pt)
    y1 = min(page_rect.height - margin_pt, max_y + pad_bottom_pt)

    if x1 <= x0 or y1 <= y0:
        return page_rect
    return fitz.Rect(x0, y0, x1, y1)


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
    # Auto detección del rectángulo de contenido
    auto_detect_content_rect: bool = False,
    auto_rect_pad_top_cm: float = 0.2,
    auto_rect_pad_bottom_cm: float = 0.2,
    # Nuevas mejoras
    dehyphenate_lines: bool = False,
    debug_export_content_rects: Path | None = None,
    # Rango de páginas y columnas genéricas
    start_page: int | None = None,
    end_page: int | None = None,
    cols_start_page: int | None = None,
    cols_after_start: int = 3,
    col_overlap_cm: float = 0.0,
) -> None:
    """
    Extrae texto desde un PDF, preservando estructura básica y, desde una página dada, en N columnas.

    Parámetros:
    - input_pdf: ruta al PDF de entrada.
    - output_txt: ruta del archivo de texto de salida.
    - margin_cm: margen a recortar en todos los lados (cm).
    - header_cm: banda superior adicional a recortar como encabezado (cm).
    - footer_cm: banda inferior adicional a recortar como pie (cm).
    - three_cols_start_page: [DEPRECATED] página (1-based) para pasar a 3 columnas (para compatibilidad).
    - preserve_spaces_until_page: si se indica, preserva espacios en blanco tal cual hasta esa página (1-based).
    - special_header_pages: set de páginas (1-based) que usan un encabezado especial con altura special_header_cm.
    - special_header_cm: altura (cm) del encabezado especial para páginas en special_header_pages.
    - remove_header_lines: elimina líneas de encabezado conocidas al inicio del texto de cada página.
    - auto_detect_content_rect: detecta dinámicamente el rectángulo de contenido por página.
    - auto_rect_pad_top_cm / auto_rect_pad_bottom_cm: padding extra (cm) aplicado arriba/abajo al rect detectado.
    - dehyphenate_lines: une palabras separadas por guion al final de línea.
    - debug_export_content_rects: si se indica una ruta, exporta CSV con rectángulos de contenido por página.
    - start_page / end_page: rango (1-based, inclusivo) de páginas a procesar.
    - cols_start_page: página (1-based) a partir de la cual usar 'cols_after_start' columnas. Si None, usa 'three_cols_start_page'.
    - cols_after_start: número de columnas a usar a partir de 'cols_start_page' (por defecto 3).
    - col_overlap_cm: solape horizontal (cm) entre columnas para evitar cortes en los bordes (por defecto 0.0).
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
    pad_top_pt = cm_to_pt(auto_rect_pad_top_cm)
    pad_bottom_pt = cm_to_pt(auto_rect_pad_bottom_cm)
    col_overlap_pt = cm_to_pt(col_overlap_cm)

    doc = fitz.open(input_pdf)
    try:
        page_count = doc.page_count
        # Rango de páginas efectivo (1-based)
        eff_start_page = max(1, start_page) if start_page else 1
        eff_end_page = min(page_count, end_page) if end_page else page_count
        if eff_start_page > eff_end_page:
            raise ValueError("start_page > end_page")

        # Índice para columnas (0-based)
        effective_cols_start_page = cols_start_page if cols_start_page is not None else three_cols_start_page
        cols_start_idx = max(0, (effective_cols_start_page or 1) - 1)

        all_pages_text: list[str] = []
        rect_rows: list[str] = []
        if debug_export_content_rects is not None:
            rect_rows.append("page_no,x0,y0,x1,y1")
        for page_idx in range(page_count):
            page_no = page_idx + 1
            if page_no < eff_start_page or page_no > eff_end_page:
                continue

            page = doc.load_page(page_idx)
            width, height = page.rect.width, page.rect.height

            # Escoger altura de encabezado dinámica por página
            header_pt_this_page = base_header_pt
            if special_header_pages and (page_no in special_header_pages) and (special_header_pt is not None):
                header_pt_this_page = special_header_pt

            # Área de contenido (recorta márgenes y bandas de encabezado/pie)
            if auto_detect_content_rect:
                content_rect = _auto_content_rect(page, margin_pt, pad_top_pt, pad_bottom_pt)
            else:
                x0 = margin_pt
                y0 = margin_pt + header_pt_this_page
                x1 = width - margin_pt
                y1 = height - margin_pt - footer_pt
                content_rect = fitz.Rect(x0, y0, x1, y1)

            if debug_export_content_rects is not None:
                rect_rows.append(f"{page_no},{content_rect.x0:.2f},{content_rect.y0:.2f},{content_rect.x1:.2f},{content_rect.y1:.2f}")

            if content_rect.width <= 0 or content_rect.height <= 0:
                # fallback: extraer toda la página
                page_text = page.get_text("text") or ""
                if remove_header_lines:
                    page_text = remove_known_header_lines(page_text)
                if dehyphenate_lines and page_text:
                    page_text = _dehyphenate(page_text)
                all_pages_text.append(page_text.strip())
                continue

            preserve_ws = (preserve_spaces_until_page is not None) and (page_no <= preserve_spaces_until_page)

            # Determinar número de columnas para esta página
            num_cols = cols_after_start if page_idx >= cols_start_idx else 1
            if num_cols <= 1:
                page_text = extract_page_text_by_clip(page, content_rect, preserve_ws=preserve_ws).strip()
                if dehyphenate_lines:
                    page_text = _dehyphenate(page_text)
            else:
                col_w = content_rect.width / float(num_cols)
                cols_text: list[str] = []
                for i in range(num_cols):
                    left = content_rect.x0 + i * col_w
                    right = content_rect.x0 + (i + 1) * col_w
                    # aplicar solape
                    if i > 0:
                        left -= col_overlap_pt / 2.0
                    if i < num_cols - 1:
                        right += col_overlap_pt / 2.0
                    # clamp
                    left = max(content_rect.x0, left)
                    right = min(content_rect.x1, right)
                    col_rect = fitz.Rect(left, content_rect.y0, right, content_rect.y1)
                    t = extract_page_text_by_clip(page, col_rect, preserve_ws=preserve_ws).rstrip()
                    if dehyphenate_lines:
                        t = _dehyphenate(t)
                    cols_text.append(t)
                page_text = "\n\n".join(cols_text).strip()

            if remove_header_lines and page_text:
                page_text = remove_known_header_lines(page_text)

            all_pages_text.append(page_text)

        # Separar páginas con dos saltos de línea
        final_text = "\n\n".join(all_pages_text).rstrip() + "\n"
        output_txt.write_text(final_text, encoding="utf-8")

        if debug_export_content_rects is not None and rect_rows:
            Path(debug_export_content_rects).write_text("\n".join(rect_rows) + "\n", encoding="utf-8")

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
        help="[DEPRECATED] Página (1-based) desde la cual el PDF está en 3 columnas (por defecto 13)",
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
    # Auto content rect flags
    p.add_argument(
        "--auto-detect-content-rect",
        action="store_true",
        help="Detecta automáticamente el rectángulo de contenido por página usando bloques de texto",
    )
    p.add_argument(
        "--auto-rect-pad-top-cm",
        type=float,
        default=0.2,
        help="Padding superior (cm) añadido al rectángulo detectado automáticamente (por defecto 0.2)",
    )
    p.add_argument(
        "--auto-rect-pad-bottom-cm",
        type=float,
        default=0.2,
        help="Padding inferior (cm) añadido al rectángulo detectado automáticamente (por defecto 0.2)",
    )
    p.add_argument(
        "--dehyphenate-lines",
        action="store_true",
        help="Une palabras separadas por guion al final de línea",
    )
    p.add_argument(
        "--debug-export-content-rects",
        default=None,
        help="Ruta de salida (CSV) para exportar los rectángulos de contenido usados por página",
    )
    # Rango de páginas y columnas
    p.add_argument("--start-page", type=int, default=None, help="Página inicial (1-based) a procesar")
    p.add_argument("--end-page", type=int, default=None, help="Página final (1-based) a procesar")
    p.add_argument("--cols-start-page", type=int, default=None, help="Página (1-based) a partir de la cual usar N columnas")
    p.add_argument("--cols-after-start", type=int, default=3, help="Número de columnas a partir de --cols-start-page (por defecto 3)")
    p.add_argument("--col-overlap-cm", type=float, default=0.0, help="Solape horizontal (cm) entre columnas (por defecto 0.0)")
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
            auto_detect_content_rect=args.auto_detect_content_rect,
            auto_rect_pad_top_cm=args.auto_rect_pad_top_cm,
            auto_rect_pad_bottom_cm=args.auto_rect_pad_bottom_cm,
            dehyphenate_lines=args.dehyphenate_lines,
            debug_export_content_rects=Path(args.debug_export_content_rects) if args.debug_export_content_rects else None,
            start_page=args.start_page,
            end_page=args.end_page,
            cols_start_page=args.cols_start_page,
            cols_after_start=args.cols_after_start,
            col_overlap_cm=args.col_overlap_cm,
        )
        print(f"[OK] Texto extraído en: {args.output}")
        if args.debug_export_content_rects:
            print(f"[OK] Rectángulos exportados en: {args.debug_export_content_rects}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
