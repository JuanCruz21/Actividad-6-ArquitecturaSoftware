"""Datos de demostración. Solo se cargan si la base de datos está vacía.

Credenciales de prueba (entorno local):
    recepcion@labcloud.test / recepcion123
    analista@labcloud.test  / analista123
    admin@labcloud.test     / admin123
"""

import sqlite3

from labcloud.datos.repositorios import RepositorioInventario, RepositorioPacientes, RepositorioUsuarios
from labcloud.negocio.eventos import SujetoEventos
from labcloud.negocio.seguridad import hash_password

USUARIOS = [
    ("Laura Gómez", "recepcion@labcloud.test", "recepcion123", "recepcion"),
    ("Andrés Pardo", "analista@labcloud.test", "analista123", "analista"),
    ("Sofía Herrera", "admin@labcloud.test", "admin123", "administrador"),
]

PACIENTES = [
    ("1012345678", "Camila", "Rodríguez Peña", "1990-04-12", "3001234567", "camila.rp@correo.test"),
    ("80123456", "Jorge", "Martínez Ruiz", "1975-09-30", "3109876543", None),
    ("52987654", "Valentina", "López Castro", "1988-01-22", "3205554433", "vale.lc@correo.test"),
    ("1098765432", "Mateo", "Suárez Díaz", "2001-06-05", "3014445566", None),
    ("39456123", "Lucía", "Fernández Mora", "1962-11-18", "3157778899", None),
]

INVENTARIO = [
    ("Reactivo hematología", "HEM-2026-07", 40, 10, "pruebas", "2027-03-31"),
    ("Reactivo glucosa", "GLU-2026-05", 25, 8, "pruebas", "2027-01-15"),
    ("Reactivo colesterol", "COL-2026-04", 9, 8, "pruebas", "2026-12-20"),
    ("Reactivo creatinina", "CRE-2026-06", 30, 8, "pruebas", "2027-02-28"),
    ("Reactivo TSH", "TSH-2026-03", 12, 5, "pruebas", "2026-11-30"),
    ("Tiras reactivas de orina", "URI-2026-08", 50, 15, "tiras", "2027-06-30"),
    ("Tubos EDTA 4 mL", "TUB-2026-02", 180, 50, "unidades", "2028-01-31"),
]

ORDENES = [
    # (índice paciente, exámenes, prioridad, avance: 0=pendiente, 1=en proceso, 2=procesada)
    (0, ["hemograma", "glucosa"], "normal", 2),
    (1, ["colesterol", "creatinina"], "urgente", 1),
    (2, ["uroanalisis"], "normal", 0),
    (3, ["hemograma", "tsh"], "normal", 0),
    (4, ["glucosa"], "urgente", 0),
]

VALORES_DEMO = {"hemograma": "13.8", "glucosa": "92", "colesterol": "185", "creatinina": "0.9",
                "tsh": "2.1", "uroanalisis": "Normal"}


def cargar_datos_demo(conn: sqlite3.Connection) -> None:
    from labcloud.negocio.servicios import ServicioMuestras, ServicioOrdenes

    usuarios = RepositorioUsuarios(conn)
    if usuarios.contar() > 0:
        return
    ids = {rol: usuarios.crear(nombre, correo, hash_password(pw), rol) for nombre, correo, pw, rol in USUARIOS}

    pacientes = RepositorioPacientes(conn)
    paciente_ids = [
        pacientes.crear(dict(zip(("documento", "nombres", "apellidos", "fecha_nacimiento", "telefono", "correo"), p)))
        for p in PACIENTES
    ]
    inventario = RepositorioInventario(conn)
    for item in INVENTARIO:
        inventario.crear(dict(zip(("nombre", "lote", "cantidad", "minimo", "unidad", "vencimiento"), item)))

    silencioso = SujetoEventos()  # sin observadores: la carga inicial no genera notificaciones
    ordenes = ServicioOrdenes(conn, silencioso)
    muestras = ServicioMuestras(conn, silencioso)
    for indice, examenes, prioridad, avance in ORDENES:
        orden = ordenes.crear(paciente_ids[indice], examenes, prioridad, ids["recepcion"])
        for muestra in orden["muestras"]:
            if avance >= 1:
                muestras.iniciar_procesamiento(muestra["id"])
            if avance >= 2:
                valores = [{"examen": e, "valor": VALORES_DEMO[e]} for e in muestra["examenes"].split(",")]
                muestras.registrar_resultados(muestra["id"], valores, ids["analista"])
    conn.commit()
