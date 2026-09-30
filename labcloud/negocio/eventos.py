"""Patrón Observer: notifica cambios de estado de órdenes, muestras e inventario.

`SujetoEventos` es el sujeto; cada `Observador` reacciona a los eventos publicados
(persistirlos, difundirlos a la interfaz en tiempo real, etc.).
"""

import asyncio
import json
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from labcloud.datos import database
from labcloud.datos.repositorios import RepositorioEventos


@dataclass
class Evento:
    tipo: str
    mensaje: str
    roles: list[str]
    entidad: str | None = None
    entidad_id: int | None = None
    id: int | None = None
    creado_en: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))


class Observador(ABC):
    @abstractmethod
    def actualizar(self, evento: Evento) -> None: ...


class SujetoEventos:
    def __init__(self) -> None:
        self._observadores: list[Observador] = []

    def suscribir(self, observador: Observador) -> None:
        if observador not in self._observadores:
            self._observadores.append(observador)

    def desuscribir(self, observador: Observador) -> None:
        self._observadores.remove(observador)

    def notificar(self, evento: Evento) -> None:
        for observador in list(self._observadores):
            observador.actualizar(evento)


class RegistroEventosObserver(Observador):
    """Persiste cada evento para que la interfaz muestre el historial de notificaciones."""

    def actualizar(self, evento: Evento) -> None:
        conn = database.conectar()
        try:
            evento.id = RepositorioEventos(conn).registrar(
                evento.tipo, evento.mensaje, evento.entidad, evento.entidad_id, evento.roles
            )
            conn.commit()
        finally:
            conn.close()


@dataclass(eq=False)
class _Suscriptor:
    rol: str
    cola: asyncio.Queue
    loop: asyncio.AbstractEventLoop


class DifusorTiempoRealObserver(Observador):
    """Envía los eventos a las interfaces conectadas (Server-Sent Events) según su rol."""

    def __init__(self) -> None:
        self._suscriptores: set[_Suscriptor] = set()
        self._lock = threading.Lock()

    def conectar(self, rol: str) -> _Suscriptor:
        suscriptor = _Suscriptor(rol, asyncio.Queue(maxsize=100), asyncio.get_running_loop())
        with self._lock:
            self._suscriptores.add(suscriptor)
        return suscriptor

    def desconectar(self, suscriptor: _Suscriptor) -> None:
        with self._lock:
            self._suscriptores.discard(suscriptor)

    def actualizar(self, evento: Evento) -> None:
        carga = json.dumps(asdict(evento), ensure_ascii=False)
        with self._lock:
            destinatarios = [s for s in self._suscriptores if s.rol in evento.roles]
        for s in destinatarios:
            s.loop.call_soon_threadsafe(self._encolar, s.cola, carga)

    @staticmethod
    def _encolar(cola: asyncio.Queue, carga: str) -> None:
        if not cola.full():
            cola.put_nowait(carga)


sujeto_eventos = SujetoEventos()
difusor_tiempo_real = DifusorTiempoRealObserver()
sujeto_eventos.suscribir(RegistroEventosObserver())
sujeto_eventos.suscribir(difusor_tiempo_real)
