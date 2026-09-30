"""Gestor de navegación: contexto del patrón Strategy."""

from labcloud.negocio.errores import AccesoDenegado, NoEncontrado
from labcloud.negocio.navegacion.comandos import InvocadorNavegacion, obtener_comando
from labcloud.negocio.navegacion.estrategias import EstrategiaNavegacion, crear_estrategia


class GestorNavegacion:
    def __init__(self, estrategia: EstrategiaNavegacion | None = None):
        self._estrategia = estrategia

    @classmethod
    def para_rol(cls, rol: str) -> "GestorNavegacion":
        return cls(crear_estrategia(rol))

    def establecer_estrategia(self, estrategia: EstrategiaNavegacion) -> None:
        self._estrategia = estrategia

    @property
    def estrategia(self) -> EstrategiaNavegacion:
        if self._estrategia is None:
            raise RuntimeError("El gestor de navegación no tiene estrategia asignada")
        return self._estrategia

    def obtener_ruta(self) -> str:
        return self.estrategia.obtener_ruta_principal()

    def obtener_menu(self) -> dict:
        return self.estrategia.obtener_menu()

    def navegar(self, clave: str, invocador: InvocadorNavegacion, usuario_id: int) -> str:
        comando = obtener_comando(clave)
        if comando is None:
            raise NoEncontrado(f"Acción de navegación desconocida: {clave}")
        if not self.estrategia.puede_ejecutar(clave):
            raise AccesoDenegado(f"'{comando.etiqueta}' no está disponible para el rol {self.estrategia.nombre}")
        return invocador.ejecutar(comando, usuario_id)
