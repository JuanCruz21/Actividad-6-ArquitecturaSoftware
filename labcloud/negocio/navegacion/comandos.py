"""Patrón Command: cada acción de navegación se encapsula como un objeto ejecutable.

Las estrategias no conocen rutas; referencian comandos por su clave. El invocador
ejecuta el comando, registra el historial y permite deshacer (volver atrás).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from labcloud.datos.repositorios import RepositorioHistorialNavegacion


class ComandoNavegacion(ABC):
    clave: str
    etiqueta: str
    icono: str
    descripcion: str

    @abstractmethod
    def ejecutar(self) -> str:
        """Ejecuta la acción y devuelve la ruta de destino."""

    def a_dict(self) -> dict:
        return {
            "clave": self.clave,
            "etiqueta": self.etiqueta,
            "icono": self.icono,
            "descripcion": self.descripcion,
            "ruta": self.ejecutar(),
        }


@dataclass
class IrAModulo(ComandoNavegacion):
    clave: str
    etiqueta: str
    ruta: str
    icono: str
    descripcion: str

    def ejecutar(self) -> str:
        return self.ruta


CATALOGO_COMANDOS: dict[str, ComandoNavegacion] = {
    c.clave: c
    for c in [
        IrAModulo("inicio", "Inicio", "/inicio", "home", "Resumen y accesos del rol"),
        IrAModulo("pacientes", "Pacientes", "/pacientes", "users", "Registro y consulta de pacientes"),
        IrAModulo("ordenes.nueva", "Nueva orden", "/ordenes/nueva", "file-plus", "Crear una solicitud de análisis"),
        IrAModulo("ordenes.listado", "Consultar órdenes", "/ordenes", "files", "Listado de órdenes registradas"),
        IrAModulo("muestras.seguimiento", "Seguimiento de muestra", "/muestras/seguimiento", "search",
                  "Estado de muestras por orden o paciente"),
        IrAModulo("muestras.pendientes", "Muestras pendientes", "/muestras/pendientes", "inbox",
                  "Muestras en espera de análisis"),
        IrAModulo("procesamiento", "Procesamiento", "/procesamiento", "flask", "Muestras en proceso y captura"),
        IrAModulo("resultados", "Resultados", "/resultados", "clipboard", "Resultados registrados"),
        IrAModulo("usuarios", "Usuarios", "/usuarios", "user-cog", "Cuentas, roles y permisos"),
        IrAModulo("inventario", "Inventario", "/inventario", "package", "Existencias, lotes y alertas"),
        IrAModulo("indicadores", "Indicadores", "/indicadores", "chart", "Información consolidada de gestión"),
        IrAModulo("configuracion", "Configuración", "/configuracion", "settings", "Estrategias de navegación"),
        IrAModulo("pruebas", "Pruebas de navegación", "/pruebas", "timer", "Escenarios P1–P3 y métricas"),
    ]
}


def obtener_comando(clave: str) -> ComandoNavegacion | None:
    return CATALOGO_COMANDOS.get(clave)


class InvocadorNavegacion:
    """Ejecuta comandos de navegación y mantiene una pila de historial por usuario."""

    def __init__(self, historial: RepositorioHistorialNavegacion):
        self.historial = historial

    def ejecutar(self, comando: ComandoNavegacion, usuario_id: int) -> str:
        ruta = comando.ejecutar()
        self.historial.registrar(usuario_id, comando.clave, ruta)
        return ruta

    def deshacer(self, usuario_id: int, ruta_por_defecto: str) -> str:
        entradas = self.historial.recientes(usuario_id, limite=2)
        if not entradas:
            return ruta_por_defecto
        self.historial.eliminar(entradas[0]["id"])
        return entradas[1]["ruta"] if len(entradas) > 1 else ruta_por_defecto
