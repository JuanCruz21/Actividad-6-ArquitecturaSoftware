"""Pruebas unitarias de los patrones Strategy y Command."""

import pytest

from labcloud.negocio.errores import AccesoDenegado, DatosInvalidos
from labcloud.negocio.navegacion.comandos import CATALOGO_COMANDOS, InvocadorNavegacion
from labcloud.negocio.navegacion.estrategias import (
    EstrategiaNavegacion,
    NavegacionAdministrador,
    NavegacionAnalista,
    NavegacionConvencional,
    NavegacionRecepcion,
    crear_estrategia,
    registrar_estrategia,
    roles_registrados,
)
from labcloud.negocio.navegacion.gestor import GestorNavegacion


@pytest.mark.parametrize("rol, clase, prioritarias", [
    ("recepcion", NavegacionRecepcion, ["Pacientes", "Nueva orden", "Seguimiento de muestra"]),
    ("analista", NavegacionAnalista, ["Muestras pendientes", "Procesamiento", "Resultados"]),
    ("administrador", NavegacionAdministrador, ["Usuarios", "Inventario", "Indicadores", "Configuración"]),
])
def test_cada_rol_obtiene_su_estrategia(rol, clase, prioritarias):
    gestor = GestorNavegacion.para_rol(rol)
    assert isinstance(gestor.estrategia, clase)
    assert [i["etiqueta"] for i in gestor.obtener_menu()["principales"]] == prioritarias


def test_ruta_principal_del_analista_son_las_muestras_pendientes():
    assert GestorNavegacion.para_rol("analista").obtener_ruta() == "/muestras/pendientes"


def test_el_gestor_permite_cambiar_de_estrategia_en_ejecucion():
    gestor = GestorNavegacion(NavegacionRecepcion())
    gestor.establecer_estrategia(NavegacionAdministrador())
    assert gestor.obtener_menu()["rol"] == "administrador"


def test_rol_desconocido_es_rechazado():
    with pytest.raises(DatosInvalidos):
        crear_estrategia("auditor")


def test_agregar_un_rol_solo_requiere_una_nueva_estrategia():
    @registrar_estrategia("calidad_prueba")
    class NavegacionCalidad(EstrategiaNavegacion):
        nombre = "Control de calidad"
        descripcion = "Rol agregado sin modificar el gestor"

        def comandos_prioritarios(self):
            return ["resultados", "indicadores"]

    try:
        menu = GestorNavegacion.para_rol("calidad_prueba").obtener_menu()
        assert [i["ruta"] for i in menu["principales"]] == ["/resultados", "/indicadores"]
    finally:
        from labcloud.negocio.navegacion import estrategias
        estrategias._REGISTRO.pop("calidad_prueba")
    assert "calidad_prueba" not in roles_registrados()


def test_menu_convencional_requiere_mas_niveles_para_nueva_orden():
    arbol = NavegacionConvencional().obtener_menu()

    def profundidad(nodos, clave, nivel=1):
        for n in nodos:
            if n["clave"] == clave:
                return nivel
            encontrado = profundidad(n["hijos"], clave, nivel + 1)
            if encontrado:
                return encontrado
        return None

    assert profundidad(arbol, "ordenes.nueva") == 3
    assert profundidad(arbol, "muestras.pendientes") == 3
    assert profundidad(arbol, "inventario") == 2


class HistorialEnMemoria:
    def __init__(self):
        self.entradas, self._id = [], 0

    def registrar(self, usuario_id, comando, ruta):
        self._id += 1
        self.entradas.insert(0, {"id": self._id, "usuario_id": usuario_id, "comando": comando, "ruta": ruta})

    def recientes(self, usuario_id, limite=20):
        return [e for e in self.entradas if e["usuario_id"] == usuario_id][:limite]

    def eliminar(self, entrada_id):
        self.entradas = [e for e in self.entradas if e["id"] != entrada_id]


def test_invocador_ejecuta_y_deshace_comandos():
    invocador = InvocadorNavegacion(HistorialEnMemoria())
    gestor = GestorNavegacion.para_rol("recepcion")
    assert gestor.navegar("pacientes", invocador, 1) == "/pacientes"
    assert gestor.navegar("ordenes.nueva", invocador, 1) == "/ordenes/nueva"
    assert invocador.deshacer(1, "/inicio") == "/pacientes"
    assert invocador.deshacer(1, "/inicio") == "/inicio"


def test_comando_fuera_de_la_estrategia_es_denegado():
    with pytest.raises(AccesoDenegado):
        GestorNavegacion.para_rol("recepcion").navegar("inventario", InvocadorNavegacion(HistorialEnMemoria()), 1)


def test_todas_las_estrategias_referencian_comandos_existentes():
    for rol in roles_registrados():
        assert crear_estrategia(rol).claves_permitidas() <= set(CATALOGO_COMANDOS)
