"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Aviso, Cargando, Encabezado, Estado, Prioridad, Tarjeta, Vacio } from "@/components/ui";
import { useAlEvento } from "@/lib/eventos";
import { fecha } from "@/lib/formato";
import type { Muestra } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

function LineaTiempo({ m }: { m: Muestra }) {
  const pasos = [
    { etiqueta: "Recibida", fecha: m.creado_en, hecho: true },
    { etiqueta: "En proceso", fecha: m.iniciada_en, hecho: !!m.iniciada_en },
    { etiqueta: "Procesada", fecha: m.procesada_en, hecho: !!m.procesada_en },
  ];
  const actual = pasos.findLastIndex((p) => p.hecho);
  return (
    <div className="linea-tiempo">
      {pasos.map((p, i) => (
        <div key={p.etiqueta} className={`paso ${p.hecho ? "hecho" : ""} ${i === actual + 1 ? "actual" : ""}`}>
          <strong>{p.etiqueta}</strong>
          <small>{p.hecho ? fecha(p.fecha) : "Pendiente"}</small>
        </div>
      ))}
    </div>
  );
}

function Seguimiento() {
  const parametros = useSearchParams();
  const [termino, setTermino] = useState(parametros.get("q") ?? "");
  const { datos, cargando, error, recargar } = useDatos<Muestra[]>(
    `/api/muestras${termino.trim() ? `?q=${encodeURIComponent(termino.trim())}` : ""}`,
  );
  useAlEvento(["muestra.", "orden."], recargar);

  return (
    <>
      <Encabezado
        titulo="Seguimiento de muestra"
        descripcion="Consulta el estado de las muestras por código de orden, muestra o documento. Se actualiza en tiempo real."
      />
      <Tarjeta>
        <input
          type="search"
          placeholder="Ej.: ORD-00003, MUE-00004 o 52987654"
          value={termino}
          onChange={(e) => setTermino(e.target.value)}
          autoFocus
        />
      </Tarjeta>
      {error && <Aviso>{error}</Aviso>}
      {cargando ? (
        <Cargando />
      ) : !datos?.length ? (
        <Vacio>No se encontraron muestras.</Vacio>
      ) : (
        datos.slice(0, 25).map((m) => (
          <Tarjeta
            key={m.id}
            titulo={`${m.codigo} · ${m.tipo}`}
            extra={
              <div className="fila">
                <Prioridad valor={m.prioridad} />
                <Estado valor={m.estado} />
              </div>
            }
          >
            <p className="tenue">
              Orden {m.orden_codigo} · {m.paciente_nombre} ({m.paciente_documento}) ·{" "}
              {m.examenes_detalle?.map((e) => e.nombre).join(", ")}
            </p>
            <LineaTiempo m={m} />
            {!!m.resultados?.length && (
              <table>
                <thead>
                  <tr>
                    <th>Examen</th>
                    <th className="num">Valor</th>
                    <th>Referencia</th>
                  </tr>
                </thead>
                <tbody>
                  {m.resultados.map((r) => (
                    <tr key={r.id}>
                      <td>{r.examen}</td>
                      <td className="num">{r.valor} {r.unidad}</td>
                      <td>{r.referencia}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Tarjeta>
        ))
      )}
    </>
  );
}

export default function PaginaSeguimiento() {
  return (
    <Suspense>
      <Seguimiento />
    </Suspense>
  );
}
