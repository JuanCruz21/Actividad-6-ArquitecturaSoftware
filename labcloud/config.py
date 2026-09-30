"""Configuración del monolito (rutas de base de datos y del frontend compilado)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = Path(os.getenv("LABCLOUD_DB", BASE_DIR / "labcloud.db"))
FRONTEND_DIR = Path(os.getenv("LABCLOUD_FRONTEND", BASE_DIR / "frontend" / "out"))
HOST = os.getenv("LABCLOUD_HOST", "127.0.0.1")
PORT = int(os.getenv("LABCLOUD_PORT", "8000"))
DURACION_SESION_HORAS = 12
