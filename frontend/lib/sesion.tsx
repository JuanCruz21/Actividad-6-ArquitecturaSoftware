"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, guardarToken, leerToken } from "./api";
import { href } from "./formato";
import type { MenuNavegacion, Usuario } from "./tipos";

interface ContextoSesion {
  usuario: Usuario | null;
  menu: MenuNavegacion | null;
  cargando: boolean;
  iniciarSesion: (correo: string, password: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
  navegar: (clave: string, consulta?: string) => Promise<void>;
  atras: () => Promise<void>;
}

const Contexto = createContext<ContextoSesion | null>(null);

export function SesionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [menu, setMenu] = useState<MenuNavegacion | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargarSesion = useCallback(async () => {
    if (!leerToken()) {
      setCargando(false);
      return;
    }
    try {
      const [u, m] = await Promise.all([
        api<Usuario>("/api/auth/yo"),
        api<MenuNavegacion>("/api/navegacion/menu"),
      ]);
      setUsuario(u);
      setMenu(m);
    } catch {
      guardarToken(null);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarSesion();
  }, [cargarSesion]);

  const iniciarSesion = useCallback(
    async (correo: string, password: string) => {
      const r = await api<{ token: string; ruta_principal: string }>("/api/auth/login", {
        method: "POST",
        body: { correo, password },
      });
      guardarToken(r.token);
      setCargando(true);
      await cargarSesion();
      router.push(href(r.ruta_principal));
    },
    [cargarSesion, router],
  );

  const cerrarSesion = useCallback(async () => {
    await api("/api/auth/logout", { method: "POST" }).catch(() => undefined);
    guardarToken(null);
    setUsuario(null);
    setMenu(null);
    router.push(href("/login"));
  }, [router]);

  // Patrón Command: cada clic del menú ejecuta un comando en el backend, que valida
  // el permiso según la estrategia del rol, lo registra en el historial y devuelve la ruta.
  const navegar = useCallback(
    async (clave: string, consulta?: string) => {
      const r = await api<{ ruta: string }>(`/api/navegacion/comandos/${encodeURIComponent(clave)}`, {
        method: "POST",
      });
      router.push(href(r.ruta, consulta));
    },
    [router],
  );

  const atras = useCallback(async () => {
    const r = await api<{ ruta: string }>("/api/navegacion/deshacer", { method: "POST" });
    router.push(href(r.ruta));
  }, [router]);

  return (
    <Contexto.Provider value={{ usuario, menu, cargando, iniciarSesion, cerrarSesion, navegar, atras }}>
      {children}
    </Contexto.Provider>
  );
}

export function useSesion() {
  const ctx = useContext(Contexto);
  if (!ctx) throw new Error("useSesion debe usarse dentro de SesionProvider");
  return ctx;
}
