"use client";

import { Plus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Aviso, Cargando, Encabezado, Tarjeta } from "@/components/ui";
import { api } from "@/lib/api";
import { ETIQUETAS_ROL, fecha } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { Usuario } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const VACIO = { nombre: "", correo: "", password: "", rol: "recepcion" };

export default function Usuarios() {
  const { usuario: actual } = useSesion();
  const { datos, cargando, error, recargar } = useDatos<{ usuarios: Usuario[]; roles: string[] }>("/api/usuarios");
  const [formulario, setFormulario] = useState(VACIO);
  const [abierto, setAbierto] = useState(false);
  const [mensaje, setMensaje] = useState<{ tipo: "error" | "exito"; texto: string } | null>(null);

  const crear = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await api("/api/usuarios", { method: "POST", body: formulario });
      setMensaje({ tipo: "exito", texto: `Usuario ${formulario.correo} creado.` });
      setFormulario(VACIO);
      setAbierto(false);
      recargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: (err as Error).message });
    }
  };

  const alternar = async (u: Usuario) => {
    try {
      await api(`/api/usuarios/${u.id}`, { method: "PATCH", body: { activo: !u.activo } });
      recargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: (err as Error).message });
    }
  };

  return (
    <>
      <Encabezado
        titulo="Usuarios"
        descripcion="Cuentas, roles y acceso. El rol determina la estrategia de navegación."
        acciones={
          <button className="boton" onClick={() => setAbierto((a) => !a)}>
            <Plus size={16} /> Nuevo usuario
          </button>
        }
      />
      {mensaje && <Aviso tipo={mensaje.tipo}>{mensaje.texto}</Aviso>}
      {abierto && (
        <Tarjeta titulo="Nuevo usuario">
          <form className="formulario" onSubmit={crear}>
            <label>
              Nombre
              <input required value={formulario.nombre} onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })} />
            </label>
            <label>
              Correo
              <input type="email" required value={formulario.correo} onChange={(e) => setFormulario({ ...formulario, correo: e.target.value })} />
            </label>
            <label>
              Contraseña (mín. 6)
              <input type="password" minLength={6} required value={formulario.password} onChange={(e) => setFormulario({ ...formulario, password: e.target.value })} autoComplete="new-password" />
            </label>
            <label>
              Rol
              <select value={formulario.rol} onChange={(e) => setFormulario({ ...formulario, rol: e.target.value })}>
                {datos?.roles.map((r) => (
                  <option key={r} value={r}>{ETIQUETAS_ROL[r] ?? r}</option>
                ))}
              </select>
            </label>
            <button className="boton">Crear</button>
          </form>
        </Tarjeta>
      )}
      <Tarjeta>
        {error && <Aviso>{error}</Aviso>}
        {cargando ? (
          <Cargando />
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Correo</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Creado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {datos?.usuarios.map((u) => (
                  <tr key={u.id}>
                    <td>{u.nombre}</td>
                    <td>{u.correo}</td>
                    <td>{ETIQUETAS_ROL[u.rol] ?? u.rol}</td>
                    <td>
                      <span className={`insignia ${u.activo ? "estado-completada" : ""}`}>{u.activo ? "Activo" : "Inactivo"}</span>
                    </td>
                    <td>{fecha(u.creado_en)}</td>
                    <td>
                      {u.id !== actual?.id && (
                        <button className="boton secundario pequeno" onClick={() => alternar(u)}>
                          {u.activo ? "Desactivar" : "Activar"}
                        </button>
                      )}
                    </td>
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
