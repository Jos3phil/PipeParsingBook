#!/usr/bin/env python3
"""
Divide el diccionario raw usando líneas fijas específicas.

División:
- Líneas 1302-51003: Sección Quechua-Español
- Líneas 51004-final: Sección Español-Quechua
"""

from pathlib import Path


def dividir_diccionario_lineas_fijas(
    archivo_entrada: str,
    inicio_qe: int = 1302,
    fin_qe: int = 51003,
    inicio_eq: int = 51004,
    archivo_qe: str | None = None,
    archivo_eq: str | None = None,
):
    """
    Divide el diccionario usando líneas fijas específicas.

    Args:
        archivo_entrada: Archivo diccionario_raw.txt
        inicio_qe: Línea inicio quechua-español (1302)
        fin_qe: Línea fin quechua-español (51003)
        inicio_eq: Línea inicio español-quechua (51004)
        archivo_qe: Archivo de salida para Quechua-Español
        archivo_eq: Archivo de salida para Español-Quechua
    """

    print(f"Leyendo archivo: {archivo_entrada}")

    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    print(f"Total de líneas en archivo: {len(lineas)}")

    # Convertir a índices 0-based
    idx_inicio_qe = inicio_qe - 1
    idx_fin_qe = fin_qe - 1
    idx_inicio_eq = inicio_eq - 1

    # Validar rangos
    if idx_inicio_qe >= len(lineas):
        raise ValueError(f"Línea inicio QE {inicio_qe} excede el archivo ({len(lineas)} líneas)")
    if idx_fin_qe >= len(lineas):
        raise ValueError(f"Línea fin QE {fin_qe} excede el archivo ({len(lineas)} líneas)")
    if idx_inicio_eq >= len(lineas):
        raise ValueError(f"Línea inicio EQ {inicio_eq} excede el archivo ({len(lineas)} líneas)")

    print(f"Extrayendo Quechua-Español: líneas {inicio_qe} a {fin_qe}")
    print(f"Extrayendo Español-Quechua: líneas {inicio_eq} a {len(lineas)}")

    # Extraer secciones
    seccion_qe = lineas[idx_inicio_qe:idx_fin_qe + 1]  # +1 para incluir fin_qe
    seccion_eq = lineas[idx_inicio_eq:]

    # Limpiar y unir
    texto_qe = ''.join(seccion_qe).strip()
    texto_eq = ''.join(seccion_eq).strip()

    # Guardar archivos
    archivo_qe = archivo_qe or "data/diccionario_quechua_espanol_fijo.txt"
    archivo_eq = archivo_eq or "data/diccionario_espanol_quechua_fijo.txt"

    Path(archivo_qe).parent.mkdir(parents=True, exist_ok=True)
    Path(archivo_eq).parent.mkdir(parents=True, exist_ok=True)

    with open(archivo_qe, 'w', encoding='utf-8') as f:
        f.write(texto_qe)

    with open(archivo_eq, 'w', encoding='utf-8') as f:
        f.write(texto_eq)

    print(f"\n=== Resultados ===")
    print(f"Quechua-Español guardado en: {archivo_qe}")
    print(f"  - Líneas procesadas: {len(seccion_qe)}")
    print(f"  - Caracteres: {len(texto_qe)}")

    print(f"Español-Quechua guardado en: {archivo_eq}")
    print(f"  - Líneas procesadas: {len(seccion_eq)}")
    print(f"  - Caracteres: {len(texto_eq)}")

    # Mostrar primeras líneas de cada sección para verificar
    print(f"\n=== Verificación Quechua-Español (primeras 5 líneas) ===")
    for i, linea in enumerate(seccion_qe[:5]):
        print(f"{inicio_qe + i}: {linea.rstrip()}")

    print(f"\n=== Verificación Español-Quechua (primeras 5 líneas) ===")
    for i, linea in enumerate(seccion_eq[:5]):
        print(f"{inicio_eq + i}: {linea.rstrip()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Divide el diccionario RAW por líneas fijas en QE y EQ.")
    parser.add_argument("--entrada", "-i", default="data/diccionario_raw.txt", help="Archivo diccionario_raw.txt")
    parser.add_argument("--inicio-qe", type=int, default=1302, help="Línea inicio QE (1-based)")
    parser.add_argument("--fin-qe", type=int, default=51003, help="Línea fin QE (1-based, inclusiva)")
    parser.add_argument("--inicio-eq", type=int, default=51004, help="Línea inicio EQ (1-based)")
    parser.add_argument("--out-qe", default="data/diccionario_quechua_espanol_fijo.txt", help="Salida QE")
    parser.add_argument("--out-eq", default="data/diccionario_espanol_quechua_fijo.txt", help="Salida EQ")

    args = parser.parse_args()

    dividir_diccionario_lineas_fijas(
        archivo_entrada=args.entrada,
        inicio_qe=args.inicio_qe,
        fin_qe=args.fin_qe,
        inicio_eq=args.inicio_eq,
        archivo_qe=args.out_qe,
        archivo_eq=args.out_eq,
    )


if __name__ == "__main__":
    main()