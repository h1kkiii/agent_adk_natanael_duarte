import requests

from ._respuestas import error, es_entero, ok, vacio

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10


def get_weather(city: str, days: int = 3) -> dict:
    """Obtiene el clima actual y el pronóstico diario de una ciudad.

    Usá esta herramienta cuando el usuario pregunte por el clima, la
    temperatura, si va a llover o qué pronóstico hay en una ciudad (por
    ejemplo para decidir qué ropa llevar a un viaje). NO sirve para
    cotizaciones de monedas ni para recomendaciones turísticas.

    Args:
        city: Nombre de la ciudad, solo el nombre. Ejemplos: "Madrid",
            "Buenos Aires", "Lisboa".
        days: Cantidad de días de pronóstico, entre 1 y 7 (por defecto 3).
            Para "esta semana" usar 7.

    Returns:
        Un diccionario con "status" ("ok", "error" o "empty") y "mensaje".
        Si es "ok" incluye "ciudad", "pais", "temperatura_actual_c" y
        "pronostico", una lista con "fecha", "temp_min_c", "temp_max_c" y
        "prob_lluvia_pct" por día.
    """
    if not isinstance(city, str) or not city.strip():
        return error("Falta el nombre de la ciudad. Pedile al usuario que indique una ciudad.")
    if not es_entero(days):
        return error("El argumento 'days' debe ser un número entero entre 1 y 7.")
    days = int(days)
    if not 1 <= days <= 7:
        return error(f"El argumento 'days' debe estar entre 1 y 7 (recibido: {days}).")

    try:
        geo = requests.get(
            GEOCODING_URL,
            params={"name": city.strip(), "count": 1, "language": "es", "format": "json"},
            timeout=TIMEOUT,
        )
        geo.raise_for_status()
        resultados = geo.json().get("results") or []
        if not resultados:
            return vacio(f"No se encontró ninguna ciudad llamada '{city.strip()}'. Verificá el nombre.")
        lugar = resultados[0]

        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lugar["latitude"],
                "longitude": lugar["longitude"],
                "current": "temperature_2m",
                "daily": "temperature_2m_min,temperature_2m_max,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": days,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        datos = resp.json()
        diario = datos.get("daily") or {}
        fechas = diario.get("time") or []
        if not fechas:
            return vacio(f"El servicio no devolvió pronóstico para '{lugar.get('name', city)}'.")

        pronostico = [
            {
                "fecha": fechas[i],
                "temp_min_c": diario["temperature_2m_min"][i],
                "temp_max_c": diario["temperature_2m_max"][i],
                "prob_lluvia_pct": diario["precipitation_probability_max"][i],
            }
            for i in range(len(fechas))
        ]
        nombre = lugar.get("name", city.strip())
        return ok(
            f"Pronóstico de {days} día(s) para {nombre}.",
            ciudad=nombre,
            pais=lugar.get("country", "desconocido"),
            temperatura_actual_c=(datos.get("current") or {}).get("temperature_2m"),
            pronostico=pronostico,
        )
    except requests.Timeout:
        return error("El servicio del clima tardó demasiado en responder. Probá de nuevo en un rato.")
    except requests.RequestException as e:
        return error(f"No se pudo consultar el servicio del clima: {e}")
    except (KeyError, IndexError, ValueError, TypeError) as e:
        return error(f"Respuesta inesperada del servicio del clima: {e}")
