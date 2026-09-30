"""Pruebas de integración de la API del monolito."""

from labcloud.negocio.eventos import Observador, sujeto_eventos


def test_login_invalido(cliente):
    r = cliente.post("/api/auth/login", json={"correo": "recepcion@labcloud.test", "password": "mal"})
    assert r.status_code == 401


def test_rutas_protegidas_requieren_sesion(cliente):
    assert cliente.get("/api/navegacion/menu").status_code == 401


def test_login_devuelve_ruta_principal_segun_rol(cliente):
    r = cliente.post("/api/auth/login", json={"correo": "analista@labcloud.test", "password": "analista123"})
    assert r.json()["ruta_principal"] == "/muestras/pendientes"


def test_menu_segun_rol(cliente, recepcion, admin):
    assert cliente.get("/api/navegacion/menu", headers=recepcion).json()["estrategia"] == "NavegacionRecepcion"
    assert cliente.get("/api/navegacion/menu", headers=admin).json()["estrategia"] == "NavegacionAdministrador"


def test_comandos_de_navegacion_respetan_el_rol(cliente, recepcion):
    assert cliente.post("/api/navegacion/comandos/ordenes.nueva", headers=recepcion).json()["ruta"] == "/ordenes/nueva"
    assert cliente.post("/api/navegacion/comandos/inventario", headers=recepcion).status_code == 403
    assert cliente.post("/api/navegacion/deshacer", headers=recepcion).json()["ruta"] == "/inicio"


def test_permisos_de_modulos(cliente, recepcion, analista):
    assert cliente.get("/api/inventario", headers=recepcion).status_code == 403
    assert cliente.get("/api/usuarios", headers=analista).status_code == 403
    assert cliente.get("/api/pacientes", headers=recepcion).status_code == 200


def test_flujo_completo_orden_muestra_resultado_con_observer(cliente, recepcion, analista):
    recibidos = []

    class Espia(Observador):
        def actualizar(self, evento):
            recibidos.append(evento.tipo)

    espia = Espia()
    sujeto_eventos.suscribir(espia)
    try:
        paciente = cliente.post("/api/pacientes", headers=recepcion, json={
            "documento": "123456789", "nombres": "Ana", "apellidos": "Prueba"}).json()
        orden = cliente.post("/api/ordenes", headers=recepcion, json={
            "paciente_id": paciente["id"], "examenes": ["glucosa", "colesterol", "hemograma"],
            "prioridad": "urgente"}).json()
        assert len(orden["muestras"]) == 2  # suero + sangre total

        for muestra in orden["muestras"]:
            r = cliente.post(f"/api/muestras/{muestra['id']}/procesar", headers=analista)
            assert r.json()["estado"] == "en_proceso"
            valores = [{"examen": e, "valor": "100"} for e in muestra["examenes"].split(",")]
            r = cliente.post(f"/api/muestras/{muestra['id']}/resultados", headers=analista,
                             json={"valores": valores})
            assert r.json()["estado"] == "procesada"

        ordenes = cliente.get("/api/ordenes", headers=recepcion).json()
        assert next(o for o in ordenes if o["id"] == orden["id"])["estado"] == "completada"
    finally:
        sujeto_eventos.desuscribir(espia)

    assert recibidos[0] == "orden.creada"
    assert "inventario.bajo" in recibidos  # el reactivo de colesterol inicia cerca del mínimo
    assert recibidos[-1] == "orden.completada"
    eventos = cliente.get("/api/eventos", headers=recepcion).json()
    assert eventos[0]["tipo"] == "orden.completada"


def test_resultados_incompletos_son_rechazados(cliente, analista):
    pendiente = cliente.get("/api/muestras?estado=pendiente", headers=analista).json()[0]
    cliente.post(f"/api/muestras/{pendiente['id']}/procesar", headers=analista)
    r = cliente.post(f"/api/muestras/{pendiente['id']}/resultados", headers=analista,
                     json={"valores": [{"examen": "otro", "valor": "1"}]})
    assert r.status_code == 422


def test_registro_y_resumen_de_pruebas_de_navegacion(cliente, recepcion):
    cliente.post("/api/pruebas/resultados", headers=recepcion, json={
        "prueba": "P1", "modo": "convencional", "pasos": 3, "tiempo_ms": 4200, "errores": 1})
    r = cliente.post("/api/pruebas/resultados", headers=recepcion, json={
        "prueba": "P1", "modo": "optimizada", "pasos": 1, "tiempo_ms": 1100, "errores": 0})
    p1 = r.json()[0]
    assert p1["pasos_convencional"] == 3 and p1["pasos_optimizada"] == 1
    assert p1["reduccion_pasos_pct"] == 66.7


def test_admin_crea_usuario_con_rol_registrado(cliente, admin):
    r = cliente.post("/api/usuarios", headers=admin, json={
        "nombre": "Nuevo", "correo": "nuevo@labcloud.test", "password": "secreto1", "rol": "analista"})
    assert r.status_code == 201
    r = cliente.post("/api/usuarios", headers=admin, json={
        "nombre": "Otro", "correo": "otro@labcloud.test", "password": "secreto1", "rol": "auditor"})
    assert r.status_code == 422
