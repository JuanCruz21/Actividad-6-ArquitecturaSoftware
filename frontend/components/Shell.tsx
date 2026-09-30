"use client";

import { ArrowLeft, FlaskConical, LogOut } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { Icono } from "@/components/Icono";
import { Notificaciones } from "@/components/Notificaciones";
import { EventosProvider } from "@/lib/eventos";
import { ETIQUETAS_ROL, href, normalizarRuta } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { ItemMenu } from "@/lib/tipos";

export function Shell({ children }: { children: ReactNode }) {
  const { usuario, menu, cargando, cerrarSesion, navegar, atras } = useSesion();
  const router = useRouter();
  const ruta = normalizarRuta(usePathname());

  useEffect(() => {
    if (!cargando && !usuario) router.replace(href("/login"));
  }, [cargando, usuario, router]);

  if (cargando || !usuario || !menu) {
    return <div className="pantalla-carga">Cargando LabCloud…</div>;
  }

  const permitida = menu.rutas_permitidas.includes(ruta);

  const enlace = (item: ItemMenu, destacado: boolean) => (
    <li key={item.clave}>
      <button
        className={`enlace-menu ${destacado ? "destacado" : ""} ${item.ruta === ruta ? "activo" : ""}`}
        onClick={() => navegar(item.clave)}
        title={item.descripcion}
      >
        <Icono nombre={item.icono} />
        <span>{item.etiqueta}</span>
      </button>
    </li>
  );

  return (
    <EventosProvider>
      <div className="aplicacion">
        <aside className="barra-lateral">
          <div className="marca">
            <FlaskConical size={22} />
            <div>
              <strong>LabCloud</strong>
              <small>Intelligent</small>
            </div>
          </div>
          <nav aria-label="Navegación del rol">
            <p className="seccion-menu">Prioritarias · {menu.nombre}</p>
            <ul>{menu.principales.map((i) => enlace(i, true))}</ul>
            <p className="seccion-menu">Otras opciones</p>
            <ul>{menu.secundarias.map((i) => enlace(i, false))}</ul>
          </nav>
          <p className="estrategia-activa" title={menu.descripcion}>
            Estrategia: <code>{menu.estrategia}</code>
          </p>
        </aside>

        <div className="contenido">
          <header className="barra-superior">
            <button className="boton-icono" onClick={atras} aria-label="Volver (deshacer navegación)" title="Volver">
              <ArrowLeft size={18} />
            </button>
            <div className="espaciador" />
            <Notificaciones />
            <div className="usuario">
              <strong>{usuario.nombre}</strong>
              <small>{ETIQUETAS_ROL[usuario.rol] ?? usuario.rol}</small>
            </div>
            <button className="boton-icono" onClick={cerrarSesion} aria-label="Cerrar sesión" title="Cerrar sesión">
              <LogOut size={18} />
            </button>
          </header>
          <main className="principal">
            {permitida ? (
              children
            ) : (
              <div className="tarjeta sin-acceso">
                <h1>Funcionalidad fuera de tu navegación</h1>
                <p className="tenue">
                  Esta opción no forma parte de la estrategia de navegación del rol {menu.nombre}.
                </p>
                <button className="boton" onClick={() => router.push(href(menu.ruta_principal))}>
                  Ir a mi página principal
                </button>
              </div>
            )}
          </main>
        </div>
      </div>
    </EventosProvider>
  );
}
