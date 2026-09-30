"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

export function useDatos<T>(ruta: string | null) {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const recargar = useCallback(async () => {
    if (!ruta) return;
    try {
      setDatos(await api<T>(ruta));
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  }, [ruta]);

  useEffect(() => {
    setCargando(true);
    recargar();
  }, [recargar]);

  return { datos, error, cargando, recargar };
}
