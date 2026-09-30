"""Rutas HTTP de la API. Cada módulo funcional expone su propio router."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from labcloud.datos import database
from labcloud.datos.repositorios import RepositorioEventos, RepositorioHistorialNavegacion
from labcloud.negocio.catalogo import listar_examenes
from labcloud.negocio.eventos import difusor_tiempo_real
from labcloud.negocio.navegacion.comandos import InvocadorNavegacion
from labcloud.negocio.navegacion.estrategias import NavegacionConvencional, crear_estrategia, roles_registrados
from labcloud.negocio.navegacion.gestor import GestorNavegacion
from labcloud.negocio.servicios import (
    ServicioIndicadores,
    ServicioInventario,
    ServicioMuestras,
    ServicioOrdenes,
    ServicioPacientes,
    ServicioPruebas,
    ServicioResultados,
    ServicioUsuarios,
)
from labcloud.presentacion import esquemas
from labcloud.presentacion.dependencias import Conexion, UsuarioActual, obtener_token, requiere_roles

RECEPCION, ANALISTA, ADMIN = "recepcion", "analista", "administrador"

# --- Autenticación -----------------------------------------------------------------------------
auth = APIRouter(prefix="/api/auth", tags=["autenticación"])


@auth.post("/login")
def iniciar_sesion(datos: esquemas.Credenciales, conn: Conexion):
    servicio = ServicioUsuarios(conn)
    token, usuario = servicio.autenticar(datos.correo, datos.password)
    gestor = GestorNavegacion.para_rol(servicio.identificar_rol(usuario))
    return {"token": token, "usuario": usuario, "ruta_principal": gestor.obtener_ruta()}


@auth.post("/logout")
def cerrar_sesion(conn: Conexion, token: Annotated[str, Depends(obtener_token)]):
    ServicioUsuarios(conn).cerrar_sesion(token)
    return {"ok": True}


@auth.get("/yo")
def usuario_autenticado(usuario: UsuarioActual):
    return usuario


# --- Navegación (Strategy + Command) -----------------------------------------------------------
navegacion = APIRouter(prefix="/api/navegacion", tags=["navegación"])


@navegacion.get("/menu")
def menu_optimizado(usuario: UsuarioActual):
    return GestorNavegacion.para_rol(usuario["rol"]).obtener_menu()


@navegacion.get("/menu/convencional")
def menu_convencional(usuario: UsuarioActual):
    return {"estrategia": "NavegacionConvencional", "arbol": NavegacionConvencional().obtener_menu()}


@navegacion.get("/menu/simular")
def menu_simulado(rol: str, usuario: UsuarioActual):
    """Cambia la estrategia en tiempo de ejecución (usado por los escenarios de prueba)."""
    gestor = GestorNavegacion()
    gestor.establecer_estrategia(crear_estrategia(rol))
    return gestor.obtener_menu()


@navegacion.get("/estrategias")
def estrategias_registradas(usuario: UsuarioActual):
    return [crear_estrategia(rol).obtener_menu() for rol in roles_registrados()]


@navegacion.post("/comandos/{clave}")
def ejecutar_comando(clave: str, conn: Conexion, usuario: UsuarioActual):
    invocador = InvocadorNavegacion(RepositorioHistorialNavegacion(conn))
    ruta = GestorNavegacion.para_rol(usuario["rol"]).navegar(clave, invocador, usuario["id"])
    return {"comando": clave, "ruta": ruta}


@navegacion.post("/deshacer")
def deshacer_navegacion(conn: Conexion, usuario: UsuarioActual):
    gestor = GestorNavegacion.para_rol(usuario["rol"])
    invocador = InvocadorNavegacion(RepositorioHistorialNavegacion(conn))
    return {"ruta": invocador.deshacer(usuario["id"], gestor.obtener_ruta())}


@navegacion.get("/historial")
def historial_navegacion(conn: Conexion, usuario: UsuarioActual):
    return RepositorioHistorialNavegacion(conn).recientes(usuario["id"])


# --- Usuarios ----------------------------------------------------------------------------------
usuarios = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@usuarios.get("")
def listar_usuarios(conn: Conexion, _=requiere_roles(ADMIN)):
    return {"usuarios": ServicioUsuarios(conn).listar(), "roles": roles_registrados()}


@usuarios.post("", status_code=201)
def crear_usuario(datos: esquemas.NuevoUsuario, conn: Conexion, _=requiere_roles(ADMIN)):
    return ServicioUsuarios(conn).crear(datos.nombre, datos.correo, datos.password, datos.rol)


@usuarios.patch("/{usuario_id}")
def cambiar_estado_usuario(usuario_id: int, datos: esquemas.EstadoUsuario, conn: Conexion,
                           actor: dict = requiere_roles(ADMIN)):
    return ServicioUsuarios(conn).cambiar_estado(usuario_id, datos.activo, actor["id"])


# --- Pacientes y órdenes -----------------------------------------------------------------------
pacientes = APIRouter(prefix="/api/pacientes", tags=["pacientes"])


@pacientes.get("")
def listar_pacientes(conn: Conexion, q: str | None = None, _=requiere_roles(RECEPCION, ADMIN)):
    return ServicioPacientes(conn).listar(q)


@pacientes.post("", status_code=201)
def crear_paciente(datos: esquemas.NuevoPaciente, conn: Conexion, _=requiere_roles(RECEPCION)):
    return ServicioPacientes(conn).crear(datos.model_dump())


ordenes = APIRouter(prefix="/api/ordenes", tags=["órdenes"])


@ordenes.get("/examenes")
def catalogo_examenes(usuario: UsuarioActual):
    return listar_examenes()


@ordenes.get("")
def listar_ordenes(conn: Conexion, estado: str | None = None, _=requiere_roles(RECEPCION, ADMIN)):
    return ServicioOrdenes(conn).listar(estado)


@ordenes.post("", status_code=201)
def crear_orden(datos: esquemas.NuevaOrden, conn: Conexion, usuario: dict = requiere_roles(RECEPCION)):
    return ServicioOrdenes(conn).crear(datos.paciente_id, datos.examenes, datos.prioridad, usuario["id"])


# --- Muestras y resultados ---------------------------------------------------------------------
muestras = APIRouter(prefix="/api/muestras", tags=["muestras"])


@muestras.get("")
def listar_muestras(conn: Conexion, estado: str | None = None, q: str | None = None,
                    _=requiere_roles(RECEPCION, ANALISTA, ADMIN)):
    servicio = ServicioMuestras(conn)
    return servicio.buscar(q) if q else servicio.listar(estado)


@muestras.get("/{muestra_id}")
def detalle_muestra(muestra_id: int, conn: Conexion, _=requiere_roles(RECEPCION, ANALISTA, ADMIN)):
    return ServicioMuestras(conn).detalle(muestra_id)


@muestras.post("/{muestra_id}/procesar")
def procesar_muestra(muestra_id: int, conn: Conexion, _=requiere_roles(ANALISTA)):
    return ServicioMuestras(conn).iniciar_procesamiento(muestra_id)


@muestras.post("/{muestra_id}/resultados")
def registrar_resultados(muestra_id: int, datos: esquemas.RegistroResultados, conn: Conexion,
                         usuario: dict = requiere_roles(ANALISTA)):
    valores = [v.model_dump() for v in datos.valores]
    return ServicioMuestras(conn).registrar_resultados(muestra_id, valores, usuario["id"])


resultados = APIRouter(prefix="/api/resultados", tags=["resultados"])


@resultados.get("")
def listar_resultados(conn: Conexion, q: str | None = None, _=requiere_roles(RECEPCION, ANALISTA, ADMIN)):
    return ServicioResultados(conn).listar(q)


# --- Inventario e indicadores ------------------------------------------------------------------
inventario = APIRouter(prefix="/api/inventario", tags=["inventario"])


@inventario.get("")
def listar_inventario(conn: Conexion, _=requiere_roles(ADMIN)):
    return ServicioInventario(conn).listar()


@inventario.post("", status_code=201)
def crear_insumo(datos: esquemas.NuevoInsumo, conn: Conexion, _=requiere_roles(ADMIN)):
    return ServicioInventario(conn).crear(datos.model_dump())


@inventario.post("/{item_id}/ajuste")
def ajustar_insumo(item_id: int, datos: esquemas.AjusteInventario, conn: Conexion, _=requiere_roles(ADMIN)):
    return ServicioInventario(conn).ajustar(item_id, datos.delta)


indicadores = APIRouter(prefix="/api/indicadores", tags=["indicadores"])


@indicadores.get("")
def resumen_indicadores(conn: Conexion, _=requiere_roles(ADMIN)):
    return ServicioIndicadores(conn).resumen()


# --- Pruebas de navegación (sección 8) ---------------------------------------------------------
pruebas = APIRouter(prefix="/api/pruebas", tags=["pruebas"])


@pruebas.get("/escenarios")
def escenarios_prueba(conn: Conexion, usuario: UsuarioActual):
    return ServicioPruebas(conn).escenarios()


@pruebas.post("/resultados", status_code=201)
def registrar_prueba(datos: esquemas.ResultadoPrueba, conn: Conexion, usuario: UsuarioActual):
    return ServicioPruebas(conn).registrar(datos.model_dump(), usuario["id"])


@pruebas.get("/resumen")
def resumen_pruebas(conn: Conexion, usuario: UsuarioActual):
    return {"resumen": ServicioPruebas(conn).resumen(), "historial": ServicioPruebas(conn).historial()}


@pruebas.delete("/resultados")
def reiniciar_pruebas(conn: Conexion, _=requiere_roles(ADMIN)):
    ServicioPruebas(conn).reiniciar()
    return {"ok": True}


# --- Eventos (Observer) ------------------------------------------------------------------------
eventos = APIRouter(prefix="/api/eventos", tags=["eventos"])


@eventos.get("")
def eventos_recientes(conn: Conexion, usuario: UsuarioActual, limite: int = Query(15, le=50)):
    return RepositorioEventos(conn).recientes(usuario["rol"], limite)


@eventos.get("/stream")
async def flujo_eventos(request: Request, token: Annotated[str, Depends(obtener_token)]):
    conn = database.conectar()
    try:
        usuario = ServicioUsuarios(conn).usuario_por_token(token)
    finally:
        conn.close()
    suscriptor = difusor_tiempo_real.conectar(usuario["rol"])

    async def generar():
        try:
            yield "event: conectado\ndata: {}\n\n"
            while not await request.is_disconnected():
                try:
                    carga = await asyncio.wait_for(suscriptor.cola.get(), timeout=15)
                    yield f"event: evento\ndata: {carga}\n\n"
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            difusor_tiempo_real.desconectar(suscriptor)

    return StreamingResponse(generar(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


ROUTERS = [auth, navegacion, usuarios, pacientes, ordenes, muestras, resultados, inventario, indicadores,
           pruebas, eventos]
