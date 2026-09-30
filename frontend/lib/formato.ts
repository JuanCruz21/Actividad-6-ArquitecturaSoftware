export function fecha(valor: string | null | undefined): string {
  if (!valor) return "—";
  const d = new Date(valor.replace(" ", "T") + (valor.includes("Z") ? "" : "Z"));
  if (Number.isNaN(d.getTime())) return valor;
  return d.toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" });
}

export function segundos(ms: number | null | undefined): string {
  return ms == null ? "—" : `${(ms / 1000).toFixed(1)} s`;
}

export const ETIQUETAS_ESTADO: Record<string, string> = {
  pendiente: "Pendiente",
  en_proceso: "En proceso",
  procesada: "Procesada",
  registrada: "Registrada",
  completada: "Completada",
};

export const ETIQUETAS_ROL: Record<string, string> = {
  recepcion: "Recepción",
  analista: "Analista",
  administrador: "Administrador",
};

export function normalizarRuta(ruta: string): string {
  return ruta.length > 1 ? ruta.replace(/\/+$/, "") : ruta;
}

/** La exportación estática usa `trailingSlash`: las rutas del cliente deben terminar en "/". */
export function href(ruta: string, consulta?: string): string {
  const base = ruta.endsWith("/") ? ruta : `${ruta}/`;
  return consulta ? `${base}?${consulta}` : base;
}
