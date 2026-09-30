"""Dependencias compartidas: conexión, usuario autenticado y control de acceso por rol."""

import sqlite3
from typing import Annotated

from fastapi import Depends, Header

from labcloud.datos.database import obtener_conexion
from labcloud.negocio.errores import AccesoDenegado, NoAutenticado
from labcloud.negocio.servicios import ServicioUsuarios

Conexion = Annotated[sqlite3.Connection, Depends(obtener_conexion)]


def obtener_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise NoAutenticado("Debes iniciar sesión")
    return authorization.split(" ", 1)[1].strip()


def usuario_actual(conn: Conexion, token: Annotated[str, Depends(obtener_token)]) -> dict:
    return ServicioUsuarios(conn).usuario_por_token(token)


UsuarioActual = Annotated[dict, Depends(usuario_actual)]


def requiere_roles(*roles: str):
    def verificar(usuario: UsuarioActual) -> dict:
        if usuario["rol"] not in roles:
            raise AccesoDenegado("Tu rol no tiene acceso a esta funcionalidad")
        return usuario

    return Depends(verificar)
