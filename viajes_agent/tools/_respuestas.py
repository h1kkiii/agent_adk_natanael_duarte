"""Helpers para devolver siempre el mismo formato de respuesta desde las tools."""


def ok(mensaje: str, **datos) -> dict:
    return {"status": "ok", "mensaje": mensaje, **datos}


def error(mensaje: str) -> dict:
    return {"status": "error", "mensaje": mensaje}


def vacio(mensaje: str) -> dict:
    return {"status": "empty", "mensaje": mensaje}


def es_entero(valor) -> bool:
    # bool es subclase de int: True no debe valer como 1.
    if isinstance(valor, bool):
        return False
    return isinstance(valor, int) or (isinstance(valor, float) and valor.is_integer())


def es_numero(valor) -> bool:
    return not isinstance(valor, bool) and isinstance(valor, (int, float))
