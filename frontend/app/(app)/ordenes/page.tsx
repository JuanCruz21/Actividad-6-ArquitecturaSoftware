"use client";

import { useState } from "react";
import { Aviso, Cargando, Encabezado, Estado, Prioridad, Tarjeta, Vacio } from "@/components/ui";
import { useAlEvento } from "@/lib/eventos";
import { fecha } from "@/lib/formato";
import type { Orden } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

export default function Ordenes() {
  const [estado, setEstado] = useState("");
  const { datos, cargando, error, recargar } = useDatos<Orden[]>(`/api/ordenes${estado ? `?estado=${estado}` : ""}`);
  useAlEvento(["orden.", "muestra."], recargar);

  return (
    <>
      <Encabezado titulo="Órdenes" descripcion="Solicitudes de análisis registradas y su avance." />
      <Tarjeta
        titulo="Listado de órdenes"
        extra={
          <select value={estado} onChange={(e) => setEstado(e.target.value)} style={{ maxWidth: 200 }}>
            <option value="">Todos los estados</option>
            <option value="registrada">Registrada</option>
            <option value="en_proceso">En proceso</option>
            <option value="completada">Completada</option>
          </select>
        }
      >
        {error && <Aviso>{error}</Aviso>}
        {cargando ? (
          <Cargando />
        ) : !datos?.length ? (
          <Vacio>No hay órdenes.</Vacio>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Paciente</th>
                  <th>Muestras</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {datos.map((o) => (
                  <tr key={o.id}>
                    <td>
                      <strong>{o.codigo}</strong> <Prioridad valor={o.prioridad} />
                    </td>
                    <td>
                      {o.paciente_nombre}
                      <br />
                      <small className="tenue">{o.paciente_documento}</small>
                    </td>
                    <td>
                      {o.muestras.map((m) => (
                        <div key={m.id} className="fila">
                          <small>{m.codigo} · {m.tipo}</small> <Estado valor={m.estado} />
                        </div>
                      ))}
                    </td>
                    <td><Estado valor={o.estado} /></td>
                    <td>{fecha(o.creado_en)}</td>
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
