import math
import re

import requests

from ._respuestas import error, es_numero, ok, vacio

RATES_URL = "https://open.er-api.com/v6/latest/{base}"
TIMEOUT = 10
CODIGO_ISO = re.compile(r"^[A-Z]{3}$")


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convierte un monto de una moneda a otra usando la cotización actual.

    Usá esta herramienta cuando el usuario pregunte cuánto equivale un monto
    en otra moneda o quiera saber una cotización (por ejemplo para presupuestar
    un viaje). Hay que pasar códigos ISO de 3 letras: dólar = USD, euro = EUR,
    peso argentino = ARS, real = BRL, libra = GBP. NO sirve para clima ni para
    buscar información turística.

    Args:
        amount: Monto a convertir, mayor a 0. Ejemplo: 200.
        from_currency: Código ISO de la moneda de origen. Ejemplo: "EUR".
        to_currency: Código ISO de la moneda de destino. Ejemplo: "ARS".

    Returns:
        Un diccionario con "status" ("ok", "error" o "empty") y "mensaje".
        Si es "ok" incluye "monto", "de", "a", "tasa", "resultado" y
        "actualizado" (fecha de la cotización).
    """
    if not es_numero(amount) or not math.isfinite(amount):
        return error("El argumento 'amount' debe ser un número válido mayor a 0.")
    if amount <= 0:
        return error(f"El monto debe ser mayor a 0 (recibido: {amount}).")
    for nombre, valor in (("from_currency", from_currency), ("to_currency", to_currency)):
        if not isinstance(valor, str) or not valor.strip():
            return error(f"Falta el argumento '{nombre}'. Pedile al usuario la moneda.")

    origen = from_currency.strip().upper()
    destino = to_currency.strip().upper()
    for codigo in (origen, destino):
        if not CODIGO_ISO.match(codigo):
            return error(
                f"'{codigo}' no es un código de moneda válido. "
                "Usá códigos ISO de 3 letras, por ejemplo USD, EUR o ARS."
            )

    try:
        resp = requests.get(RATES_URL.format(base=origen), timeout=TIMEOUT)
        # Con una base inexistente la API responde un JSON con result="error" (a veces con HTTP 404),
        # así que se lee el JSON antes de mirar el status HTTP.
        try:
            datos = resp.json()
        except ValueError:
            resp.raise_for_status()
            return error("Respuesta inesperada del servicio de cotizaciones.")
        if datos.get("result") != "success":
            if datos.get("error-type") == "unsupported-code" or resp.status_code == 404:
                return vacio(f"La moneda '{origen}' no está soportada por el servicio de cotizaciones.")
            return error(f"El servicio de cotizaciones devolvió un error: {datos.get('error-type', resp.status_code)}")

        tasa = (datos.get("rates") or {}).get(destino)
        if tasa is None:
            return vacio(f"La moneda '{destino}' no está soportada por el servicio de cotizaciones.")
        resultado = round(amount * tasa, 2)
        return ok(
            f"{amount} {origen} = {resultado} {destino}",
            monto=amount,
            de=origen,
            a=destino,
            tasa=tasa,
            resultado=resultado,
            actualizado=datos.get("time_last_update_utc"),
        )
    except requests.Timeout:
        return error("El servicio de cotizaciones tardó demasiado en responder. Probá de nuevo en un rato.")
    except requests.RequestException as e:
        return error(f"No se pudo consultar el servicio de cotizaciones: {e}")
    except (KeyError, ValueError, TypeError) as e:
        return error(f"Respuesta inesperada del servicio de cotizaciones: {e}")
