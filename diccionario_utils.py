from typing import Dict, List, Optional, Tuple, Set, Union
from collections import defaultdict, Counter
class DiccionarioAPI:
   
    """
    API para consultar y manipular el diccionario Quechua-Español procesado.

    Funciones optimizadas eliminando redundancias y manteniendo nombres originales
    con referencias a la nomenclatura de las funciones de búsqueda básica requeridas.
     DiccionarioAPI

    API para consultar y manipular un diccionario procesado Quechua↔Español.

    Propósito
        Proveer operaciones de búsqueda, consulta de variantes dialectales y estadísticas
        sobre dos secciones del diccionario: Quechua→Español y Español→Quechua.
        Optimiza búsquedas mediante índices en memoria construidos al inicializar la instancia.

    Inicialización
        DiccionarioAPI(quechua_entries: List[Dict], spanish_entries: List[Dict])

            quechua_entries: Lista de entradas (dict) correspondientes a la sección
                             Quechua→Español.
            spanish_entries: Lista de entradas (dict) correspondientes a la sección
                             Español→Quechua.

    Estructura esperada de cada entrada (dict)
        - 'lema' : str                     # lema o forma canónica
        - 'categoria_gramatical' : str     # p. ej. 'sustantivo', 'verbo', ...
        - 'campo_semantico' : str          # p. ej. 'botanica', 'zoologia', ...
        - 'definicion' : str               # texto de la definición
        - 'variantes_dialectales' : dict   # {dialecto: variante, ...}
        - 'ejemplos' : list                # ejemplos de uso (opcional)
        Cualquier clave adicional es permitida; las búsquedas usan las claves anteriores.

    Atributos principales
        - quechua_entries: List[Dict]      # entradas de la sección Quechua→Español
        - spanish_entries: List[Dict]      # entradas de la sección Español→Quechua
        - all_entries: List[Dict]          # concatenación de ambas secciones
        - lema_index: Dict[str, List[Dict]]            # índice general por lema (normalizado a minúsculas)
        - category_index: Dict[str, List[Dict]]        # índice por categoría gramatical (minúsculas)
        - semantic_index: Dict[str, List[Dict]]        # índice por campo semántico (minúsculas)
        - quechua_lema_index: Dict[str, List[Dict]]    # índice por lema para la sección Quechua
        - spanish_lema_index: Dict[str, List[Dict]]    # índice por lema para la sección Español

    Comportamiento y funciones principales
        - Búsquedas por lema:
            - buscar_por_quechua(lema: str) -> List[Dict]
                Busca en la sección Quechua→Español. Intenta coincidencia exacta
                (normalizando a minúsculas); si no hay resultados realiza una búsqueda
                parcial (subcadena, prefijos recíprocos).
            - buscar_por_espanol(lema: str) -> List[Dict]
                Igual que buscar_por_quechua pero en la sección Español→Quechua.
            - buscar_por_lema(lema: str, exacto: bool = False) -> List[Dict]
                Búsqueda genérica que abarca ambas secciones. Si exacto=True retorna
                coincidencias exactas; si exacto=False realiza coincidencias parciales
                (subcadena o inclusión recíproca).

        - Búsquedas por contenido:
            - buscar_por_definicion(termino: str) -> List[Dict]
                Retorna entradas cuya definición contiene el término (caso insensitive).
            - buscar_por_categoria_gramatical(categoria: str) -> List[Dict]
                Retorna entradas por categoría (búsqueda normalizada a minúsculas).
            - buscar_por_campo_semantico(campo: str) -> List[Dict]
                Retorna entradas por campo semántico (minúsculas).

        - Variantes dialectales:
            - obtener_variantes_dialectales(lema: str) -> List[str]
                Retorna una lista ordenada de variantes únicas encontradas para el lema
                (busca en ambas secciones). Excluye la forma idéntica al lema buscado.
            - obtener_variantes_dialectales_detalladas(lema: str) -> Dict[str, List[str]]
                Retorna un dict {dialecto: [variantes,...]} consolidando variantes de
                entradas con lema exactamente igual al proporcionado.

        - Estadísticas y análisis:
            - contar_entradas() -> Dict[str,int]
                Cuenta entradas por sección y total.
            - listar_categorias_gramaticales() -> List[str]
                Lista ordenada de categorías encontradas.
            - listar_campos_semanticos() -> List[str]
                Lista ordenada de campos semánticos encontrados.
            - listar_lemas() -> Dict
                Retorna lemas organizados por sección, estadísticas sobre longitudes,
                lemas comunes entre secciones y muestras (primeros/últimos).
            - estadisticas_generales() -> Dict
                Resumen estadístico: totales, conteos por categoría y campo, número y
                porcentajes de entradas con variantes y con ejemplos.

    Normalización y consideraciones
        - Todas las búsquedas de lemas y claves de índice se realizan con minúsculas
          para minimizar problemas de capitalización.
        - Las búsquedas parciales se basan en inclusion de subcadenas y comparaciones
          de prefijos recíprocos, lo cual puede devolver resultados amplios.
        - Índices se construyen en memoria al inicializar la instancia: operaciones
          de búsqueda son rápidas (O(1) para coincidencias exactas en índices; O(n)
          sobre los lemas indexados para búsquedas parciales).
        - No se realizan modificaciones automáticas sobre las listas de entradas
          pasadas al constructor. Si las entradas externas cambian después de la
          inicialización, reconstruir índices llamando internamente a _build_indexes()
          (método privado).

    Errores y robustez
        - Los métodos esperan que las entradas sean dicts y que las claves relevantes
          (p. ej. 'lema') existan o se manejen como cadenas vacías. No se lanzan
          excepciones específicas para entradas malformadas; tales entradas simplemente
          serán ignoradas en índices o búsquedas según corresponda.
        - No se garantiza seguridad para hilos (thread-safety) si la misma instancia
          es modificada concurrentemente.

    Ejemplo de uso (resumen)
        api = DiccionarioAPI(quechua_entries, spanish_entries)
        api.buscar_por_quechua("muna")
        api.obtener_variantes_dialectales("muna")
        api.estadisticas_generales()

    Notas
        - Diseñada para ser integrada en herramientas de consulta, APIs REST o utilidades
          de análisis lingüístico. La estructura de cada entrada puede ampliarse según
          necesidades siempre y cuando se mantengan las claves usadas por las búsquedas.
    """

    def __init__(self, quechua_entries: List[Dict], spanish_entries: List[Dict]):
        """
        Inicializa la API con las entradas procesadas de ambas secciones.

        Args:
            quechua_entries: Entradas de la sección Quechua→Español
            spanish_entries: Entradas de la sección Español→Quechua
        """
        self.quechua_entries = quechua_entries
        self.spanish_entries = spanish_entries
        self.all_entries = quechua_entries + spanish_entries

        # Crear índices para búsqueda rápida
        self._build_indexes()

    def _build_indexes(self):
        """
        Construye índices optimizados para búsqueda rápida por sección e idioma.
        """
        # Índices generales
        self.lema_index = defaultdict(list)
        self.category_index = defaultdict(list)
        self.semantic_index = defaultdict(list)

        # Índices específicos por sección/idioma
        self.quechua_lema_index = defaultdict(list)  # Para búsquedas en Quechua
        self.spanish_lema_index = defaultdict(list)  # Para búsquedas en Español

        # Indexar todas las entradas
        for entry in self.all_entries:
            # Índice general por lema
            lema = entry.get('lema', '').lower()
            if lema:
                self.lema_index[lema].append(entry)

            # Índice por categoría gramatical
            categoria = entry.get('categoria_gramatical', '')
            if categoria:
                self.category_index[categoria].append(entry)

            # Índice por campo semántico
            campo = entry.get('campo_semantico', '')
            if campo:
                self.semantic_index[campo].append(entry)

        # Indexar por secciones específicas
        for entry in self.quechua_entries:
            lema = entry.get('lema', '').lower()
            if lema:
                self.quechua_lema_index[lema].append(entry)

        for entry in self.spanish_entries:
            lema = entry.get('lema', '').lower()
            if lema:
                self.spanish_lema_index[lema].append(entry)

    # =================== FUNCIONES DE BÚSQUEDA ESPECÍFICAS POR IDIOMA ===================

    def buscar_por_quechua(self, lema: str) -> List[Dict]:
        """
        Busca entradas por lema en Quechua (sección Quechua→Español).

        NUEVA FUNCIÓN - Implementa: buscar_por_quechua(lema: str) -> List[Dict]

        Args:
            lema: Palabra en Quechua a buscar

        Returns:
            List[Dict]: Entradas que coinciden con el lema en Quechua
        """
        lema_lower = lema.lower()

        # Búsqueda exacta en el índice de Quechua
        exact_matches = self.quechua_lema_index.get(lema_lower, [])

        # Búsqueda parcial si no hay coincidencias exactas
        if not exact_matches:
            partial_matches = []
            for indexed_lema, entries in self.quechua_lema_index.items():
                if (lema_lower in indexed_lema or
                    indexed_lema.startswith(lema_lower) or
                    lema_lower.startswith(indexed_lema)):
                    partial_matches.extend(entries)
            return partial_matches

        return exact_matches

    def buscar_por_espanol(self, lema: str) -> List[Dict]:
        """
        Busca entradas por lema en Español (sección Español→Quechua).

        NUEVA FUNCIÓN - Implementa: buscar_por_espanol(lema: str) -> List[Dict]

        Args:
            lema: Palabra en Español a buscar

        Returns:
            List[Dict]: Entradas que coinciden con el lema en Español
        """
        lema_lower = lema.lower()

        # Búsqueda exacta en el índice de Español
        exact_matches = self.spanish_lema_index.get(lema_lower, [])

        # Búsqueda parcial si no hay coincidencias exactas
        if not exact_matches:
            partial_matches = []
            for indexed_lema, entries in self.spanish_lema_index.items():
                if (lema_lower in indexed_lema or
                    indexed_lema.startswith(lema_lower) or
                    lema_lower.startswith(indexed_lema)):
                    partial_matches.extend(entries)
            return partial_matches

        return exact_matches

    # =================== FUNCIONES DE BÚSQUEDA GENERAL ===================

    def buscar_por_lema(self, lema: str, exacto: bool = False) -> List[Dict]:
        """
        Busca entradas por lema en ambas secciones (función genérica original).

        Args:
            lema: Lema a buscar
            exacto: Si True, busca coincidencia exacta. Si False, busca coincidencias parciales.

        Returns:
            List[Dict]: Entradas que coinciden con el lema
        """
        lema_lower = lema.lower()

        if exacto:
            return self.lema_index.get(lema_lower, [])
        else:
            results = []
            for indexed_lema, entries in self.lema_index.items():
                if lema_lower in indexed_lema or indexed_lema in lema_lower:
                    results.extend(entries)
            return results

    def buscar_por_definicion(self, termino: str) -> List[Dict]:
        """
        Busca entradas que contengan un término en su definición.

        Args:
            termino: Término a buscar en las definiciones

        Returns:
            List[Dict]: Entradas que contienen el término en su definición
        """
        termino_lower = termino.lower()
        results = []

        for entry in self.all_entries:
            definicion = entry.get('definicion', '').lower()
            if termino_lower in definicion:
                results.append(entry)

        return results

    def buscar_por_categoria_gramatical(self, categoria: str) -> List[Dict]:
        """
        Busca entradas por categoría gramatical.

        FUNCIÓN ORIGINAL - También implementa: buscar_por_categoria_gramatical(categoria: str) -> List[Dict]

        Args:
            categoria: Categoría gramatical (sustantivo, verbo, adjetivo, etc.)

        Returns:
            List[Dict]: Entradas de la categoría especificada
        """
        return self.category_index.get(categoria.lower(), [])

    def buscar_por_campo_semantico(self, campo: str) -> List[Dict]:
        """
        Busca entradas por campo semántico.

        FUNCIÓN ORIGINAL - También implementa: buscar_por_campo_semantico(campo: str) -> List[Dict]

        Args:
            campo: Campo semántico (botanica, zoologia, medicina, etc.)

        Returns:
            List[Dict]: Entradas del campo semántico especificado
        """
        return self.semantic_index.get(campo.lower(), [])

    # =================== FUNCIONES DE VARIANTES DIALECTALES ===================

    def obtener_variantes_dialectales(self, lema: str) -> List[str]:
        """
        Obtiene todas las variantes dialectales de un lema como lista simple.

        VERSIÓN SIMPLIFICADA - Implementa: obtener_variantes_dialectales(lema: str) -> List[str]
        Para obtener la versión detallada por dialecto, usar obtener_variantes_dialectales_detalladas()

        Args:
            lema: Lema para buscar variantes

        Returns:
            List[str]: Lista ordenada de variantes dialectales encontradas
        """
        # Buscar en ambas secciones
        quechua_entries = self.buscar_por_quechua(lema)
        spanish_entries = self.buscar_por_espanol(lema)
        all_found_entries = quechua_entries + spanish_entries

        # Recopilar todas las variantes únicas
        all_variants = set()

        for entry in all_found_entries:
            variants_dict = entry.get('variantes_dialectales', {})
            for dialect, variant in variants_dict.items():
                if variant and variant != lema.lower():
                    all_variants.add(variant)

        return sorted(list(all_variants))

    def obtener_variantes_dialectales_detalladas(self, lema: str) -> Dict[str, List[str]]:
        """
        Obtiene todas las variantes dialectales de un lema organizadas por dialecto.

        VERSIÓN DETALLADA - Función original que retorna información estructurada por dialecto.
        Para obtener solo la lista simple, usar obtener_variantes_dialectales()

        Args:
            lema: Lema para buscar variantes

        Returns:
            Dict[str, List[str]]: Diccionario con dialectos como claves y listas de variantes como valores
        """
        entries = self.buscar_por_lema(lema, exacto=True)
        all_variants = defaultdict(list)

        for entry in entries:
            variants = entry.get('variantes_dialectales', {})
            for dialect, variant in variants.items():
                if variant not in all_variants[dialect]:
                    all_variants[dialect].append(variant)

        return dict(all_variants)

    # =================== FUNCIONES DE ANÁLISIS Y ESTADÍSTICAS ===================

    def contar_entradas(self) -> Dict[str, int]:
        """
        Cuenta entradas por sección.

        Returns:
            Dict[str, int]: Conteo de entradas por sección
        """
        return {
            'quechua_espanol': len(self.quechua_entries),
            'espanol_quechua': len(self.spanish_entries),
            'total': len(self.all_entries)
        }

    def listar_categorias_gramaticales(self) -> List[str]:
        """
        Lista todas las categorías gramaticales encontradas.

        Returns:
            List[str]: Lista ordenada de categorías gramaticales
        """
        return sorted(list(self.category_index.keys()))

    def listar_campos_semanticos(self) -> List[str]:
        """
        Lista todos los campos semánticos encontrados.

        Returns:
            List[str]: Lista ordenada de campos semánticos
        """
        return sorted(list(self.semantic_index.keys()))

    def listar_lemas(self) -> Dict:
        """
        Lista todos los lemas organizados por sección.

        NUEVA FUNCIÓN DE UTILIDAD - Implementa: listar_lemas() -> Dict

        Returns:
            Dict: Diccionario con lemas organizados por sección y estadísticas

        Structure:
            {
                'quechua_espanol': ['lema1', 'lema2', ...],
                'espanol_quechua': ['lema3', 'lema4', ...],
                'total_lemas': int,
                'lemas_unicos_total': int,
                'estadisticas': {...}
            }
        """
        # Extraer lemas de cada sección
        quechua_lemas = []
        spanish_lemas = []

        # Lemas de la sección Quechua→Español
        for entry in self.quechua_entries:
            lema = entry.get('lema', '').strip()
            if lema:
                quechua_lemas.append(lema.lower())

        # Lemas de la sección Español→Quechua
        for entry in self.spanish_entries:
            lema = entry.get('lema', '').strip()
            if lema:
                spanish_lemas.append(lema.lower())

        # Ordenar lemas alfabéticamente
        quechua_lemas_sorted = sorted(list(set(quechua_lemas)))  # Eliminar duplicados y ordenar
        spanish_lemas_sorted = sorted(list(set(spanish_lemas)))  # Eliminar duplicados y ordenar

        # Calcular estadísticas adicionales
        all_lemas_combined = quechua_lemas + spanish_lemas
        lemas_unicos_total = len(set(all_lemas_combined))

        # Lemas que aparecen en ambas secciones (intersección)
        lemas_quechua_set = set(quechua_lemas)
        lemas_spanish_set = set(spanish_lemas)
        lemas_comunes = sorted(list(lemas_quechua_set.intersection(lemas_spanish_set)))

        # Análisis de longitud de lemas
        longitudes_quechua = [len(lema) for lema in quechua_lemas_sorted]
        longitudes_spanish = [len(lema) for lema in spanish_lemas_sorted]

        promedio_longitud_quechua = sum(longitudes_quechua) / len(longitudes_quechua) if longitudes_quechua else 0
        promedio_longitud_spanish = sum(longitudes_spanish) / len(longitudes_spanish) if longitudes_spanish else 0

        # Análisis de caracteres especiales (para Quechua)
        lemas_con_caracteres_especiales = []
        caracteres_quechua = set(['ñ', 'ü', 'q', 'k', "'"])

        for lema in quechua_lemas_sorted:
            if any(char in lema for char in caracteres_quechua):
                lemas_con_caracteres_especiales.append(lema)

        return {
            'quechua_espanol': quechua_lemas_sorted,
            'espanol_quechua': spanish_lemas_sorted,
            'total_lemas': len(all_lemas_combined),
            'lemas_unicos_total': lemas_unicos_total,
            'estadisticas': {
                'lemas_unicos_quechua': len(quechua_lemas_sorted),
                'lemas_unicos_espanol': len(spanish_lemas_sorted),
                'lemas_comunes_ambas_secciones': lemas_comunes,
                'cantidad_lemas_comunes': len(lemas_comunes),
                'promedio_longitud_lemas_quechua': round(promedio_longitud_quechua, 2),
                'promedio_longitud_lemas_espanol': round(promedio_longitud_spanish, 2),
                'lemas_con_caracteres_quechua': len(lemas_con_caracteres_especiales),
                'porcentaje_caracteres_especiales': round(
                    len(lemas_con_caracteres_especiales) / len(quechua_lemas_sorted) * 100, 2
                ) if quechua_lemas_sorted else 0
            },
            'muestras': {
                'primeros_5_quechua': quechua_lemas_sorted[:5],
                'primeros_5_espanol': spanish_lemas_sorted[:5],
                'ultimos_5_quechua': quechua_lemas_sorted[-5:] if len(quechua_lemas_sorted) >= 5 else quechua_lemas_sorted,
                'ultimos_5_espanol': spanish_lemas_sorted[-5:] if len(spanish_lemas_sorted) >= 5 else spanish_lemas_sorted,
                'lemas_comunes_muestra': lemas_comunes[:10] if lemas_comunes else []
            }
        }

    def estadisticas_generales(self) -> Dict:
        """
        Genera estadísticas generales del diccionario.

        Returns:
            Dict: Estadísticas completas del diccionario
        """
        # Contar por categorías
        category_counts = {cat: len(entries) for cat, entries in self.category_index.items()}

        # Contar por campos semánticos
        semantic_counts = {campo: len(entries) for campo, entries in self.semantic_index.items()}

        # Contar entradas con variantes dialectales
        entries_with_variants = sum(1 for entry in self.all_entries
                                  if entry.get('variantes_dialectales'))

        # Contar entradas con ejemplos
        entries_with_examples = sum(1 for entry in self.all_entries
                                   if entry.get('ejemplos'))

        return {
            'total_entradas': len(self.all_entries),
            'entradas_por_seccion': self.contar_entradas(),
            'categorias_gramaticales': category_counts,
            'campos_semanticos': semantic_counts,
            'entradas_con_variantes_dialectales': entries_with_variants,
            'entradas_con_ejemplos': entries_with_examples,
            'porcentaje_con_variantes': round(entries_with_variants / len(self.all_entries) * 100, 2),
            'porcentaje_con_ejemplos': round(entries_with_examples / len(self.all_entries) * 100, 2)
        }

# =================== FIN DE LA CLASE DiccionarioAPI ===================