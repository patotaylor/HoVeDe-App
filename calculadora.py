from datetime import datetime, time, timedelta
from math import ceil


def calcular_tiempos(checkin, etd, eta):
    if not checkin <= etd < eta:
        raise ValueError("Los horarios deben estar en orden cronológico")

    fin_tsv = eta + timedelta(minutes=30)
    duracion_tsv = fin_tsv - checkin
    inicio_descanso = fin_tsv + timedelta(minutes=45)

    return {
        "fin_tsv": fin_tsv,
        "duracion_tsv": duracion_tsv,
        "inicio_descanso": inicio_descanso
    }
    
# Anexo VII: (TSV máximo, descanso normal, descanso nocturno interrumpido)
TABLA_DESCANSOS = [
    (6, 8, 10),
    (8, 10, 12),
    (9, 11, 13),
    (10, 12, 14),
    (11, 13, 15),
    (12, 14, 16),
    (13, 15, 16),
    (14, 16, 17),
    (15, 17, 17),
    (16, 18, 18),
    (17, 20, 20),
    (18, 22, 22),
    (19, 24, 24),
    (20, 26, 26),
    (21, 28, 28),
    (22, 30, 30),
    (23, 34, 34),
    (float("inf"), 36, 36)
]

def buscar_descansos(duracion_tsv):
    horas = duracion_tsv.total_seconds() / 3600

    for limite, normal, interrumpido in TABLA_DESCANSOS:
        if horas <= limite:
            return normal, interrumpido

def minutos_nocturnos(inicio, fin):
    total = 0
    dia = inicio.date()

    while dia <= fin.date():
        desde = datetime.combine(dia, time(0, 0))
        hasta = datetime.combine(dia, time(6, 0))

        total += max(
            0,
            (min(fin, hasta) - max(inicio, desde)).total_seconds() / 60
        )
        dia += timedelta(days=1)

    return total


def ultimo_aterrizaje(checkin):
    for minutos in range(780, 29, -1):
        fin_tsv = checkin + timedelta(minutes=minutos)
        nocturnos = minutos_nocturnos(checkin, fin_tsv)
        reduccion = ceil(nocturnos / 60) * 30

        if minutos + reduccion <= 780:
            return fin_tsv - timedelta(minutes=30)

def tiene_noche_completa(inicio, fin):
    dia = inicio.date()

    while dia <= fin.date():
        noche_inicio = datetime.combine(dia, time(0, 0))
        noche_fin = datetime.combine(dia, time(6, 0))

        if inicio <= noche_inicio and fin >= noche_fin:
            return True

        dia += timedelta(days=1)

    return False


def calcular_descanso(checkin, fin_tsv, inicio_descanso):
    duracion_tsv = fin_tsv - checkin
    normal, interrumpido = buscar_descansos(duracion_tsv)

    fin_normal = inicio_descanso + timedelta(hours=normal)

    if tiene_noche_completa(inicio_descanso, fin_normal):
        horas = normal
        tipo = "Normal"
    else:
        horas = interrumpido
        tipo = "Nocturno interrumpido"

        if minutos_nocturnos(checkin, fin_tsv) > 180:
            horas += 2

    proxima_presentacion = inicio_descanso + timedelta(hours=horas)

    return tipo, horas, proxima_presentacion