"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { Aviso, Cargando, Encabezado, Prioridad, Tarjeta, Vacio } from "@/components/ui";
import { api } from "@/lib/api";
import { useAlEvento } from "@/lib/eventos";
import { fecha } from "@/lib/formato";
import type { Muestra } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

function CapturaResultados({ muestra, alGuardar }: { muestra: Muestra; alGuardar: (codigo: string) => void }) {
  const [valores, setValores] = useState<Record<string, { valor: string; observaciones: string }>>({});
  const [error, setError] = useState<string | null>(null);
  const destacada = useSearchParams().get("muestra") === String(muestra.id);

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api(`/api/muestras/${muestra.id}/resultados`, {
        method: "POST",
        body: {
          valores: (muestra.examenes_detalle ?? []).map((ex) => ({
            examen: ex.clave,
            valor: valores[ex.clave]?.valor ?? "",
            observaciones: valores[ex.clave]?.observaciones || null,
          })),
        },
      });
      alGuardar(muestra.codigo);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const cambiar = (clave: string, campo: "valor" | "observaciones", v: string) =>
    setValores((prev) => ({ ...prev, [clave]: { ...(prev[clave] ?? { valor: "", observaciones: "" }), [campo]: v } }));

  return (
    <div style={destacada ? { outline: "2px solid var(--primario)", borderRadius: "var(--radio)" } : undefined}>
      <Tarjeta
        titulo={`${muestra.codigo} · ${muestra.tipo}`}
        extra={<small className="tenue">Iniciada {fecha(muestra.iniciada_en)}</small>}
      >
        <p className="tenue">
          {muestra.orden_codigo} · {muestra.paciente_nombre} <Prioridad valor={muestra.prioridad} />
        </p>
        {error && <Aviso>{error}</Aviso>}
        <form onSubmit={guardar} style={{ display: "grid", gap: 12 }}>
          {muestra.examenes_detalle?.map((ex) => (
            <div key={ex.clave} className="formulario">
              <label>
                {ex.nombre} {ex.unidad && `(${ex.unidad})`} · ref. {ex.referencia}
                <input
                  required
                  value={valores[ex.clave]?.valor ?? ""}
                  onChange={(e) => cambiar(ex.clave, "valor", e.target.value)}
                />
              </label>
              <label>
                Observaciones
                <input
                  value={valores[ex.clave]?.observaciones ?? ""}
                  onChange={(e) => cambiar(ex.clave, "observaciones", e.target.value)}
                />
              </label>
            </div>
          ))}
          <div>
            <button className="boton">Registrar resultados</button>
          </div>
        </form>
      </Tarjeta>
    </div>
  );
}

function Procesamiento() {
  const { datos, cargando, error, recargar } = useDatos<Muestra[]>("/api/muestras?estado=en_proceso");
  const [exito, setExito] = useState<string | null>(null);
  useAlEvento(["muestra."], recargar);

  return (
    <>
      <Encabezado titulo="Procesamiento" descripcion="Muestras en análisis: captura los resultados para finalizarlas." />
      {exito && <Aviso tipo="exito">{exito}</Aviso>}
      {error && <Aviso>{error}</Aviso>}
      {cargando ? (
        <Cargando />
      ) : !datos?.length ? (
        <Tarjeta>
          <Vacio>No hay muestras en procesamiento. Inicia una desde “Muestras pendientes”.</Vacio>
        </Tarjeta>
      ) : (
        datos.map((m) => (
          <CapturaResultados
            key={m.id}
            muestra={m}
            alGuardar={(codigo) => {
              setExito(`Resultados de ${codigo} registrados.`);
              recargar();
            }}
          />
        ))
      )}
    </>
  );
}

export default function PaginaProcesamiento() {
  return (
    <Suspense>
      <Procesamiento />
    </Suspense>
  );
}
