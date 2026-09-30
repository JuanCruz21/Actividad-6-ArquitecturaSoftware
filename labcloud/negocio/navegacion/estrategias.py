"""Patrón Strategy: una estrategia de navegación por rol.

Para incorporar un rol nuevo basta con crear una clase que herede de
`EstrategiaNavegacion` y decorarla con `@registrar_estrategia("<rol>")`;
ni el gestor ni la interfaz necesitan cambios.
"""

from abc import ABC, abstractmethod

from labcloud.negocio.errores import DatosInvalidos
from labcloud.negocio.navegacion.comandos import CATALOGO_COMANDOS


class EstrategiaNavegacion(ABC):
    rol: str
    nombre: str
    descripcion: str

    @abstractmethod
    def comandos_prioritarios(self) -> list[str]:
        """Claves de los comandos que el rol necesita a un clic."""

    def comandos_secundarios(self) -> list[str]:
        return ["inicio", "pruebas"]

    def obtener_ruta_principal(self) -> str:
        return CATALOGO_COMANDOS["inicio"].ejecutar()

    def obtener_menu(self) -> dict:
        return {
            "rol": self.rol,
            "estrategia": type(self).__name__,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "ruta_principal": self.obtener_ruta_principal(),
            "principales": [CATALOGO_COMANDOS[c].a_dict() for c in self.comandos_prioritarios()],
            "secundarias": [CATALOGO_COMANDOS[c].a_dict() for c in self.comandos_secundarios()],
            "rutas_permitidas": sorted(self.rutas_permitidas()),
        }

    def claves_permitidas(self) -> set[str]:
        return set(self.comandos_prioritarios()) | set(self.comandos_secundarios())

    def rutas_permitidas(self) -> set[str]:
        return {CATALOGO_COMANDOS[c].ejecutar() for c in self.claves_permitidas()}

    def puede_ejecutar(self, clave: str) -> bool:
        return clave in self.claves_permitidas()


_REGISTRO: dict[str, type[EstrategiaNavegacion]] = {}


def registrar_estrategia(rol: str):
    def decorador(cls: type[EstrategiaNavegacion]) -> type[EstrategiaNavegacion]:
        cls.rol = rol
        _REGISTRO[rol] = cls
        return cls

    return decorador


def crear_estrategia(rol: str) -> EstrategiaNavegacion:
    try:
        return _REGISTRO[rol]()
    except KeyError:
        raise DatosInvalidos(f"No existe una estrategia de navegación para el rol '{rol}'") from None


def roles_registrados() -> list[str]:
    return list(_REGISTRO)


@registrar_estrategia("recepcion")
class NavegacionRecepcion(EstrategiaNavegacion):
    nombre = "Recepción"
    descripcion = "Prioriza pacientes, órdenes y seguimiento de muestras."

    def comandos_prioritarios(self) -> list[str]:
        return ["pacientes", "ordenes.nueva", "muestras.seguimiento"]

    def comandos_secundarios(self) -> list[str]:
        return ["inicio", "ordenes.listado", "pruebas"]


@registrar_estrategia("analista")
class NavegacionAnalista(EstrategiaNavegacion):
    nombre = "Analista"
    descripcion = "Prioriza muestras pendientes, procesamiento y resultados."

    def comandos_prioritarios(self) -> list[str]:
        return ["muestras.pendientes", "procesamiento", "resultados"]

    def obtener_ruta_principal(self) -> str:
        return CATALOGO_COMANDOS["muestras.pendientes"].ejecutar()


@registrar_estrategia("administrador")
class NavegacionAdministrador(EstrategiaNavegacion):
    nombre = "Administrador"
    descripcion = "Prioriza usuarios, inventario, indicadores y configuración."

    def comandos_prioritarios(self) -> list[str]:
        return ["usuarios", "inventario", "indicadores", "configuracion"]

    def comandos_secundarios(self) -> list[str]:
        return ["inicio", "ordenes.listado", "pruebas"]


class NavegacionConvencional:
    """Menú jerárquico único para todos los roles (línea base para las pruebas)."""

    ARBOL = [
        ("inicio", None),
        ("Gestión clínica", [
            ("pacientes", None),
            ("Órdenes", [("ordenes.nueva", None), ("ordenes.listado", None)]),
        ]),
        ("Laboratorio", [
            ("Muestras", [("muestras.seguimiento", None), ("muestras.pendientes", None)]),
            ("procesamiento", None),
            ("resultados", None),
        ]),
        ("Administración", [("usuarios", None), ("inventario", None), ("configuracion", None)]),
        ("Reportes", [("indicadores", None), ("pruebas", None)]),
    ]

    def obtener_menu(self) -> list[dict]:
        return [self._nodo(etiqueta, hijos, ruta_padre="") for etiqueta, hijos in self.ARBOL]

    def _nodo(self, clave_o_etiqueta: str, hijos, ruta_padre: str) -> dict:
        if hijos is None:
            nodo = CATALOGO_COMANDOS[clave_o_etiqueta].a_dict()
            nodo["hijos"] = []
            return nodo
        clave = f"{ruta_padre}/{clave_o_etiqueta}".lower()
        return {
            "clave": clave,
            "etiqueta": clave_o_etiqueta,
            "icono": "folder",
            "descripcion": "",
            "ruta": None,
            "hijos": [self._nodo(e, h, clave) for e, h in hijos],
        }
