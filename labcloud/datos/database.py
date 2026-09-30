"""Conexión y esquema de la base de datos SQLite."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from labcloud import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL,
    correo        TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol           TEXT NOT NULL,
    activo        INTEGER NOT NULL DEFAULT 1,
    creado_en     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sesiones (
    token      TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    expira_en  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pacientes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    documento        TEXT NOT NULL UNIQUE,
    nombres          TEXT NOT NULL,
    apellidos        TEXT NOT NULL,
    fecha_nacimiento TEXT,
    telefono         TEXT,
    correo           TEXT,
    creado_en        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ordenes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo      TEXT UNIQUE,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
    examenes    TEXT NOT NULL,
    prioridad   TEXT NOT NULL DEFAULT 'normal',
    estado      TEXT NOT NULL DEFAULT 'registrada',
    creado_por  INTEGER REFERENCES usuarios(id),
    creado_en   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS muestras (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo       TEXT UNIQUE,
    orden_id     INTEGER NOT NULL REFERENCES ordenes(id),
    tipo         TEXT NOT NULL,
    examenes     TEXT NOT NULL,
    estado       TEXT NOT NULL DEFAULT 'pendiente',
    creado_en    TEXT NOT NULL DEFAULT (datetime('now')),
    iniciada_en  TEXT,
    procesada_en TEXT
);

CREATE TABLE IF NOT EXISTS resultados (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    muestra_id    INTEGER NOT NULL REFERENCES muestras(id),
    examen        TEXT NOT NULL,
    valor         TEXT NOT NULL,
    unidad        TEXT,
    referencia    TEXT,
    observaciones TEXT,
    analista_id   INTEGER REFERENCES usuarios(id),
    registrado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS inventario (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    lote        TEXT NOT NULL,
    cantidad    INTEGER NOT NULL DEFAULT 0,
    minimo      INTEGER NOT NULL DEFAULT 0,
    unidad      TEXT NOT NULL DEFAULT 'unidades',
    vencimiento TEXT
);

CREATE TABLE IF NOT EXISTS historial_navegacion (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    comando       TEXT NOT NULL,
    ruta          TEXT NOT NULL,
    registrado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS metricas_navegacion (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    prueba        TEXT NOT NULL,
    rol           TEXT NOT NULL,
    modo          TEXT NOT NULL CHECK (modo IN ('convencional', 'optimizada')),
    pasos         INTEGER NOT NULL,
    tiempo_ms     INTEGER NOT NULL,
    errores       INTEGER NOT NULL DEFAULT 0,
    recorrido     TEXT,
    usuario_id    INTEGER REFERENCES usuarios(id),
    registrado_en TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS eventos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo       TEXT NOT NULL,
    mensaje    TEXT NOT NULL,
    entidad    TEXT,
    entidad_id INTEGER,
    roles      TEXT NOT NULL,
    creado_en  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def conectar(ruta: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(ruta or config.DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar(conn: sqlite3.Connection) -> None:
    conn.executescript(ESQUEMA)
    conn.commit()


def obtener_conexion() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: una conexión por solicitud."""
    conn = conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
