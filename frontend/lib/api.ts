const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const CLAVE_TOKEN = "labcloud.token";

export class ErrorApi extends Error {
  constructor(mensaje: string, public estado: number) {
    super(mensaje);
  }
}

export function leerToken(): string | null {
  try {
    return localStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}

export function guardarToken(token: string | null) {
  try {
    if (token) localStorage.setItem(CLAVE_TOKEN, token);
    else localStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* almacenamiento no disponible */
  }
}

export function urlApi(ruta: string) {
  return BASE + ruta;
}

function mensajeDeError(datos: unknown, estado: number): string {
  const detalle = (datos as { detail?: unknown } | null)?.detail;
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) {
    return detalle
      .map((d: { loc?: string[]; msg?: string }) => `${d.loc?.slice(1).join(".") ?? ""}: ${d.msg ?? ""}`)
      .join(" · ");
  }
  return `Error ${estado}`;
}

export async function api<T = unknown>(
  ruta: string,
  opciones: { method?: string; body?: unknown } = {},
): Promise<T> {
  const token = leerToken();
  const respuesta = await fetch(urlApi(ruta), {
    method: opciones.method ?? "GET",
    headers: {
      ...(opciones.body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: opciones.body !== undefined ? JSON.stringify(opciones.body) : undefined,
  });
  const datos = await respuesta.json().catch(() => null);
  if (respuesta.status === 401 && ruta !== "/api/auth/login") {
    guardarToken(null);
    if (!window.location.pathname.startsWith("/login")) window.location.href = "/login/";
  }
  if (!respuesta.ok) throw new ErrorApi(mensajeDeError(datos, respuesta.status), respuesta.status);
  return datos as T;
}
