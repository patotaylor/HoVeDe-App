CREATE TABLE IF NOT EXISTS vuelos (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    matricula VARCHAR(20) NOT NULL,
    desde VARCHAR(10) NOT NULL,
    hasta VARCHAR(10) NOT NULL,
    horas_vuelo NUMERIC(6,2) NOT NULL CHECK (horas_vuelo > 0),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);