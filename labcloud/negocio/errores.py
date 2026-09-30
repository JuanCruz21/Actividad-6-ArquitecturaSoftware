"""Errores de dominio, traducidos a respuestas HTTP por la capa de presentación."""


class ErrorNegocio(Exception):
    estado_http = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoAutenticado(ErrorNegocio):
    estado_http = 401


class AccesoDenegado(ErrorNegocio):
    estado_http = 403


class NoEncontrado(ErrorNegocio):
    estado_http = 404


class Conflicto(ErrorNegocio):
    estado_http = 409


class DatosInvalidos(ErrorNegocio):
    estado_http = 422
