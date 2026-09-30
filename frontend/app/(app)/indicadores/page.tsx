"use client";

import { Aviso, Cargando, Encabezado, Tarjeta, Vacio } from "@/components/ui";
import { TablaResumen } from "@/components/TablaResumen";
import { useAlEvento } from "@/lib/eventos";
import { ETIQUETAS_ESTADO } from "@/lib/formato";
import type { FilaResumenPrueba, Insumo } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

interface Resumen {
  pacientes: number;
  usuarios: number;
  ordenes_por_estado: Record<string, number>;
  muestras_por_estado: Record<string, number>;
  minutos_promedio_procesamiento: number | null;
  inventario_bajo: Insumo[];
  navegacion: FilaResumenPrueba[];
}

function Barras({ datos, orden }: { datos: Record<string, number>; orden: string[] }) {
  const maximo = Math.max(1, ...Object.values(datos));
  return (
    <div className="barras">
      {orden.map((estado) => (
        <div key={estado} className="barra">
          <span>{ETIQUETAS_ESTADO[estado]}</span>
          <div className="barra-pista">
            <div className="barra-relleno" style={{ width: `${((datos[estado] ?? 0) / maximo) * 100}%` }} />
          </div>
          <strong className="num">{datos[estado] ?? 0}</strong>
        </div>
      ))}
    </div>
  );
}

export default function Indicadores() {
  const { datos, cargando, error, recargar } = useDatos<Resumen>("/api/indicadores");
  useAlEvento(["orden.", "muestra.", "inventario."], recargar);
  if (cargando) return <Cargando />;
  if (error || !datos) return <Aviso>{error}</Aviso>;

  const total = (r: Record<string, number>) => Object.values(r).reduce((a, b) => a + b, 0);

  return (
    <>
      <Encabezado titulo="Indicadores" descripcion="Información consolidada del laboratorio, actualizada en tiempo real." />
      <div className="metricas">
        <div className="metrica"><span>Pacientes</span><strong>{datos.pacientes}</strong></div>
        <div className="metrica"><span>Órdenes</span><strong>{total(datos.ordenes_por_estado)}</strong></div>
        <div className="metrica"><span>Muestras</span><strong>{total(datos.muestras_por_estado)}</strong></div>
        <div className="metrica">
          <span>Tiempo medio recepción → resultado</span>
          <strong>{datos.minutos_promedio_procesamiento != null ? `${datos.minutos_promedio_procesamiento} min` : "—"}</strong>
        </div>
        <div className="metrica"><span>Insumos bajo mínimo</span><strong>{datos.inventario_bajo.length}</strong></div>
      </div>
      <div className="rejilla">
        <Tarjeta titulo="Órdenes por estado">
          <Barras datos={datos.ordenes_por_estado} orden={["registrada", "en_proceso", "completada"]} />
        </Tarjeta>
        <Tarjeta titulo="Muestras por estado">
          <Barras datos={datos.muestras_por_estado} orden={["pendiente", "en_proceso", "procesada"]} />
        </Tarjeta>
        <Tarjeta titulo="Alertas de inventario">
          {datos.inventario_bajo.length === 0 ? (
            <Vacio>Sin alertas.</Vacio>
          ) : (
            <ul className="lista-eventos">
              {datos.inventario_bajo.map((i) => (
                <li key={i.id} className="evento evento-inventario">
                  <span>{i.nombre}</span>
                  <time>{i.cantidad} {i.unidad} · mínimo {i.minimo}</time>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>
      </div>
      <Tarjeta titulo="Navegación: convencional vs. optimizada (promedios)">
        <TablaResumen filas={datos.navegacion} />
      </Tarjeta>
    </>
  );
}
