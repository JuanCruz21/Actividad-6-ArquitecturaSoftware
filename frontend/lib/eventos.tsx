"use client";

// Patrón Observer en la interfaz: el proveedor recibe los eventos del backend (Server-Sent
// Events) y notifica a los componentes suscritos para que actualicen su información.

import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { api, leerToken, urlApi } from "./api";
import type { EventoSistema } from "./tipos";

type Oyente = (evento: EventoSistema) => void;

interface ContextoEventos {
  notificaciones: EventoSistema[];
  noLeidas: number;
  conectado: boolean;
  marcarLeidas: () => void;
  suscribir: (oyente: Oyente) => () => void;
}

const Contexto = createContext<ContextoEventos | null>(null);

export function EventosProvider({ children }: { children: ReactNode }) {
  const oyentes = useRef(new Set<Oyente>());
  const [notificaciones, setNotificaciones] = useState<EventoSistema[]>([]);
  const [noLeidas, setNoLeidas] = useState(0);
  const [conectado, setConectado] = useState(false);

  useEffect(() => {
    api<EventoSistema[]>("/api/eventos").then(setNotificaciones).catch(() => undefined);

    const control = new AbortController();
    let reintento: ReturnType<typeof setTimeout> | undefined;

    const publicar = (evento: EventoSistema) => {
      setNotificaciones((previas) => [evento, ...previas].slice(0, 30));
      setNoLeidas((n) => n + 1);
      oyentes.current.forEach((oyente) => oyente(evento));
    };

    const conectar = async () => {
      try {
        const token = leerToken();
        if (!token) return;
        const respuesta = await fetch(urlApi("/api/eventos/stream"), {
          headers: { Authorization: `Bearer ${token}` },
          signal: control.signal,
        });
        if (!respuesta.ok || !respuesta.body) throw new Error("sin flujo");
        setConectado(true);
        const lector = respuesta.body.pipeThrough(new TextDecoderStream()).getReader();
        let bufer = "";
        for (;;) {
          const { value, done } = await lector.read();
          if (done) break;
          bufer += value;
          let corte: number;
          while ((corte = bufer.indexOf("\n\n")) >= 0) {
            const bloque = bufer.slice(0, corte);
            bufer = bufer.slice(corte + 2);
            const lineas = bloque.split("\n");
            const tipo = lineas.find((l) => l.startsWith("event:"))?.slice(6).trim();
            const datos = lineas.find((l) => l.startsWith("data:"))?.slice(5).trim();
            if (tipo === "evento" && datos) publicar(JSON.parse(datos));
          }
        }
      } catch {
        /* se reintenta abajo */
      }
      setConectado(false);
      if (!control.signal.aborted) reintento = setTimeout(conectar, 3000);
    };

    conectar();
    return () => {
      control.abort();
      clearTimeout(reintento);
    };
  }, []);

  const suscribir = useCallback((oyente: Oyente) => {
    oyentes.current.add(oyente);
    return () => {
      oyentes.current.delete(oyente);
    };
  }, []);

  const marcarLeidas = useCallback(() => setNoLeidas(0), []);

  return (
    <Contexto.Provider value={{ notificaciones, noLeidas, conectado, marcarLeidas, suscribir }}>
      {children}
    </Contexto.Provider>
  );
}

export function useEventos() {
  const ctx = useContext(Contexto);
  if (!ctx) throw new Error("useEventos debe usarse dentro de EventosProvider");
  return ctx;
}

/** Ejecuta `alRecibir` cada vez que llega un evento cuyo tipo empieza por alguno de los prefijos. */
export function useAlEvento(prefijos: string[], alRecibir: (evento: EventoSistema) => void) {
  const { suscribir } = useEventos();
  const callback = useRef(alRecibir);
  callback.current = alRecibir;
  const clave = prefijos.join("|");
  useEffect(
    () =>
      suscribir((evento) => {
        if (clave.split("|").some((p) => evento.tipo.startsWith(p))) callback.current(evento);
      }),
    [suscribir, clave],
  );
}
