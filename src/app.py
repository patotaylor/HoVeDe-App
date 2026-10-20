import os
from datetime import datetime

import psycopg
from flask import Flask, abort, redirect, render_template, request, url_for

from api_vuelos import buscar_vuelo
from calculadora import calcular_descanso, calcular_tiempos, ultimo_aterrizaje

app = Flask(__name__)


def conectar():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "hovede"),
        user=os.getenv("DB_USER", "hovede"),
        password=os.environ["DB_PASSWORD"]
    )

def obtener_matricula():
    letras = request.form["matricula"].strip().upper()

    if len(letras) != 3 or not letras.isascii() or not letras.isalpha():
        abort(400, description="La matrícula debe tener exactamente 3 letras")

    return "LV-" + letras

@app.route("/")
def inicio():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, fecha, matricula, desde, hasta, horas_vuelo
                FROM vuelos WHERE NOT is_deleted
                ORDER BY fecha DESC, id DESC
            """)
            vuelos = cursor.fetchall()
    return render_template("index.html", vuelos=vuelos)


@app.route("/agregar", methods=["POST"])
def agregar():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vuelos (fecha, matricula, desde, hasta, horas_vuelo)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                request.form["fecha"], obtener_matricula(),
                request.form["desde"], request.form["hasta"],
                request.form["horas_vuelo"]
            ))
    return redirect(url_for("inicio"))


@app.route("/editar/<int:id>")
def editar(id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, fecha, matricula, desde, hasta, horas_vuelo
                FROM vuelos WHERE id = %s AND NOT is_deleted
            """, (id,))
            vuelo = cursor.fetchone()
    if vuelo is None:
        abort(404)
    return render_template("editar.html", vuelo=vuelo)


@app.route("/modificar/<int:id>", methods=["POST"])
def modificar(id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE vuelos
                SET fecha = %s, matricula = %s, desde = %s,
                    hasta = %s, horas_vuelo = %s
                WHERE id = %s AND NOT is_deleted
            """, (
                request.form["fecha"], obtener_matricula(),
                request.form["desde"], request.form["hasta"],
                request.form["horas_vuelo"], id
            ))
    return redirect(url_for("inicio"))


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE vuelos SET is_deleted = TRUE WHERE id = %s",
                (id,)
            )
    return redirect(url_for("inicio"))


# Las mismas variables se usan al buscar y al calcular: así no se borran los campos.
def campos_formulario():
    campos = {campo: request.form.get(campo, "") for campo in (
        "numero", "fecha_busqueda", "matricula", "desde", "hasta",
        "checkin_fecha", "etd_fecha", "eta_fecha"
    )}

    for nombre in ("checkin", "etd", "eta"):
        hh = request.form.get(f"{nombre}_hh", "")
        mm = request.form.get(f"{nombre}_mm", "")

        campos[f"{nombre}_hora"] = f"{hh}:{mm}" if hh and mm else ""

    return campos

def leer_fecha_hora(campos, prefijo):
    return datetime.strptime(
        f'{campos[prefijo + "_fecha"]} {campos[prefijo + "_hora"]}',
        "%Y-%m-%d %H:%M"
    )


@app.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    campos = campos_formulario() if request.method == "POST" else {}
    resultado = None
    error = None

    if request.method == "POST":
        try:
            checkin = leer_fecha_hora(campos, "checkin")
            etd = leer_fecha_hora(campos, "etd")
            eta = leer_fecha_hora(campos, "eta")
            resultado = calcular_tiempos(checkin, etd, eta)
            resultado["ultimo_aterrizaje"] = ultimo_aterrizaje(checkin)
            resultado["excede_tsv"] = eta > resultado["ultimo_aterrizaje"]
            tipo, horas, proxima = calcular_descanso(
                checkin, resultado["fin_tsv"], resultado["inicio_descanso"]
            )
            resultado["tipo_descanso"] = tipo
            resultado["horas_descanso"] = horas
            resultado["proxima_presentacion"] = proxima
        except ValueError as exc:
            error = f"Revisá los horarios ingresados: {exc}"

    return render_template("calculadora.html", campos=campos,
                           resultado=resultado, error=error)


@app.route("/buscar-vuelo", methods=["POST"])
def consultar_vuelo():
    campos = campos_formulario()
    numero = request.form.get("numero", "").strip()
    fecha = request.form.get("fecha_busqueda", "")

    try:
        if not numero or not fecha:
            raise ValueError("Ingresá el número de vuelo y la fecha")
        vuelo = buscar_vuelo(numero, fecha)
        campos.update({
            "numero": vuelo["numero"],
            "fecha_busqueda": vuelo["fecha"],
            "matricula": vuelo["matricula"],
            "desde": vuelo["desde"],
            "hasta": vuelo["hasta"],
            "checkin_fecha": vuelo["checkin"].strftime("%Y-%m-%d"),
            "checkin_hora": vuelo["checkin"].strftime("%H:%M"),
            "etd_fecha": vuelo["etd"].strftime("%Y-%m-%d"),
            "etd_hora": vuelo["etd"].strftime("%H:%M")
        })
        error = None
    except ValueError as exc:
        error = f"No se pudo cargar el vuelo: {exc}"

    return render_template("calculadora.html", campos=campos,
                           resultado=None, error=error)


if __name__ == "__main__":
    app.run(debug=True)
