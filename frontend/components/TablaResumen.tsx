import { segundos } from "@/lib/formato";
import type { FilaResumenPrueba } from "@/lib/tipos";

const n = (v: number | null) => (v == null ? "—" : v);

/** Tabla 6 del documento: registro de resultados de las pruebas de navegación. */
export function TablaResumen({ filas }: { filas: FilaResumenPrueba[] }) {
  return (
    <div className="tabla-contenedor">
      <table>
        <thead>
          <tr>
            <th>Prueba</th>
            <th className="num">Pasos conv.</th>
            <th className="num">Pasos opt.</th>
            <th className="num">Reducción pasos</th>
            <th className="num">Tiempo conv.</th>
            <th className="num">Tiempo opt.</th>
            <th className="num">Errores (conv. / opt.)</th>
            <th className="num">Ejecuciones</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f.prueba}>
              <td>
                <strong>{f.prueba}</strong> – {f.rol}
                <br />
                <small className="tenue">{f.tarea}</small>
              </td>
              <td className="num">{n(f.pasos_convencional)}</td>
              <td className="num">{n(f.pasos_optimizada)}</td>
              <td className="num">{f.reduccion_pasos_pct == null ? "—" : `${f.reduccion_pasos_pct}%`}</td>
              <td className="num">{segundos(f.tiempo_convencional_ms)}</td>
              <td className="num">{segundos(f.tiempo_optimizado_ms)}</td>
              <td className="num">{n(f.errores_convencional)} / {n(f.errores_optimizada)}</td>
              <td className="num">{f.ejecuciones_convencional} / {f.ejecuciones_optimizada}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
