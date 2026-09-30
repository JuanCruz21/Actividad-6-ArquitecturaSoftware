"use client";

import { Plus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Aviso, Cargando, Encabezado, Tarjeta, Vacio } from "@/components/ui";
import { api } from "@/lib/api";
import { fecha } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { Paciente } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const VACIO = { documento: "", nombres: "", apellidos: "", fecha_nacimiento: "", telefono: "", correo: "" };

export default function Pacientes() {
  const { usuario, navegar } = useSesion();
  const [busqueda, setBusqueda] = useState("");
  const { datos, cargando, error, recargar } = useDatos<Paciente[]>(
    `/api/pacientes${busqueda ? `?q=${encodeURIComponent(busqueda)}` : ""}`,
  );
  const [formulario, setFormulario] = useState(VACIO);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [mensaje, setMensaje] = useState<{ tipo: "error" | "exito"; texto: string } | null>(null);
  const puedeCrear = usuario?.rol === "recepcion";

  const guardar = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const datosLimpios = Object.fromEntries(Object.entries(formulario).map(([k, v]) => [k, v.trim() || null]));
      const p = await api<Paciente>("/api/pacientes", { method: "POST", body: datosLimpios });
      setMensaje({ tipo: "exito", texto: `Paciente ${p.nombres} ${p.apellidos} registrado.` });
      setFormulario(VACIO);
      setMostrarFormulario(false);
      recargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: (err as Error).message });
    }
  };

  const campo = (clave: keyof typeof VACIO, etiqueta: string, tipo = "text", requerido = false) => (
    <label>
      {etiqueta}
      <input
        type={tipo}
        required={requerido}
        value={formulario[clave]}
        onChange={(e) => setFormulario({ ...formulario, [clave]: e.target.value })}
      />
    </label>
  );

  return (
    <>
      <Encabezado
        titulo="Pacientes"
        descripcion="Registro y consulta de pacientes del laboratorio."
        acciones={
          puedeCrear && (
            <button className="boton" onClick={() => setMostrarFormulario((m) => !m)}>
              <Plus size={16} /> Registrar paciente
            </button>
          )
        }
      />
      {mensaje && <Aviso tipo={mensaje.tipo}>{mensaje.texto}</Aviso>}
      {mostrarFormulario && (
        <Tarjeta titulo="Nuevo paciente">
          <form className="formulario" onSubmit={guardar}>
            {campo("documento", "Documento", "text", true)}
            {campo("nombres", "Nombres", "text", true)}
            {campo("apellidos", "Apellidos", "text", true)}
            {campo("fecha_nacimiento", "Fecha de nacimiento", "date")}
            {campo("telefono", "Teléfono", "tel")}
            {campo("correo", "Correo", "email")}
            <button className="boton">Guardar</button>
          </form>
        </Tarjeta>
      )}
      <Tarjeta
        titulo="Listado"
        extra={
          <input
            type="search"
            placeholder="Buscar por documento o nombre"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            style={{ maxWidth: 300 }}
          />
        }
      >
        {error && <Aviso>{error}</Aviso>}
        {cargando ? (
          <Cargando />
        ) : !datos?.length ? (
          <Vacio>No se encontraron pacientes.</Vacio>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Documento</th>
                  <th>Paciente</th>
                  <th>Nacimiento</th>
                  <th>Contacto</th>
                  <th>Registrado</th>
                  {puedeCrear && <th />}
                </tr>
              </thead>
              <tbody>
                {datos.map((p) => (
                  <tr key={p.id}>
                    <td>{p.documento}</td>
                    <td>{p.nombres} {p.apellidos}</td>
                    <td>{p.fecha_nacimiento ?? "—"}</td>
                    <td>{[p.telefono, p.correo].filter(Boolean).join(" · ") || "—"}</td>
                    <td>{fecha(p.creado_en)}</td>
                    {puedeCrear && (
                      <td>
                        <button className="boton secundario pequeno" onClick={() => navegar("ordenes.nueva", `paciente=${p.id}`)}>
                          Nueva orden
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Tarjeta>
    </>
  );
}
