import type { ReactNode } from "react";
import { ETIQUETAS_ESTADO } from "@/lib/formato";

export function Encabezado({ titulo, descripcion, acciones }: { titulo: string; descripcion?: string; acciones?: ReactNode }) {
  return (
    <header className="encabezado">
      <div>
        <h1>{titulo}</h1>
        {descripcion && <p className="tenue">{descripcion}</p>}
      </div>
      {acciones && <div className="acciones">{acciones}</div>}
    </header>
  );
}

export function Tarjeta({ titulo, children, extra }: { titulo?: string; children: ReactNode; extra?: ReactNode }) {
  return (
    <section className="tarjeta">
      {(titulo || extra) && (
        <div className="tarjeta-cabecera">
          {titulo && <h2>{titulo}</h2>}
          {extra}
        </div>
      )}
      {children}
    </section>
  );
}

export function Estado({ valor }: { valor: string }) {
  return <span className={`insignia estado-${valor}`}>{ETIQUETAS_ESTADO[valor] ?? valor}</span>;
}

export function Prioridad({ valor }: { valor?: string }) {
  return valor === "urgente" ? <span className="insignia urgente">Urgente</span> : null;
}

export function Vacio({ children }: { children: ReactNode }) {
  return <p className="vacio">{children}</p>;
}

export function Aviso({ tipo = "error", children }: { tipo?: "error" | "exito" | "info"; children: ReactNode }) {
  return <div className={`aviso aviso-${tipo}`} role={tipo === "error" ? "alert" : "status"}>{children}</div>;
}

export function Cargando() {
  return <p className="tenue">Cargando…</p>;
}
