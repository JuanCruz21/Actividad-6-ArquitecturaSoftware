"use client";

import { Minus, Plus, TriangleAlert } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Aviso, Cargando, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { useAlEvento } from "@/lib/eventos";
import type { Insumo } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const VACIO = { nombre: "", lote: "", cantidad: "0", minimo: "0", unidad: "unidades", vencimiento: "" };

export default function Inventario() {
  const { datos, cargando, error, recargar } = useDatos<Insumo[]>("/api/inventario");
  const [formulario, setFormulario] = useState(VACIO);
  const [abierto, setAbierto] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  useAlEvento(["inventario."], recargar);

  const ajustar = async (item: Insumo, delta: number) => {
    try {
      await api(`/api/inventario/${item.id}/ajuste`, { method: "POST", body: { delta } });
      recargar();
    } catch (err) {
      setMensaje((err as Error).message);
    }
  };

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/api/inventario", {
        method: "POST",
        body: {
          ...formulario,
          cantidad: Number(formulario.cantidad),
          minimo: Number(formulario.minimo),
          vencimiento: formulario.vencimiento || null,
        },
      });
      setFormulario(VACIO);
      setAbierto(false);
      recargar();
    } catch (err) {
      setMensaje((err as Error).message);
    }
  };

  const bajos = datos?.filter((i) => i.bajo_minimo).length ?? 0;

  return (
    <>
      <Encabezado
        titulo="Inventario"
        descripcion="Existencias, lotes y alertas. El consumo de reactivos se descuenta al procesar muestras."
        acciones={
          <button className="boton" onClick={() => setAbierto((a) => !a)}>
            <Plus size={16} /> Nuevo insumo
          </button>
        }
      />
      {bajos > 0 && (
        <Aviso tipo="info">
          <TriangleAlert size={14} style={{ verticalAlign: "-2px" }} /> {bajos} insumo(s) en o por debajo del mínimo.
        </Aviso>
      )}
      {(error || mensaje) && <Aviso>{error ?? mensaje}</Aviso>}
      {abierto && (
        <Tarjeta titulo="Nuevo insumo">
          <form className="formulario" onSubmit={crear}>
            {(
              [
                ["nombre", "Nombre", "text"],
                ["lote", "Lote", "text"],
                ["cantidad", "Cantidad", "number"],
                ["minimo", "Mínimo", "number"],
                ["unidad", "Unidad", "text"],
                ["vencimiento", "Vencimiento", "date"],
              ] as const
            ).map(([clave, etiqueta, tipo]) => (
              <label key={clave}>
                {etiqueta}
                <input
                  type={tipo}
                  min={tipo === "number" ? 0 : undefined}
                  required={clave !== "vencimiento"}
                  value={formulario[clave]}
                  onChange={(e) => setFormulario({ ...formulario, [clave]: e.target.value })}
                />
              </label>
            ))}
            <button className="boton">Guardar</button>
          </form>
        </Tarjeta>
      )}
      <Tarjeta>
        {cargando ? (
          <Cargando />
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Insumo</th>
                  <th>Lote</th>
                  <th className="num">Cantidad</th>
                  <th className="num">Mínimo</th>
                  <th>Vencimiento</th>
                  <th>Ajustar</th>
                </tr>
              </thead>
              <tbody>
                {datos?.map((i) => (
                  <tr key={i.id} className={i.bajo_minimo ? "alerta" : ""}>
                    <td>
                      {i.nombre} {i.bajo_minimo ? <span className="insignia estado-pendiente">Bajo mínimo</span> : null}
                    </td>
                    <td>{i.lote}</td>
                    <td className="num">{i.cantidad} {i.unidad}</td>
                    <td className="num">{i.minimo}</td>
                    <td>{i.vencimiento ?? "—"}</td>
                    <td>
                      <div className="fila">
                        <button className="boton-icono" aria-label={`Restar 1 a ${i.nombre}`} onClick={() => ajustar(i, -1)}>
                          <Minus size={14} />
                        </button>
                        <button className="boton-icono" aria-label={`Sumar 10 a ${i.nombre}`} onClick={() => ajustar(i, 10)}>
                          +10
                        </button>
                      </div>
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
