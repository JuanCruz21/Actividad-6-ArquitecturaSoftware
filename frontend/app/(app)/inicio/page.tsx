"use client";

import { Icono } from "@/components/Icono";
import { Encabezado, Tarjeta, Vacio } from "@/components/ui";
import { useEventos } from "@/lib/eventos";
import { fecha } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import { useDatos } from "@/lib/useDatos";

interface EntradaHistorial {
  id: number;
  comando: string;
  ruta: string;
  registrado_en: string;
}

export default function Inicio() {
  const { usuario, menu, navegar } = useSesion();
  const { notificaciones } = useEventos();
  const { datos: historial } = useDatos<EntradaHistorial[]>("/api/navegacion/historial");
  if (!usuario || !menu) return null;

  return (
    <>
      <Encabezado
        titulo={`Hola, ${usuario.nombre.split(" ")[0]}`}
        descripcion={`${menu.nombre}: ${menu.descripcion}`}
      />
      <div className="accesos">
        {menu.principales.map((item) => (
          <button key={item.clave} className="acceso" onClick={() => navegar(item.clave)}>
            <span className="icono-acceso">
              <Icono nombre={item.icono} tamano={20} />
            </span>
            <strong>{item.etiqueta}</strong>
            <small>{item.descripcion}</small>
          </button>
        ))}
      </div>
      <div className="rejilla">
        <Tarjeta titulo="Actividad reciente">
          {notificaciones.length === 0 ? (
            <Vacio>Sin eventos para tu rol.</Vacio>
          ) : (
            <ul className="lista-eventos">
              {notificaciones.slice(0, 6).map((n, i) => (
                <li key={`${n.id}-${i}`} className={`evento evento-${n.tipo.split(".")[0]}`}>
                  <span>{n.mensaje}</span>
                  <time>{fecha(n.creado_en)}</time>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>
        <Tarjeta titulo="Historial de navegación (Command)">
          {!historial?.length ? (
            <Vacio>Aún no has ejecutado acciones de navegación.</Vacio>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Comando</th>
                  <th>Ruta</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {historial.slice(0, 8).map((h) => (
                  <tr key={h.id}>
                    <td><code>{h.comando}</code></td>
                    <td>{h.ruta}</td>
                    <td>{fecha(h.registrado_en)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Tarjeta>
      </div>
    </>
  );
}
