"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState, type FormEvent } from "react";
import { Aviso, Encabezado, Estado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { useSesion } from "@/lib/sesion";
import type { Examen, Orden, Paciente } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

function FormularioOrden() {
  const parametros = useSearchParams();
  const { navegar } = useSesion();
  const { datos: pacientes } = useDatos<Paciente[]>("/api/pacientes");
  const { datos: examenes } = useDatos<Examen[]>("/api/ordenes/examenes");
  const [pacienteId, setPacienteId] = useState(parametros.get("paciente") ?? "");
  const [seleccion, setSeleccion] = useState<string[]>([]);
  const [prioridad, setPrioridad] = useState<"normal" | "urgente">("normal");
  const [error, setError] = useState<string | null>(null);
  const [creada, setCreada] = useState<Orden | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    const p = parametros.get("paciente");
    if (p) setPacienteId(p);
  }, [parametros]);

  const porTipo = useMemo(() => {
    const grupos: Record<string, Examen[]> = {};
    examenes?.forEach((e) => (grupos[e.tipo_muestra] ??= []).push(e));
    return grupos;
  }, [examenes]);

  const alternar = (clave: string) =>
    setSeleccion((s) => (s.includes(clave) ? s.filter((c) => c !== clave) : [...s, clave]));

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      const orden = await api<Orden>("/api/ordenes", {
        method: "POST",
        body: { paciente_id: Number(pacienteId), examenes: seleccion, prioridad },
      });
      setCreada(orden);
      setSeleccion([]);
      setPrioridad("normal");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <>
      <Encabezado titulo="Nueva orden" descripcion="Registra una solicitud de análisis; las muestras se generan por tipo." />
      {creada && (
        <Aviso tipo="exito">
          Orden <strong>{creada.codigo}</strong> creada para {creada.paciente_nombre}. Se generaron{" "}
          {creada.muestras.length} muestra(s): {creada.muestras.map((m) => `${m.codigo} (${m.tipo})`).join(", ")}.{" "}
          <button className="boton secundario pequeno" onClick={() => navegar("muestras.seguimiento", `q=${creada.codigo}`)}>
            Ver seguimiento
          </button>
        </Aviso>
      )}
      {error && <Aviso>{error}</Aviso>}
      <Tarjeta>
        <form onSubmit={enviar} style={{ display: "grid", gap: 16 }}>
          <div className="formulario">
            <label>
              Paciente
              <select value={pacienteId} onChange={(e) => setPacienteId(e.target.value)} required>
                <option value="">Selecciona un paciente…</option>
                {pacientes?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.documento} — {p.nombres} {p.apellidos}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Prioridad
              <select value={prioridad} onChange={(e) => setPrioridad(e.target.value as "normal" | "urgente")}>
                <option value="normal">Normal</option>
                <option value="urgente">Urgente</option>
              </select>
            </label>
          </div>
          <div className="examenes">
            {Object.entries(porTipo).map(([tipo, lista]) => (
              <fieldset key={tipo} className="grupo-examenes">
                <h3>{tipo}</h3>
                {lista.map((ex) => (
                  <label key={ex.clave} className="check">
                    <input type="checkbox" checked={seleccion.includes(ex.clave)} onChange={() => alternar(ex.clave)} />
                    {ex.nombre}
                  </label>
                ))}
              </fieldset>
            ))}
          </div>
          <div className="fila">
            <button className="boton" disabled={enviando || !pacienteId || seleccion.length === 0}>
              {enviando ? "Creando…" : `Crear orden (${seleccion.length} examen${seleccion.length === 1 ? "" : "es"})`}
            </button>
            {creada && <Estado valor={creada.estado} />}
          </div>
        </form>
      </Tarjeta>
    </>
  );
}

export default function NuevaOrden() {
  return (
    <Suspense>
      <FormularioOrden />
    </Suspense>
  );
}
