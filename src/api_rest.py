from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request


def crear_api(conectar):
    api = Blueprint("api", __name__, url_prefix="/api")

    def serializar_vuelo(vuelo):
        return {
            "id": vuelo[0],
            "fecha": vuelo[1].isoformat(),
            "matricula": vuelo[2],
            "desde": vuelo[3],
            "hasta": vuelo[4],
            "horas_vuelo": float(vuelo[5])
        }

    def validar_vuelo(datos):
        if not isinstance(datos, dict):
            raise ValueError("Se requiere un objeto JSON")

        campos = ("fecha", "matricula", "desde", "hasta", "horas_vuelo")

        if any(campo not in datos for campo in campos):
            raise ValueError("Faltan campos obligatorios")

        try:
            fecha = date.fromisoformat(datos["fecha"])
        except (TypeError, ValueError):
            raise ValueError("La fecha debe tener formato AAAA-MM-DD")

        matricula = datos["matricula"]
        if not isinstance(matricula, str):
            raise ValueError("La matrícula debe ser un texto")

        matricula = matricula.strip().upper()

        letras = matricula[3:]
        if (
            not matricula.startswith("LV-")
            or len(letras) != 3
            or not letras.isascii()
            or not letras.isalpha()
        ):
            raise ValueError("La matrícula debe tener formato LV-XXX")

        aeropuertos = []
        for campo in ("desde", "hasta"):
            valor = datos[campo]
            if not isinstance(valor, str):
                raise ValueError(f"El campo {campo} debe ser un texto")

            valor = valor.strip().upper()
            if not valor or len(valor) > 10:
                raise ValueError(f"El campo {campo} debe tener entre 1 y 10 caracteres")

            aeropuertos.append(valor)

        try:
            if isinstance(datos["horas_vuelo"], bool):
                raise ValueError()
            horas = Decimal(str(datos["horas_vuelo"]))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("Las horas de vuelo deben ser numéricas")

        if not horas.is_finite() or horas <= 0 or horas > Decimal("9999.99"):
            raise ValueError("Las horas de vuelo deben estar entre 0.01 y 9999.99")

        if horas != horas.quantize(Decimal("0.01")):
            raise ValueError("Las horas de vuelo admiten hasta dos decimales")

        return (fecha, matricula, aeropuertos[0], aeropuertos[1], horas)

    def leer_json():
        datos = request.get_json(silent=True)
        return validar_vuelo(datos)

    @api.get("/vuelos")
    def listar_vuelos():
        with conectar() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    SELECT id, fecha, matricula, desde, hasta, horas_vuelo
                    FROM vuelos
                    WHERE NOT is_deleted
                    ORDER BY fecha DESC, id DESC
                """)
                vuelos = cursor.fetchall()

        return jsonify([serializar_vuelo(vuelo) for vuelo in vuelos])

    @api.get("/vuelos/<int:id>")
    def obtener_vuelo(id):
        with conectar() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    SELECT id, fecha, matricula, desde, hasta, horas_vuelo
                    FROM vuelos
                    WHERE id = %s AND NOT is_deleted
                """, (id,))
                vuelo = cursor.fetchone()

        if vuelo is None:
            return jsonify({"error": "Vuelo no encontrado"}), 404

        return jsonify(serializar_vuelo(vuelo))

    @api.post("/vuelos")
    def crear_vuelo():
        try:
            valores = leer_json()
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        with conectar() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO vuelos
                        (fecha, matricula, desde, hasta, horas_vuelo)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, fecha, matricula, desde, hasta, horas_vuelo
                """, valores)
                vuelo = cursor.fetchone()

        return jsonify(serializar_vuelo(vuelo)), 201

    @api.put("/vuelos/<int:id>")
    def actualizar_vuelo(id):
        try:
            valores = leer_json()
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        with conectar() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    UPDATE vuelos
                    SET fecha = %s, matricula = %s, desde = %s,
                        hasta = %s, horas_vuelo = %s
                    WHERE id = %s AND NOT is_deleted
                    RETURNING id, fecha, matricula, desde, hasta, horas_vuelo
                """, (*valores, id))
                vuelo = cursor.fetchone()

        if vuelo is None:
            return jsonify({"error": "Vuelo no encontrado"}), 404

        return jsonify(serializar_vuelo(vuelo))

    @api.delete("/vuelos/<int:id>")
    def eliminar_vuelo(id):
        with conectar() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    UPDATE vuelos
                    SET is_deleted = TRUE
                    WHERE id = %s AND NOT is_deleted
                    RETURNING id
                """, (id,))
                eliminado = cursor.fetchone()

        if eliminado is None:
            return jsonify({"error": "Vuelo no encontrado"}), 404

        return "", 204

    return api