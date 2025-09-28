#!/usr/bin/env python3

import re

def es_inicio_lema(linea):
    """Detecta si una línea es el inicio de un nuevo lema"""
    linea = linea.strip()
    if not linea:
        return False

    # Patrones de inicio de lema más específicos
    patrones = [
        # Formato: "palabra. tipo." o "palabra, palabra. tipo."
        r'^[A-Za-záéíóúñüÁÉÍÓÚÑÜ]+(?:,\s*[A-Za-záéíóúñüÁÉÍÓÚÑÜ]+)*\.\s*(s\.|v\.|adj\.|adv\.|interj\.|alfab\.|fam\.|Geog\.|Bot\.|Zool\.|Med\.Folk\.|Hist\.|Relig\.|Mús\.|Ecol\.Veg\.)',
        # Tipos múltiples
        r'^[A-Za-záéíóúñüÁÉÍÓÚÑÜ]+\.\s*(adj\.\s*y\s*s\.|s\.\s*y\s*adj\.|v\.\s*y\s*s\.|s\.\s*y\s*v\.)',
        # Interjecciones con exclamación
        r'^[A-Za-záéíóúñüÁÉÍÓÚÑÜ]+!\s*interj\.',
    ]

    for patron in patrones:
        if re.match(patron, linea, re.IGNORECASE):
            return True

    return False

def es_contexto_interno(linea):
    """Detecta si es parte interna de una definición, no un nuevo lema"""
    linea = linea.strip()

    # Contextos internos específicos que NO son nuevos lemas
    contextos_internos = [
        r'^VARIEDADES:',
        r'^SINÓN:',
        r'^EJEM:',
        r'^Pe\.Aya:',
        r'^Pe\.Anc:',
        r'^Pe\.Caj:',
        r'^Pe\.Jun:',
        r'^Pe\.S\.Mar:',
        r'^Pe\.Pun:',
        r'^Bol:',
        r'^Ec:',
        r'^Arg:',
        r'^Folk\.',
        r'^Med\.Folk\.',
        r'^Ecol\.Veg\.',
        r'^\|\|',  # Separador de acepciones adicionales
    ]

    # Solo marcar como contexto interno patrones específicos
    for patron in contextos_internos:
        if re.match(patron, linea, re.IGNORECASE):
            return True

    return False

def extraer_lema(linea):
    """Extrae el lema (palabra) de la línea de inicio"""
    linea = linea.strip()

    # Buscar la primera palabra antes del punto o tipo gramatical
    match = re.match(r'^([A-Za-záéíóúñüÁÉÍÓÚÑÜ]+)', linea)
    if match:
        return match.group(1)

    return None

def normalizar_diccionario_simple(archivo_entrada, archivo_salida, debug=False):
    """
    Enfoque simple y confiable:
    1. Procesa línea por línea
    2. Detecta inicios de lemas de manera conservadora
    3. Une líneas hasta encontrar el siguiente lema
    """

    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    entradas = []  # Lista de entradas completas
    entrada_actual = []  # Líneas de la entrada actual
    lema_actual = None

    for i, linea in enumerate(lineas):
        linea_limpia = linea.strip()

        # Saltar líneas vacías
        if not linea_limpia:
            continue

        if debug:
            print(f"Línea {i+1}: {linea_limpia}")

        # Verificar si es inicio de un nuevo lema
        es_lema = es_inicio_lema(linea_limpia)
        es_interno = es_contexto_interno(linea_limpia)

        if debug:
            print(f"  es_inicio_lema: {es_lema}, es_contexto_interno: {es_interno}")

        if es_lema and not es_interno:
            # Si ya hay una entrada en proceso, guardarla
            if entrada_actual and lema_actual:
                texto_entrada = ' '.join(entrada_actual).strip()
                entradas.append({
                    'lema': lema_actual,
                    'texto': texto_entrada
                })
                if debug:
                    print(f"  -> Guardada entrada: {lema_actual}")

            # Iniciar nueva entrada
            lema_actual = extraer_lema(linea_limpia)
            entrada_actual = [linea_limpia]
            if debug:
                print(f"  -> Nuevo lema: {lema_actual}")
        else:
            # Continuar con la entrada actual
            if entrada_actual:  # Solo si ya hay una entrada iniciada
                entrada_actual.append(linea_limpia)
                if debug:
                    print(f"  -> Continuando entrada")

    # No olvidar la última entrada
    if entrada_actual and lema_actual:
        texto_entrada = ' '.join(entrada_actual).strip()
        entradas.append({
            'lema': lema_actual,
            'texto': texto_entrada
        })

    # Crear el texto final con marcadores
    resultado = []
    for entrada in entradas:
        resultado.append(f"<begin>\n{entrada['texto']}\n<end>")

    # Guardar resultado
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write('\n'.join(resultado))

    print(f"Diccionario normalizado simple guardado en: {archivo_salida}")
    print(f"Total de lemas procesados: {len(entradas)}")

    # Mostrar estadísticas de lemas repetidos
    lemas_unicos = {}
    for entrada in entradas:
        lema = entrada['lema'].lower()
        if lema in lemas_unicos:
            lemas_unicos[lema] += 1
        else:
            lemas_unicos[lema] = 1

    repetidos = {k: v for k, v in lemas_unicos.items() if v > 1}
    print(f"Lemas con múltiples acepciones: {len(repetidos)}")

    if repetidos:
        print("Ejemplos de lemas repetidos:")
        for lema, count in list(repetidos.items())[:5]:
            print(f"  {lema}: {count} acepciones")

    return entradas

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso:")
        print("  python normalizador_simple.py <archivo_entrada> [archivo_salida]")
        print("  python normalizador_simple.py --test")
        sys.exit(1)

    if sys.argv[1] == '--test':
        # Probar con casos problemáticos
        normalizar_diccionario_simple('casos_problematicos.txt', 'casos_simple.txt')
    elif sys.argv[1] == '--debug':
        # Debug con muestra
        normalizar_diccionario_simple('muestra_con_definiciones.txt', 'debug_output.txt', debug=True)
    else:
        archivo_entrada = sys.argv[1]
        archivo_salida = sys.argv[2] if len(sys.argv) > 2 else 'diccionario_simple.txt'
        normalizar_diccionario_simple(archivo_entrada, archivo_salida)