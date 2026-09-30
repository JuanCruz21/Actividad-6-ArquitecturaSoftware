"""Servicios de negocio. Coordinan repositorios, reglas y publicación de eventos (Observer)."""

import sqlite3
from collections import defaultdict

from labcloud import config
from labcloud.datos import repositorios as repos
from labcloud.negocio.catalogo import EXAMENES
from labcloud.negocio.errores import Conflicto, DatosInvalidos, NoAutenticado, NoEncontrado
from labcloud.negocio.eventos import Evento, SujetoEventos, sujeto_eventos
from labcloud.negocio.navegacion.estrategias import crear_estrategia, roles_registrados
from labcloud.negocio.seguridad import generar_token, hash_password, verificar_password


class Servicio:
    def __init__(self, conn: sqlite3.Connection, eventos: SujetoEventos = sujeto_eventos):
        self.conn = conn
        self.eventos = eventos

    def _confirmar_y_notificar(self, *eventos: Evento) -> None:
        # Se confirma la transacción antes de notificar para que los observadores vean datos consistentes.
        self.conn.commit()
        for evento in eventos:
            self.eventos.notificar(evento)


class ServicioUsuarios(Servicio):
    """Gestor de usuarios: autenticación e identificación del rol."""

    def autenticar(self, correo: str, password: str) -> tuple[str, dict]:
        usuario = repos.RepositorioUsuarios(self.conn).por_correo(correo.strip())
        if not usuario or not usuario["activo"] or not verificar_password(password, usuario["password_hash"]):
            raise NoAutenticado("Correo o contraseña incorrectos")
        token = generar_token()
        repos.RepositorioSesiones(self.conn).crear(token, usuario["id"], config.DURACION_SESION_HORAS)
        return token, self._publico(usuario)

    def usuario_por_token(self, token: str) -> dict:
        usuario = repos.RepositorioSesiones(self.conn).usuario_por_token(token)
        if not usuario:
            raise NoAutenticado("Sesión inválida o expirada")
        return usuario

    def cerrar_sesion(self, token: str) -> None:
        repos.RepositorioSesiones(self.conn).eliminar(token)

    def identificar_rol(self, usuario: dict) -> str:
        return usuario["rol"]

    def listar(self) -> list[dict]:
        return repos.RepositorioUsuarios(self.conn).listar()

    def crear(self, nombre: str, correo: str, password: str, rol: str) -> dict:
        if rol not in roles_registrados():
            raise DatosInvalidos(f"Rol inválido. Roles disponibles: {', '.join(roles_registrados())}")
        if len(password) < 6:
            raise DatosInvalidos("La contraseña debe tener al menos 6 caracteres")
        repo = repos.RepositorioUsuarios(self.conn)
        if repo.por_correo(correo):
            raise Conflicto("Ya existe un usuario con ese correo")
        usuario_id = repo.crear(nombre.strip(), correo.strip(), hash_password(password), rol)
        return repo.por_id(usuario_id)

    def cambiar_estado(self, usuario_id: int, activo: bool, actor_id: int) -> dict:
        repo = repos.RepositorioUsuarios(self.conn)
        if not repo.por_id(usuario_id):
            raise NoEncontrado("Usuario no encontrado")
        if usuario_id == actor_id and not activo:
            raise DatosInvalidos("No puedes desactivar tu propia cuenta")
        repo.actualizar_estado(usuario_id, activo)
        return repo.por_id(usuario_id)

    @staticmethod
    def _publico(usuario: dict) -> dict:
        return {k: usuario[k] for k in ("id", "nombre", "correo", "rol")}


class ServicioPacientes(Servicio):
    def listar(self, busqueda: str | None = None) -> list[dict]:
        return repos.RepositorioPacientes(self.conn).listar(busqueda)

    def crear(self, datos: dict) -> dict:
        repo = repos.RepositorioPacientes(self.conn)
        if repo.por_documento(datos["documento"]):
            raise Conflicto("Ya existe un paciente con ese documento")
        return repo.por_id(repo.crear(datos))


class ServicioOrdenes(Servicio):
    def listar(self, estado: str | None = None) -> list[dict]:
        ordenes = repos.RepositorioOrdenes(self.conn).listar(estado)
        muestras = repos.RepositorioMuestras(self.conn)
        for orden in ordenes:
            orden["muestras"] = muestras.por_orden(orden["id"])
        return ordenes

    def crear(self, paciente_id: int, examenes: list[str], prioridad: str, usuario_id: int) -> dict:
        if not repos.RepositorioPacientes(self.conn).por_id(paciente_id):
            raise NoEncontrado("Paciente no encontrado")
        examenes = list(dict.fromkeys(examenes))
        if not examenes:
            raise DatosInvalidos("Selecciona al menos un examen")
        desconocidos = [e for e in examenes if e not in EXAMENES]
        if desconocidos:
            raise DatosInvalidos(f"Exámenes desconocidos: {', '.join(desconocidos)}")

        orden_id = repos.RepositorioOrdenes(self.conn).crear(paciente_id, examenes, prioridad, usuario_id)
        por_tipo: dict[str, list[str]] = defaultdict(list)
        for clave in examenes:
            por_tipo[EXAMENES[clave].tipo_muestra].append(clave)
        muestras = repos.RepositorioMuestras(self.conn)
        for tipo, claves in por_tipo.items():
            muestras.crear(orden_id, tipo, claves)

        orden = repos.RepositorioOrdenes(self.conn).por_id(orden_id)
        orden["muestras"] = muestras.por_orden(orden_id)
        urgente = " (URGENTE)" if prioridad == "urgente" else ""
        self._confirmar_y_notificar(Evento(
            tipo="orden.creada",
            mensaje=f"Nueva orden {orden['codigo']}{urgente}: {len(orden['muestras'])} muestra(s) pendiente(s)",
            roles=["analista", "recepcion"],
            entidad="orden",
            entidad_id=orden_id,
        ))
        return orden


class ServicioMuestras(Servicio):
    def listar(self, estado: str | None = None) -> list[dict]:
        return [self._enriquecer(m) for m in repos.RepositorioMuestras(self.conn).listar(estado)]

    def buscar(self, termino: str) -> list[dict]:
        return [self._enriquecer(m) for m in repos.RepositorioMuestras(self.conn).buscar(termino)]

    def detalle(self, muestra_id: int) -> dict:
        muestra = repos.RepositorioMuestras(self.conn).por_id(muestra_id)
        if not muestra:
            raise NoEncontrado("Muestra no encontrada")
        return self._enriquecer(muestra)

    def iniciar_procesamiento(self, muestra_id: int) -> dict:
        muestra = self.detalle(muestra_id)
        if muestra["estado"] != "pendiente":
            raise Conflicto(f"La muestra {muestra['codigo']} no está pendiente")
        repos.RepositorioMuestras(self.conn).iniciar(muestra_id)
        ordenes = repos.RepositorioOrdenes(self.conn)
        if ordenes.por_id(muestra["orden_id"])["estado"] == "registrada":
            ordenes.actualizar_estado(muestra["orden_id"], "en_proceso")

        eventos = [Evento(
            tipo="muestra.en_proceso",
            mensaje=f"Muestra {muestra['codigo']} ({muestra['tipo']}) en procesamiento",
            roles=["analista", "recepcion"],
            entidad="muestra",
            entidad_id=muestra_id,
        )]
        eventos += self._consumir_reactivos(muestra["examenes_lista"])
        self._confirmar_y_notificar(*eventos)
        return self.detalle(muestra_id)

    def registrar_resultados(self, muestra_id: int, valores: list[dict], analista_id: int) -> dict:
        muestra = self.detalle(muestra_id)
        if muestra["estado"] != "en_proceso":
            raise Conflicto("Solo se pueden registrar resultados de muestras en procesamiento")
        por_examen = {v["examen"]: v for v in valores if str(v.get("valor", "")).strip()}
        faltantes = [e for e in muestra["examenes_lista"] if e not in por_examen]
        if faltantes:
            nombres = ", ".join(EXAMENES[e].nombre for e in faltantes)
            raise DatosInvalidos(f"Faltan resultados para: {nombres}")

        resultados = repos.RepositorioResultados(self.conn)
        for clave in muestra["examenes_lista"]:
            examen = EXAMENES[clave]
            valor = por_examen[clave]
            resultados.crear(muestra_id, examen.nombre, str(valor["valor"]).strip(), examen.unidad,
                             examen.referencia, valor.get("observaciones"), analista_id)
        repos.RepositorioMuestras(self.conn).marcar_procesada(muestra_id)

        eventos = [Evento(
            tipo="muestra.procesada",
            mensaje=f"Resultados registrados para la muestra {muestra['codigo']}",
            roles=["analista", "recepcion"],
            entidad="muestra",
            entidad_id=muestra_id,
        )]
        restantes = [m for m in repos.RepositorioMuestras(self.conn).por_orden(muestra["orden_id"])
                     if m["estado"] != "procesada"]
        if not restantes:
            repos.RepositorioOrdenes(self.conn).actualizar_estado(muestra["orden_id"], "completada")
            eventos.append(Evento(
                tipo="orden.completada",
                mensaje=f"Orden {muestra['orden_codigo']} completada: resultados listos para "
                        f"{muestra['paciente_nombre']}",
                roles=["recepcion", "administrador"],
                entidad="orden",
                entidad_id=muestra["orden_id"],
            ))
        self._confirmar_y_notificar(*eventos)
        return self.detalle(muestra_id)

    def _consumir_reactivos(self, examenes: list[str]) -> list[Evento]:
        inventario = repos.RepositorioInventario(self.conn)
        alertas = []
        for clave in examenes:
            item = inventario.por_nombre(EXAMENES[clave].reactivo)
            if not item:
                continue
            inventario.ajustar(item["id"], -1)
            actualizado = inventario.por_id(item["id"])
            if actualizado["bajo_minimo"]:
                alertas.append(Evento(
                    tipo="inventario.bajo",
                    mensaje=f"Stock bajo: {actualizado['nombre']} ({actualizado['cantidad']} "
                            f"{actualizado['unidad']}, mínimo {actualizado['minimo']})",
                    roles=["administrador", "analista"],
                    entidad="inventario",
                    entidad_id=item["id"],
                ))
        return alertas

    def _enriquecer(self, muestra: dict) -> dict:
        claves = muestra["examenes"].split(",")
        muestra["examenes_lista"] = claves
        muestra["examenes_detalle"] = [
            {"clave": c, "nombre": EXAMENES[c].nombre, "unidad": EXAMENES[c].unidad,
             "referencia": EXAMENES[c].referencia} for c in claves if c in EXAMENES
        ]
        muestra["resultados"] = repos.RepositorioResultados(self.conn).por_muestra(muestra["id"])
        return muestra


class ServicioResultados(Servicio):
    def listar(self, busqueda: str | None = None) -> list[dict]:
        return repos.RepositorioResultados(self.conn).listar(busqueda)


class ServicioInventario(Servicio):
    def listar(self) -> list[dict]:
        return repos.RepositorioInventario(self.conn).listar()

    def crear(self, datos: dict) -> dict:
        repo = repos.RepositorioInventario(self.conn)
        if repo.por_nombre(datos["nombre"]):
            raise Conflicto("Ya existe un insumo con ese nombre")
        return repo.por_id(repo.crear(datos))

    def ajustar(self, item_id: int, delta: int) -> dict:
        repo = repos.RepositorioInventario(self.conn)
        if not repo.por_id(item_id):
            raise NoEncontrado("Insumo no encontrado")
        repo.ajustar(item_id, delta)
        item = repo.por_id(item_id)
        eventos = []
        if item["bajo_minimo"]:
            eventos.append(Evento(
                tipo="inventario.bajo",
                mensaje=f"Stock bajo: {item['nombre']} ({item['cantidad']} {item['unidad']})",
                roles=["administrador"],
                entidad="inventario",
                entidad_id=item_id,
            ))
        self._confirmar_y_notificar(*eventos)
        return item


class ServicioIndicadores(Servicio):
    def resumen(self) -> dict:
        muestras = repos.RepositorioMuestras(self.conn)
        return {
            "pacientes": repos.RepositorioPacientes(self.conn).contar(),
            "usuarios": repos.RepositorioUsuarios(self.conn).contar(),
            "ordenes_por_estado": repos.RepositorioOrdenes(self.conn).conteo_por_estado(),
            "muestras_por_estado": muestras.conteo_por_estado(),
            "minutos_promedio_procesamiento": muestras.minutos_promedio_procesamiento(),
            "inventario_bajo": repos.RepositorioInventario(self.conn).bajo_minimo(),
            "navegacion": ServicioPruebas(self.conn).resumen(),
        }


ESCENARIOS_PRUEBA = [
    {"prueba": "P1", "rol": "recepcion", "tarea": "Acceder a la opción Nueva orden", "objetivo": "ordenes.nueva"},
    {"prueba": "P2", "rol": "analista", "tarea": "Acceder a Muestras pendientes", "objetivo": "muestras.pendientes"},
    {"prueba": "P3", "rol": "administrador", "tarea": "Acceder a Inventario", "objetivo": "inventario"},
]


class ServicioPruebas(Servicio):
    """Registro y comparación de recorridos convencionales frente a optimizados (Tabla 6)."""

    def escenarios(self) -> list[dict]:
        return [dict(e, rol_nombre=crear_estrategia(e["rol"]).nombre) for e in ESCENARIOS_PRUEBA]

    def registrar(self, datos: dict, usuario_id: int) -> dict:
        escenario = next((e for e in ESCENARIOS_PRUEBA if e["prueba"] == datos["prueba"]), None)
        if not escenario:
            raise NoEncontrado("Escenario de prueba desconocido")
        registro = dict(datos, rol=escenario["rol"], usuario_id=usuario_id,
                        recorrido=" > ".join(datos.get("recorrido") or []))
        repos.RepositorioMetricas(self.conn).registrar(registro)
        return self.resumen()

    def historial(self) -> list[dict]:
        return repos.RepositorioMetricas(self.conn).listar()

    def reiniciar(self) -> None:
        repos.RepositorioMetricas(self.conn).eliminar_todo()

    def resumen(self) -> list[dict]:
        promedios = {(p["prueba"], p["modo"]): p for p in repos.RepositorioMetricas(self.conn).promedios()}
        filas = []
        for e in ESCENARIOS_PRUEBA:
            conv = promedios.get((e["prueba"], "convencional"))
            opt = promedios.get((e["prueba"], "optimizada"))
            reduccion = None
            if conv and opt and conv["pasos"]:
                reduccion = round((conv["pasos"] - opt["pasos"]) / conv["pasos"] * 100, 1)
            filas.append({
                "prueba": e["prueba"],
                "rol": crear_estrategia(e["rol"]).nombre,
                "tarea": e["tarea"],
                "pasos_convencional": _r(conv, "pasos"),
                "pasos_optimizada": _r(opt, "pasos"),
                "reduccion_pasos_pct": reduccion,
                "tiempo_convencional_ms": _r(conv, "tiempo_ms", 0),
                "tiempo_optimizado_ms": _r(opt, "tiempo_ms", 0),
                "errores_convencional": _r(conv, "errores"),
                "errores_optimizada": _r(opt, "errores"),
                "ejecuciones_convencional": conv["ejecuciones"] if conv else 0,
                "ejecuciones_optimizada": opt["ejecuciones"] if opt else 0,
            })
        return filas


def _r(fila: dict | None, campo: str, decimales: int = 1):
    return round(fila[campo], decimales) if fila else None
