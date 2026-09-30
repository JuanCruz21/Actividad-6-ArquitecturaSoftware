"use client";

import { ChevronDown, ChevronRight, CircleCheck, Play, RefreshCw } from "lucide-react";
import { useState } from "react";
import { Icono } from "@/components/Icono";
import { TablaResumen } from "@/components/TablaResumen";
import { Aviso, Encabezado, Tarjeta, Vacio } from "@/components/ui";
import { api } from "@/lib/api";
import { fecha, segundos } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { FilaResumenPrueba, ItemMenu, MenuNavegacion } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

type Modo = "convencional" | "optimizada";

interface Escenario {
  prueba: "P1" | "P2" | "P3";
  rol: string;
  rol_nombre: string;
  tarea: string;
  objetivo: string;
}

interface Ejecucion {
  id: number;
  prueba: string;
  modo: Modo;
  pasos: number;
  tiempo_ms: number;
  errores: number;
  recorrido: string | null;
  usuario_nombre: string | null;
  registrado_en: string;
}

interface Recorrido {
  inicio: number;
  pasos: number;
  errores: number;
  camino: string[];
  expandidos: string[];
  aviso: string | null;
}

interface Final {
  pasos: number;
  errores: number;
  tiempo_ms: number;
  camino: string[];
}

export default function Pruebas() {
  const { usuario } = useSesion();
  const { datos: escenarios } = useDatos<Escenario[]>("/api/pruebas/escenarios");
  const { datos: resumen, recargar } = useDatos<{ resumen: FilaResumenPrueba[]; historial: Ejecucion[] }>(
    "/api/pruebas/resumen",
  );
  const { datos: convencional } = useDatos<{ arbol: ItemMenu[] }>("/api/navegacion/menu/convencional");
  const [prueba, setPrueba] = useState<Escenario["prueba"]>("P1");
  const [modo, setModo] = useState<Modo>("convencional");
  const escenario = escenarios?.find((e) => e.prueba === prueba);
  const { datos: optimizado } = useDatos<MenuNavegacion>(
    escenario ? `/api/navegacion/menu/simular?rol=${escenario.rol}` : null,
  );
  const [recorrido, setRecorrido] = useState<Recorrido | null>(null);
  const [final, setFinal] = useState<Final | null>(null);
  const [error, setError] = useState<string | null>(null);

  const iniciar = () => {
    setFinal(null);
    setError(null);
    setRecorrido({ inicio: performance.now(), pasos: 0, errores: 0, camino: [], expandidos: [], aviso: null });
  };

  const abrirCarpeta = (nodo: ItemMenu) => {
    setRecorrido((r) =>
      r && {
        ...r,
        pasos: r.pasos + 1,
        camino: [...r.camino, nodo.etiqueta],
        aviso: null,
        expandidos: r.expandidos.includes(nodo.clave)
          ? r.expandidos.filter((c) => c !== nodo.clave)
          : [...r.expandidos, nodo.clave],
      },
    );
  };

  const elegir = async (nodo: ItemMenu) => {
    if (!recorrido || !escenario) return;
    const pasos = recorrido.pasos + 1;
    const camino = [...recorrido.camino, nodo.etiqueta];
    if (nodo.clave !== escenario.objetivo) {
      setRecorrido({
        ...recorrido,
        pasos,
        camino,
        errores: recorrido.errores + 1,
        aviso: `“${nodo.etiqueta}” no es la opción solicitada (desvío registrado).`,
      });
      return;
    }
    const resultado = {
      pasos,
      errores: recorrido.errores,
      tiempo_ms: Math.round(performance.now() - recorrido.inicio),
      camino,
    };
    setRecorrido(null);
    setFinal(resultado);
    try {
      await api("/api/pruebas/resultados", {
        method: "POST",
        body: { prueba, modo, pasos, tiempo_ms: resultado.tiempo_ms, errores: resultado.errores, recorrido: camino },
      });
      recargar();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const reiniciar = async () => {
    if (!confirm("¿Eliminar todas las mediciones registradas?")) return;
    await api("/api/pruebas/resultados", { method: "DELETE" });
    recargar();
  };

  const arbol = (nodos: ItemMenu[]) => (
    <ul className="arbol">
      {nodos.map((n) => {
        const esCarpeta = !!n.hijos?.length;
        const abierto = recorrido?.expandidos.includes(n.clave);
        return (
          <li key={n.clave}>
            <button className="nodo" onClick={() => (esCarpeta ? abrirCarpeta(n) : elegir(n))}>
              {esCarpeta ? (abierto ? <ChevronDown size={15} /> : <ChevronRight size={15} />) : <Icono nombre={n.icono} tamano={15} />}
              {n.etiqueta}
            </button>
            {esCarpeta && abierto && arbol(n.hijos!)}
          </li>
        );
      })}
    </ul>
  );

  const menuPlano = (menu: MenuNavegacion) => (
    <div style={{ display: "grid", gap: 10 }}>
      <small className="tenue">Prioritarias · {menu.nombre}</small>
      <div className="menu-plano">
        {menu.principales.map((i) => (
          <button key={i.clave} className="nodo prioritaria" onClick={() => elegir(i)}>
            <Icono nombre={i.icono} tamano={16} /> {i.etiqueta}
          </button>
        ))}
      </div>
      <small className="tenue">Otras opciones</small>
      <div className="menu-plano">
        {menu.secundarias.map((i) => (
          <button key={i.clave} className="nodo" onClick={() => elegir(i)}>
            <Icono nombre={i.icono} tamano={16} /> {i.etiqueta}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <>
      <Encabezado
        titulo="Pruebas de navegación"
        descripcion="Escenarios P1–P3: compara el recorrido convencional con la navegación optimizada por rol midiendo pasos, tiempo y errores."
        acciones={
          usuario?.rol === "administrador" && (
            <button className="boton secundario" onClick={reiniciar}>
              <RefreshCw size={16} /> Reiniciar mediciones
            </button>
          )
        }
      />
      {error && <Aviso>{error}</Aviso>}
      <div className="rejilla-2">
        <Tarjeta titulo="Ejecutar escenario">
          <div className="formulario">
            <label>
              Escenario
              <select
                value={prueba}
                disabled={!!recorrido}
                onChange={(e) => {
                  setPrueba(e.target.value as Escenario["prueba"]);
                  setFinal(null);
                }}
              >
                {escenarios?.map((e) => (
                  <option key={e.prueba} value={e.prueba}>
                    {e.prueba} – {e.rol_nombre}: {e.tarea}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo de navegación
              <select
                value={modo}
                disabled={!!recorrido}
                onChange={(e) => {
                  setModo(e.target.value as Modo);
                  setFinal(null);
                }}
              >
                <option value="convencional">Convencional (menú jerárquico)</option>
                <option value="optimizada">Optimizada (estrategia del rol)</option>
              </select>
            </label>
            {recorrido ? (
              <button className="boton secundario" onClick={() => setRecorrido(null)}>
                Cancelar
              </button>
            ) : (
              <button className="boton" onClick={iniciar} disabled={!escenario}>
                <Play size={16} /> Iniciar
              </button>
            )}
          </div>

          <div className={`simulador ${recorrido ? "activo" : ""}`}>
            {escenario && (
              <p>
                <strong>Tarea ({escenario.rol_nombre}):</strong> {escenario.tarea}
              </p>
            )}
            {recorrido ? (
              <>
                <p className="recorrido">
                  Pasos: {recorrido.pasos} · Errores: {recorrido.errores}
                  {recorrido.camino.length > 0 && ` · ${recorrido.camino.join(" › ")}`}
                </p>
                {recorrido.aviso && <Aviso tipo="info">{recorrido.aviso}</Aviso>}
                {modo === "convencional"
                  ? convencional && arbol(convencional.arbol)
                  : optimizado && menuPlano(optimizado)}
              </>
            ) : final ? (
              <Aviso tipo="exito">
                <CircleCheck size={15} style={{ verticalAlign: "-2px" }} /> Objetivo alcanzado en{" "}
                <strong>{final.pasos} paso(s)</strong>, {segundos(final.tiempo_ms)} y {final.errores} error(es).
                <br />
                <small>Recorrido: {final.camino.join(" › ")}</small>
              </Aviso>
            ) : (
              <p className="tenue">
                Pulsa <strong>Iniciar</strong>: el menú aparece y el cronómetro arranca. Cada clic cuenta como un paso;
                elegir una opción que no es la solicitada cuenta como error.
              </p>
            )}
          </div>
        </Tarjeta>

        <Tarjeta titulo="Últimas ejecuciones">
          {!resumen?.historial.length ? (
            <Vacio>Sin ejecuciones registradas.</Vacio>
          ) : (
            <ul className="lista-eventos">
              {resumen.historial.slice(0, 8).map((h) => (
                <li key={h.id} className={`evento ${h.modo === "optimizada" ? "evento-muestra" : "evento-orden"}`}>
                  <span>
                    <strong>{h.prueba}</strong> {h.modo}: {h.pasos} pasos · {segundos(h.tiempo_ms)} · {h.errores} err.
                  </span>
                  <time>
                    {h.usuario_nombre} · {fecha(h.registrado_en)}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>
      </div>

      <Tarjeta titulo="Tabla 6 · Registro de resultados (promedios)">
        {resumen && <TablaResumen filas={resumen.resumen} />}
      </Tarjeta>
    </>
  );
}
