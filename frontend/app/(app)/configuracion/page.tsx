"use client";

import { Icono } from "@/components/Icono";
import { Aviso, Cargando, Encabezado, Tarjeta } from "@/components/ui";
import type { ItemMenu, MenuNavegacion } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

function Arbol({ nodos }: { nodos: ItemMenu[] }) {
  return (
    <ul className="arbol">
      {nodos.map((n) => (
        <li key={n.clave}>
          <span className="nodo">
            <Icono nombre={n.icono} tamano={15} /> {n.etiqueta}
          </span>
          {!!n.hijos?.length && <Arbol nodos={n.hijos} />}
        </li>
      ))}
    </ul>
  );
}

export default function Configuracion() {
  const { datos, cargando, error } = useDatos<MenuNavegacion[]>("/api/navegacion/estrategias");
  const { datos: convencional } = useDatos<{ arbol: ItemMenu[] }>("/api/navegacion/menu/convencional");

  return (
    <>
      <Encabezado
        titulo="Configuración de navegación"
        descripcion="Estrategias registradas (patrón Strategy). Un rol nuevo solo requiere una clase que implemente EstrategiaNavegacion."
      />
      {error && <Aviso>{error}</Aviso>}
      {cargando ? (
        <Cargando />
      ) : (
        <div className="rejilla">
          {datos?.map((e) => (
            <Tarjeta key={e.rol} titulo={e.nombre} extra={<code>{e.estrategia}</code>}>
              <p className="tenue">{e.descripcion}</p>
              <p>
                Ruta principal: <code>{e.ruta_principal}</code>
              </p>
              <div>
                <strong>Prioritarias</strong>
                <ul>
                  {e.principales.map((i) => (
                    <li key={i.clave}>
                      {i.etiqueta} <code className="tenue">{i.clave}</code>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Secundarias</strong>
                <ul>
                  {e.secundarias.map((i) => (
                    <li key={i.clave}>{i.etiqueta}</li>
                  ))}
                </ul>
              </div>
            </Tarjeta>
          ))}
          {convencional && (
            <Tarjeta titulo="Navegación convencional (línea base)" extra={<code>NavegacionConvencional</code>}>
              <p className="tenue">Menú jerárquico único para todos los roles, usado en las pruebas comparativas.</p>
              <Arbol nodos={convencional.arbol} />
            </Tarjeta>
          )}
        </div>
      )}
    </>
  );
}
