import json
import os
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def buscar_vuelo(numero, fecha):
    clave = os.getenv("RAPIDAPI_KEY")
    if not clave:
        raise ValueError("Falta configurar RAPIDAPI_KEY")

    numero = numero.strip().upper().replace(" ", "")
    url = ("https://aerodatabox.p.rapidapi.com/flights/number/"
           f"{quote(numero)}/{quote(fecha)}")
    solicitud = Request(url, headers={
        "X-RapidAPI-Key": clave,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    })

    try:
        with urlopen(solicitud, timeout=10) as respuesta:
            vuelos = json.load(respuesta)
    except (HTTPError, URLError, TimeoutError) as error:
        raise ValueError(f"No se pudo consultar AeroDataBox: {error}") from error

    if not vuelos:
        raise ValueError("No se encontró el vuelo para esa fecha")

    try:
        vuelo = vuelos[0]
        horario = vuelo["departure"]["scheduledTime"]["local"]
        etd = datetime.fromisoformat(horario).astimezone(
            timezone(timedelta(hours=-3))
        ).replace(tzinfo=None)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("La API no devolvió un horario programado válido") from error

    return {
        "numero": vuelo.get("number", numero),
        "fecha": fecha,
        "matricula": (vuelo.get("aircraft") or {}).get("reg") or "No disponible",
        "desde": (vuelo.get("departure") or {}).get("airport", {}).get("icao") or "—",
        "hasta": (vuelo.get("arrival") or {}).get("airport", {}).get("icao") or "—",
        "etd": etd,
        "checkin": etd - timedelta(hours=1)
    }
