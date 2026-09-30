"""Esquemas de entrada de la API (validación con Pydantic)."""

from typing import Literal

from pydantic import BaseModel, Field


class Credenciales(BaseModel):
    correo: str = Field(min_length=3)
    password: str = Field(min_length=1)


class NuevoUsuario(BaseModel):
    nombre: str = Field(min_length=2)
    correo: str = Field(min_length=5, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6)
    rol: str


class EstadoUsuario(BaseModel):
    activo: bool


class NuevoPaciente(BaseModel):
    documento: str = Field(min_length=5, max_length=20)
    nombres: str = Field(min_length=2)
    apellidos: str = Field(min_length=2)
    fecha_nacimiento: str | None = None
    telefono: str | None = None
    correo: str | None = None


class NuevaOrden(BaseModel):
    paciente_id: int
    examenes: list[str] = Field(min_length=1)
    prioridad: Literal["normal", "urgente"] = "normal"


class ValorResultado(BaseModel):
    examen: str
    valor: str
    observaciones: str | None = None


class RegistroResultados(BaseModel):
    valores: list[ValorResultado] = Field(min_length=1)


class NuevoInsumo(BaseModel):
    nombre: str = Field(min_length=2)
    lote: str = Field(min_length=1)
    cantidad: int = Field(ge=0)
    minimo: int = Field(ge=0)
    unidad: str = "unidades"
    vencimiento: str | None = None


class AjusteInventario(BaseModel):
    delta: int


class ResultadoPrueba(BaseModel):
    prueba: Literal["P1", "P2", "P3"]
    modo: Literal["convencional", "optimizada"]
    pasos: int = Field(ge=0)
    tiempo_ms: int = Field(ge=0)
    errores: int = Field(ge=0)
    recorrido: list[str] | None = None
