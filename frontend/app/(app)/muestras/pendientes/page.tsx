"use client";

import { Play } from "lucide-react";
import { useState } from "react";
import { Aviso, Cargando, Encabezado, Prioridad, Tarjeta, Vacio } from "@/components/ui";
import { api } from "@/lib/api";
import { useAlEvento } from "@/lib/eventos";
import { fecha } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { Muestra } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

export default function MuestrasPendientes() {
  const { navegar } = useSesion();
  const { datos, cargando, error, recargar } = useDatos<Muestra[]>("/api/muestras?estado=pendiente");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [nuevas, setNuevas] = useState(0);
  useAlEvento(["orden.creada", "muestra."], (evento) => {
    if (evento.tipo === "orden.creada") setNuevas((n) => n + 1);
    recargar();
  });

  const procesar = async (m: Muestra) => {
    try {
      await api(`/api/muestras/${m.id}/procesar`, { method: "POST" });
      await navegar("procesamiento", `muestra=${m.id}`);
    } catch (err) {
      setMensaje((err as Error).message);
    }
  };

  return (
    <>
      <Encabezado
        titulo="Muestras pendientes"
        descripcion="Muestras en espera de análisis. Las urgentes aparecen primero."
        acciones={nuevas > 0 && <span className="insignia estado-en_proceso">{nuevas} nueva(s) desde que abriste</span>}
      />
      {(error || mensaje) && <Aviso>{error ?? mensaje}</Aviso>}
      <Tarjeta>
        {cargando ? (
          <Cargando />
        ) : !datos?.length ? (
          <Vacio>No hay muestras pendientes. 🎉</Vacio>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Muestra</th>
                  <th>Tipo</th>
                  <th>Exámenes</th>
                  <th>Paciente</th>
                  <th>Recibida</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {datos.map((m) => (
                  <tr key={m.id}>
                    <td>
                      <strong>{m.codigo}</strong> <Prioridad valor={m.prioridad} />
                      <br />
                      <small className="tenue">{m.orden_codigo}</small>
                    </td>
                    <td>{m.tipo}</td>
                    <td>{m.examenes_detalle?.map((e) => e.nombre).join(", ")}</td>
                    <td>{m.paciente_nombre}</td>
                    <td>{fecha(m.creado_en)}</td>
                    <td>
                      <button className="boton pequeno" onClick={() => procesar(m)}>
                        <Play size={14} /> Procesar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Tarjeta>
    </>
  );
}
