"use client";

import { useState } from "react";
import { Aviso, Cargando, Encabezado, Tarjeta, Vacio } from "@/components/ui";
import { useAlEvento } from "@/lib/eventos";
import { fecha } from "@/lib/formato";
import type { Resultado } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

export default function Resultados() {
  const [busqueda, setBusqueda] = useState("");
  const { datos, cargando, error, recargar } = useDatos<Resultado[]>(
    `/api/resultados${busqueda ? `?q=${encodeURIComponent(busqueda)}` : ""}`,
  );
  useAlEvento(["muestra.procesada"], recargar);

  return (
    <>
      <Encabezado titulo="Resultados" descripcion="Resultados registrados por el laboratorio." />
      <Tarjeta
        extra={
          <input
            type="search"
            placeholder="Buscar por muestra, orden o documento"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            style={{ maxWidth: 320 }}
          />
        }
        titulo="Listado"
      >
        {error && <Aviso>{error}</Aviso>}
        {cargando ? (
          <Cargando />
        ) : !datos?.length ? (
          <Vacio>Sin resultados.</Vacio>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Muestra</th>
                  <th>Paciente</th>
                  <th>Examen</th>
                  <th className="num">Valor</th>
                  <th>Referencia</th>
                  <th>Analista</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {datos.map((r) => (
                  <tr key={r.id}>
                    <td>
                      {r.muestra_codigo}
                      <br />
                      <small className="tenue">{r.orden_codigo}</small>
                    </td>
                    <td>{r.paciente_nombre}</td>
                    <td>
                      {r.examen}
                      {r.observaciones && (
                        <>
                          <br />
                          <small className="tenue">{r.observaciones}</small>
                        </>
                      )}
                    </td>
                    <td className="num">{r.valor} {r.unidad}</td>
                    <td>{r.referencia}</td>
                    <td>{r.analista_nombre ?? "—"}</td>
                    <td>{fecha(r.registrado_en)}</td>
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
