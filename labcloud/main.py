"""Punto de entrada del monolito: API + interfaz web compilada servidas por un único proceso."""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from labcloud import config
from labcloud.datos import database
from labcloud.datos.seed import cargar_datos_demo
from labcloud.negocio.errores import ErrorNegocio
from labcloud.presentacion.rutas import ROUTERS


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    conn = database.conectar()
    try:
        database.inicializar(conn)
        cargar_datos_demo(conn)
    finally:
        conn.close()
    yield


class InterfazEstatica(StaticFiles):
    """Sirve el export de Next.js y responde con su 404.html para rutas inexistentes."""

    async def get_response(self, path, scope):
        respuesta = await super().get_response(path, scope)
        if respuesta.status_code == 404:
            pagina = self.directory / "404.html"
            if pagina.exists():
                return FileResponse(pagina, status_code=404)
        return respuesta


def crear_app() -> FastAPI:
    app = FastAPI(title="LabCloud Intelligent", version="0.1.0", lifespan=ciclo_de_vida)

    @app.exception_handler(ErrorNegocio)
    async def manejar_error_negocio(request: Request, exc: ErrorNegocio):
        return JSONResponse(status_code=exc.estado_http, content={"detail": exc.mensaje})

    @app.get("/api/salud", tags=["sistema"])
    def salud():
        return {"estado": "ok"}

    for router in ROUTERS:
        app.include_router(router)

    if config.FRONTEND_DIR.exists():
        app.mount("/", InterfazEstatica(directory=config.FRONTEND_DIR, html=True), name="interfaz")
    else:
        @app.get("/", include_in_schema=False)
        def sin_interfaz():
            return JSONResponse({
                "mensaje": "API de LabCloud activa. Compila la interfaz con 'make build' "
                           "(o 'cd frontend && npm run build') para servirla desde este mismo proceso.",
                "documentacion": "/docs",
            })

    return app


app = crear_app()


def run() -> None:
    uvicorn.run("labcloud.main:app", host=config.HOST, port=config.PORT)
