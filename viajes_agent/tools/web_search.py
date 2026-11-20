import time

from ddgs import DDGS

from ._respuestas import error, es_entero, ok, vacio

TIMEOUT = 10
INTENTOS = 3
PAUSA_REINTENTO = 1.5


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
    crudos = None
    ultimo_error = None
    # ddgs consulta buscadores externos que fallan o limitan de forma intermitente
    # ("No results found" o cortes de conexión con la misma consulta), por eso se reintenta.
    for intento in range(INTENTOS):
        if intento:
            time.sleep(PAUSA_REINTENTO)
        try:
            crudos = DDGS(timeout=TIMEOUT).text(consulta, max_results=max_results)
        except Exception as e:
            ultimo_error = e
            continue
        if crudos:
            ultimo_error = None
            break

    if not crudos and ultimo_error is not None and "No results found" not in str(ultimo_error):
        return error(f"No se pudo completar la búsqueda: {ultimo_error}")

    resultados = [
        {"titulo": r.get("title", ""), "resumen": r.get("body", ""), "url": r.get("href", "")}
        for r in (crudos or [])
    ]
    if not resultados:
        return vacio(f"No se encontraron resultados para '{consulta}'. Probá con otras palabras.")
    return ok(f"Se encontraron {len(resultados)} resultado(s).", resultados=resultados)
