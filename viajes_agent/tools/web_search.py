from ddgs import DDGS

from ._respuestas import error, es_entero, ok, vacio

TIMEOUT = 10


def web_search(query: str, max_results: int = 5) -> dict:
    """Busca información en internet (DuckDuckGo).

    Usá esta herramienta para todo lo que NO sea clima ni cotización de
    monedas: recomendaciones de qué ver o hacer en un destino, requisitos de
    viaje (visas, documentos, vacunas), mejores épocas para viajar,
    transporte, etc. NO la uses para pronósticos (usá get_weather) ni para
    convertir monedas (usá convert_currency).

    Args:
        query: Texto a buscar, claro y específico. Ejemplos: "qué ver en
            Lisboa 3 días", "requisitos para viajar a España desde Argentina".
        max_results: Cantidad de resultados, entre 1 y 10 (por defecto 5).

    Returns:
        Un diccionario con "status" ("ok", "error" o "empty") y "mensaje".
        Si es "ok" incluye "resultados", una lista con "titulo", "resumen"
        y "url" de cada resultado.
    """
    if not isinstance(query, str) or not query.strip():
        return error("La búsqueda está vacía. Pedile al usuario qué quiere buscar.")
    if not es_entero(max_results):
        return error("El argumento 'max_results' debe ser un número entero entre 1 y 10.")
    max_results = int(max_results)
    if not 1 <= max_results <= 10:
        return error(f"El argumento 'max_results' debe estar entre 1 y 10 (recibido: {max_results}).")

    consulta = query.strip()
    try:
        crudos = DDGS(timeout=TIMEOUT).text(consulta, max_results=max_results)
    except Exception as e:
        # ddgs usa excepciones propias; "sin resultados" se reporta como vacío y el resto como error.
        if "No results found" in str(e):
            return vacio(f"No se encontraron resultados para '{consulta}'. Probá con otras palabras.")
        return error(f"No se pudo completar la búsqueda: {e}")

    resultados = [
        {"titulo": r.get("title", ""), "resumen": r.get("body", ""), "url": r.get("href", "")}
        for r in (crudos or [])
    ]
    if not resultados:
        return vacio(f"No se encontraron resultados para '{consulta}'. Probá con otras palabras.")
    return ok(f"Se encontraron {len(resultados)} resultado(s).", resultados=resultados)
