export type Rol = "recepcion" | "analista" | "administrador" | string;

export interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  rol: Rol;
  activo?: number;
  creado_en?: string;
}

export interface ItemMenu {
  clave: string;
  etiqueta: string;
  icono: string;
  descripcion: string;
  ruta: string | null;
  hijos?: ItemMenu[];
}

export interface MenuNavegacion {
  rol: Rol;
  estrategia: string;
  nombre: string;
  descripcion: string;
  ruta_principal: string;
  principales: ItemMenu[];
  secundarias: ItemMenu[];
  rutas_permitidas: string[];
}

export interface Paciente {
  id: number;
  documento: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string | null;
  telefono: string | null;
  correo: string | null;
  creado_en: string;
}

export interface Examen {
  clave: string;
  nombre: string;
  tipo_muestra: string;
  reactivo: string;
  unidad: string;
  referencia: string;
}

export interface Resultado {
  id: number;
  muestra_id: number;
  examen: string;
  valor: string;
  unidad: string | null;
  referencia: string | null;
  observaciones: string | null;
  registrado_en: string;
  muestra_codigo?: string;
  orden_codigo?: string;
  paciente_nombre?: string;
  paciente_documento?: string;
  analista_nombre?: string;
}

export interface Muestra {
  id: number;
  codigo: string;
  orden_id: number;
  orden_codigo?: string;
  tipo: string;
  examenes: string;
  estado: "pendiente" | "en_proceso" | "procesada";
  prioridad?: "normal" | "urgente";
  paciente_nombre?: string;
  paciente_documento?: string;
  creado_en: string;
  iniciada_en: string | null;
  procesada_en: string | null;
  examenes_detalle?: { clave: string; nombre: string; unidad: string; referencia: string }[];
  resultados?: Resultado[];
}

export interface Orden {
  id: number;
  codigo: string;
  paciente_id: number;
  paciente_nombre: string;
  paciente_documento: string;
  examenes: string;
  prioridad: "normal" | "urgente";
  estado: "registrada" | "en_proceso" | "completada";
  creado_en: string;
  muestras: Muestra[];
}

export interface Insumo {
  id: number;
  nombre: string;
  lote: string;
  cantidad: number;
  minimo: number;
  unidad: string;
  vencimiento: string | null;
  bajo_minimo: number;
}

export interface EventoSistema {
  id: number | null;
  tipo: string;
  mensaje: string;
  entidad: string | null;
  entidad_id: number | null;
  creado_en: string;
}

export interface FilaResumenPrueba {
  prueba: string;
  rol: string;
  tarea: string;
  pasos_convencional: number | null;
  pasos_optimizada: number | null;
  reduccion_pasos_pct: number | null;
  tiempo_convencional_ms: number | null;
  tiempo_optimizado_ms: number | null;
  errores_convencional: number | null;
  errores_optimizada: number | null;
  ejecuciones_convencional: number;
  ejecuciones_optimizada: number;
}
