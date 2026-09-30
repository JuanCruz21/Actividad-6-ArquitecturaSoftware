"""Repositorios: única puerta de acceso a las tablas SQLite."""

import sqlite3
from typing import Any


def _dict(fila: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(fila) if fila is not None else None


def _dicts(filas: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(f) for f in filas]


class Repositorio:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn


class RepositorioUsuarios(Repositorio):
    COLUMNAS = "id, nombre, correo, rol, activo, creado_en"

    def por_correo(self, correo: str) -> dict | None:
        fila = self.conn.execute("SELECT * FROM usuarios WHERE correo = ?", (correo.lower(),)).fetchone()
        return _dict(fila)

    def por_id(self, usuario_id: int) -> dict | None:
        fila = self.conn.execute(f"SELECT {self.COLUMNAS} FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return _dict(fila)

    def listar(self) -> list[dict]:
        return _dicts(self.conn.execute(f"SELECT {self.COLUMNAS} FROM usuarios ORDER BY rol, nombre").fetchall())

    def crear(self, nombre: str, correo: str, password_hash: str, rol: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO usuarios (nombre, correo, password_hash, rol) VALUES (?, ?, ?, ?)",
            (nombre, correo.lower(), password_hash, rol),
        )
        return cur.lastrowid

    def actualizar_estado(self, usuario_id: int, activo: bool) -> None:
        self.conn.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (int(activo), usuario_id))

    def contar(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]


class RepositorioSesiones(Repositorio):
    def crear(self, token: str, usuario_id: int, horas: int) -> None:
        self.conn.execute(
            "INSERT INTO sesiones (token, usuario_id, expira_en) VALUES (?, ?, datetime('now', ?))",
            (token, usuario_id, f"+{horas} hours"),
        )

    def usuario_por_token(self, token: str) -> dict | None:
        fila = self.conn.execute(
            """SELECT u.id, u.nombre, u.correo, u.rol, u.activo
               FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id
               WHERE s.token = ? AND s.expira_en > datetime('now') AND u.activo = 1""",
            (token,),
        ).fetchone()
        return _dict(fila)

    def eliminar(self, token: str) -> None:
        self.conn.execute("DELETE FROM sesiones WHERE token = ?", (token,))


class RepositorioPacientes(Repositorio):
    def listar(self, busqueda: str | None = None) -> list[dict]:
        if busqueda:
            patron = f"%{busqueda}%"
            filas = self.conn.execute(
                """SELECT * FROM pacientes
                   WHERE documento LIKE ? OR nombres LIKE ? OR apellidos LIKE ?
                   ORDER BY apellidos, nombres""",
                (patron, patron, patron),
            ).fetchall()
        else:
            filas = self.conn.execute("SELECT * FROM pacientes ORDER BY creado_en DESC, id DESC").fetchall()
        return _dicts(filas)

    def por_id(self, paciente_id: int) -> dict | None:
        return _dict(self.conn.execute("SELECT * FROM pacientes WHERE id = ?", (paciente_id,)).fetchone())

    def por_documento(self, documento: str) -> dict | None:
        return _dict(self.conn.execute("SELECT * FROM pacientes WHERE documento = ?", (documento,)).fetchone())

    def crear(self, datos: dict) -> int:
        cur = self.conn.execute(
            """INSERT INTO pacientes (documento, nombres, apellidos, fecha_nacimiento, telefono, correo)
               VALUES (:documento, :nombres, :apellidos, :fecha_nacimiento, :telefono, :correo)""",
            datos,
        )
        return cur.lastrowid

    def contar(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]


class RepositorioOrdenes(Repositorio):
    SELECT = """SELECT o.*, p.documento AS paciente_documento,
                       p.nombres || ' ' || p.apellidos AS paciente_nombre
                FROM ordenes o JOIN pacientes p ON p.id = o.paciente_id"""

    def crear(self, paciente_id: int, examenes: list[str], prioridad: str, creado_por: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO ordenes (paciente_id, examenes, prioridad, creado_por) VALUES (?, ?, ?, ?)",
            (paciente_id, ",".join(examenes), prioridad, creado_por),
        )
        orden_id = cur.lastrowid
        self.conn.execute("UPDATE ordenes SET codigo = ? WHERE id = ?", (f"ORD-{orden_id:05d}", orden_id))
        return orden_id

    def listar(self, estado: str | None = None) -> list[dict]:
        if estado:
            filas = self.conn.execute(f"{self.SELECT} WHERE o.estado = ? ORDER BY o.id DESC", (estado,)).fetchall()
        else:
            filas = self.conn.execute(f"{self.SELECT} ORDER BY o.id DESC").fetchall()
        return _dicts(filas)

    def por_id(self, orden_id: int) -> dict | None:
        return _dict(self.conn.execute(f"{self.SELECT} WHERE o.id = ?", (orden_id,)).fetchone())

    def actualizar_estado(self, orden_id: int, estado: str) -> None:
        self.conn.execute("UPDATE ordenes SET estado = ? WHERE id = ?", (estado, orden_id))

    def conteo_por_estado(self) -> dict[str, int]:
        filas = self.conn.execute("SELECT estado, COUNT(*) FROM ordenes GROUP BY estado").fetchall()
        return {f[0]: f[1] for f in filas}


class RepositorioMuestras(Repositorio):
    SELECT = """SELECT m.*, o.codigo AS orden_codigo, o.prioridad, o.paciente_id,
                       p.documento AS paciente_documento,
                       p.nombres || ' ' || p.apellidos AS paciente_nombre
                FROM muestras m
                JOIN ordenes o ON o.id = m.orden_id
                JOIN pacientes p ON p.id = o.paciente_id"""
    ORDEN = "ORDER BY CASE o.prioridad WHEN 'urgente' THEN 0 ELSE 1 END, m.id"

    def crear(self, orden_id: int, tipo: str, examenes: list[str]) -> int:
        cur = self.conn.execute(
            "INSERT INTO muestras (orden_id, tipo, examenes) VALUES (?, ?, ?)",
            (orden_id, tipo, ",".join(examenes)),
        )
        muestra_id = cur.lastrowid
        self.conn.execute("UPDATE muestras SET codigo = ? WHERE id = ?", (f"MUE-{muestra_id:05d}", muestra_id))
        return muestra_id

    def listar(self, estado: str | None = None) -> list[dict]:
        if estado:
            filas = self.conn.execute(f"{self.SELECT} WHERE m.estado = ? {self.ORDEN}", (estado,)).fetchall()
        else:
            filas = self.conn.execute(f"{self.SELECT} ORDER BY m.id DESC").fetchall()
        return _dicts(filas)

    def buscar(self, termino: str) -> list[dict]:
        patron = f"%{termino}%"
        filas = self.conn.execute(
            f"""{self.SELECT}
                WHERE m.codigo LIKE ? OR o.codigo LIKE ? OR p.documento LIKE ?
                   OR p.nombres LIKE ? OR p.apellidos LIKE ?
                ORDER BY m.id DESC""",
            (patron,) * 5,
        ).fetchall()
        return _dicts(filas)

    def por_id(self, muestra_id: int) -> dict | None:
        return _dict(self.conn.execute(f"{self.SELECT} WHERE m.id = ?", (muestra_id,)).fetchone())

    def por_orden(self, orden_id: int) -> list[dict]:
        return _dicts(self.conn.execute("SELECT * FROM muestras WHERE orden_id = ? ORDER BY id", (orden_id,)).fetchall())

    def iniciar(self, muestra_id: int) -> None:
        self.conn.execute(
            "UPDATE muestras SET estado = 'en_proceso', iniciada_en = datetime('now') WHERE id = ?", (muestra_id,)
        )

    def marcar_procesada(self, muestra_id: int) -> None:
        self.conn.execute(
            "UPDATE muestras SET estado = 'procesada', procesada_en = datetime('now') WHERE id = ?", (muestra_id,)
        )

    def conteo_por_estado(self) -> dict[str, int]:
        filas = self.conn.execute("SELECT estado, COUNT(*) FROM muestras GROUP BY estado").fetchall()
        return {f[0]: f[1] for f in filas}

    def minutos_promedio_procesamiento(self) -> float | None:
        fila = self.conn.execute(
            """SELECT AVG((julianday(procesada_en) - julianday(creado_en)) * 24 * 60)
               FROM muestras WHERE procesada_en IS NOT NULL"""
        ).fetchone()
        return round(fila[0], 1) if fila[0] is not None else None


class RepositorioResultados(Repositorio):
    def crear(self, muestra_id: int, examen: str, valor: str, unidad: str, referencia: str,
              observaciones: str | None, analista_id: int) -> int:
        cur = self.conn.execute(
            """INSERT INTO resultados (muestra_id, examen, valor, unidad, referencia, observaciones, analista_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (muestra_id, examen, valor, unidad, referencia, observaciones, analista_id),
        )
        return cur.lastrowid

    def listar(self, busqueda: str | None = None) -> list[dict]:
        consulta = """SELECT r.*, m.codigo AS muestra_codigo, o.codigo AS orden_codigo,
                             p.documento AS paciente_documento,
                             p.nombres || ' ' || p.apellidos AS paciente_nombre,
                             u.nombre AS analista_nombre
                      FROM resultados r
                      JOIN muestras m ON m.id = r.muestra_id
                      JOIN ordenes o ON o.id = m.orden_id
                      JOIN pacientes p ON p.id = o.paciente_id
                      LEFT JOIN usuarios u ON u.id = r.analista_id"""
        if busqueda:
            patron = f"%{busqueda}%"
            filas = self.conn.execute(
                consulta + " WHERE m.codigo LIKE ? OR o.codigo LIKE ? OR p.documento LIKE ? ORDER BY r.id DESC",
                (patron, patron, patron),
            ).fetchall()
        else:
            filas = self.conn.execute(consulta + " ORDER BY r.id DESC").fetchall()
        return _dicts(filas)

    def por_muestra(self, muestra_id: int) -> list[dict]:
        return _dicts(self.conn.execute("SELECT * FROM resultados WHERE muestra_id = ?", (muestra_id,)).fetchall())


class RepositorioInventario(Repositorio):
    def listar(self) -> list[dict]:
        return _dicts(self.conn.execute(
            "SELECT *, cantidad <= minimo AS bajo_minimo FROM inventario ORDER BY nombre"
        ).fetchall())

    def por_id(self, item_id: int) -> dict | None:
        return _dict(self.conn.execute(
            "SELECT *, cantidad <= minimo AS bajo_minimo FROM inventario WHERE id = ?", (item_id,)
        ).fetchone())

    def por_nombre(self, nombre: str) -> dict | None:
        return _dict(self.conn.execute(
            "SELECT *, cantidad <= minimo AS bajo_minimo FROM inventario WHERE nombre = ?", (nombre,)
        ).fetchone())

    def crear(self, datos: dict) -> int:
        cur = self.conn.execute(
            """INSERT INTO inventario (nombre, lote, cantidad, minimo, unidad, vencimiento)
               VALUES (:nombre, :lote, :cantidad, :minimo, :unidad, :vencimiento)""",
            datos,
        )
        return cur.lastrowid

    def ajustar(self, item_id: int, delta: int) -> None:
        self.conn.execute("UPDATE inventario SET cantidad = MAX(cantidad + ?, 0) WHERE id = ?", (delta, item_id))

    def bajo_minimo(self) -> list[dict]:
        return _dicts(self.conn.execute("SELECT * FROM inventario WHERE cantidad <= minimo ORDER BY nombre").fetchall())


class RepositorioHistorialNavegacion(Repositorio):
    def registrar(self, usuario_id: int, comando: str, ruta: str) -> None:
        self.conn.execute(
            "INSERT INTO historial_navegacion (usuario_id, comando, ruta) VALUES (?, ?, ?)",
            (usuario_id, comando, ruta),
        )

    def recientes(self, usuario_id: int, limite: int = 20) -> list[dict]:
        return _dicts(self.conn.execute(
            "SELECT * FROM historial_navegacion WHERE usuario_id = ? ORDER BY id DESC LIMIT ?",
            (usuario_id, limite),
        ).fetchall())

    def eliminar(self, entrada_id: int) -> None:
        self.conn.execute("DELETE FROM historial_navegacion WHERE id = ?", (entrada_id,))


class RepositorioMetricas(Repositorio):
    def registrar(self, datos: dict) -> int:
        cur = self.conn.execute(
            """INSERT INTO metricas_navegacion (prueba, rol, modo, pasos, tiempo_ms, errores, recorrido, usuario_id)
               VALUES (:prueba, :rol, :modo, :pasos, :tiempo_ms, :errores, :recorrido, :usuario_id)""",
            datos,
        )
        return cur.lastrowid

    def listar(self) -> list[dict]:
        return _dicts(self.conn.execute(
            """SELECT m.*, u.nombre AS usuario_nombre FROM metricas_navegacion m
               LEFT JOIN usuarios u ON u.id = m.usuario_id ORDER BY m.id DESC"""
        ).fetchall())

    def promedios(self) -> list[dict]:
        return _dicts(self.conn.execute(
            """SELECT prueba, modo, COUNT(*) AS ejecuciones,
                      AVG(pasos) AS pasos, AVG(tiempo_ms) AS tiempo_ms, AVG(errores) AS errores
               FROM metricas_navegacion GROUP BY prueba, modo ORDER BY prueba, modo"""
        ).fetchall())

    def eliminar_todo(self) -> None:
        self.conn.execute("DELETE FROM metricas_navegacion")


class RepositorioEventos(Repositorio):
    def registrar(self, tipo: str, mensaje: str, entidad: str | None, entidad_id: int | None,
                  roles: list[str]) -> int:
        cur = self.conn.execute(
            "INSERT INTO eventos (tipo, mensaje, entidad, entidad_id, roles) VALUES (?, ?, ?, ?, ?)",
            (tipo, mensaje, entidad, entidad_id, ",".join(roles)),
        )
        return cur.lastrowid

    def recientes(self, rol: str, limite: int = 15) -> list[dict]:
        return _dicts(self.conn.execute(
            "SELECT * FROM eventos WHERE ',' || roles || ',' LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%,{rol},%", limite),
        ).fetchall())
