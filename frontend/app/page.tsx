"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { href } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";

export default function Raiz() {
  const { usuario, menu, cargando } = useSesion();
  const router = useRouter();
  useEffect(() => {
    if (cargando) return;
    router.replace(href(usuario && menu ? menu.ruta_principal : "/login"));
  }, [cargando, usuario, menu, router]);
  return <div className="pantalla-carga">Cargando LabCloud…</div>;
}
