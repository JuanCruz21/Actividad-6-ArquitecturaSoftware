"use client";

import { Bell } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useEventos } from "@/lib/eventos";
import { fecha } from "@/lib/formato";

export function Notificaciones() {
  const { notificaciones, noLeidas, marcarLeidas, conectado } = useEventos();
  const [abierto, setAbierto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cerrar = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false);
    };
    document.addEventListener("mousedown", cerrar);
    return () => document.removeEventListener("mousedown", cerrar);
  }, []);

  return (
    <div className="notificaciones" ref={ref}>
      <button
        className="boton-icono"
        aria-label={`Notificaciones (${noLeidas} sin leer)`}
        onClick={() => {
          setAbierto((a) => !a);
          marcarLeidas();
        }}
      >
        <Bell size={18} />
        {noLeidas > 0 && <span className="contador">{noLeidas}</span>}
      </button>
      {abierto && (
        <div className="panel-notificaciones">
          <div className="panel-cabecera">
            <strong>Notificaciones</strong>
            <span className={`punto ${conectado ? "activo" : ""}`} title={conectado ? "En vivo" : "Reconectando"}>
              {conectado ? "En vivo" : "Reconectando…"}
            </span>
          </div>
          {notificaciones.length === 0 ? (
            <p className="vacio">Sin notificaciones</p>
          ) : (
            <ul>
              {notificaciones.map((n, i) => (
                <li key={`${n.id}-${i}`} className={`evento evento-${n.tipo.split(".")[0]}`}>
                  <span>{n.mensaje}</span>
                  <time>{fecha(n.creado_en)}</time>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
