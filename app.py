
import os
import psycopg
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
from calculadora import calcular_tiempos, ultimo_aterrizaje, calcular_descanso

app = Flask(__name__)

def conectar():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "hovede"),
        user=os.getenv("DB_USER", "hovede"),
        password=os.environ["DB_PASSWORD"]
    )

@app.route("/")
def inicio():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id, fecha, matricula, desde, hasta, horas_vuelo
                FROM vuelos
                WHERE NOT is_deleted
                ORDER BY fecha DESC, id DESC
            """)
            vuelos = cursor.fetchall()

    return render_template("index.html", vuelos=vuelos)

@app.route("/agregar", methods=["POST"])
def agregar():
    fecha = request.form["fecha"]
    matricula = request.form["matricula"]
    desde = request.form["desde"]
    hasta = request.form["hasta"]
    horas = request.form["horas_vuelo"]

    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vuelos (fecha, matricula, desde, hasta, horas_vuelo)
                VALUES (%s, %s, %s, %s, %s)
            """, (fecha, matricula, desde, hasta, horas))

    return redirect("/")

@app.route("/modificar/<int:id>", methods=["POST"])
def modificar(id):
    fecha = request.form["fecha"]
    matricula = request.form["matricula"]
    desde = request.form["desde"]
    hasta = request.form["hasta"]
    horas = request.form["horas_vuelo"]

    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE vuelos
                SET fecha = %s, matricula = %s, desde = %s,
                    hasta = %s, horas_vuelo = %s
                WHERE id = %s AND NOT is_deleted
            """, (fecha, matricula, desde, hasta, horas, id))

    return redirect("/")

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE vuelos SET is_deleted = TRUE WHERE id = %s",
                (id,)
            )

    return redirect("/")


@app.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    resultado = None
    error = None

    if request.method == "POST":
        try:
            checkin = datetime.fromisoformat(request.form["checkin"])
            etd = datetime.fromisoformat(request.form["etd"])
            eta = datetime.fromisoformat(request.form["eta"])

            resultado = calcular_tiempos(checkin, etd, eta)
            resultado["ultimo_aterrizaje"] = ultimo_aterrizaje(checkin)
            resultado["excede_tsv"] = eta > resultado["ultimo_aterrizaje"]
            tipo, horas, proxima = calcular_descanso(checkin,
            resultado["fin_tsv"],
            resultado["inicio_descanso"])
            resultado["tipo_descanso"] = tipo
            resultado["horas_descanso"] = horas
            resultado["proxima_presentacion"] = proxima


        except ValueError as e:
            error = str(e)

    return render_template(
        "calculadora.html",
        resultado=resultado,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)

