"use client";

import { FlaskConical } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { Aviso } from "@/components/ui";
import { href } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";

// Cuentas de demostración creadas por labcloud/datos/seed.py (solo entorno local).
const CUENTAS_DEMO = [
  { rol: "Recepción", correo: "recepcion@labcloud.test", password: "recepcion123" },
  { rol: "Analista", correo: "analista@labcloud.test", password: "analista123" },
  { rol: "Administrador", correo: "admin@labcloud.test", password: "admin123" },
];

export default function Login() {
  const { iniciarSesion, usuario, menu } = useSesion();
  const router = useRouter();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (usuario && menu) router.replace(href(menu.ruta_principal));
  }, [usuario, menu, router]);

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      await iniciarSesion(correo, password);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="login">
      <form className="tarjeta" onSubmit={enviar}>
        <div className="fila">
          <FlaskConical size={28} color="var(--primario)" />
          <div>
            <h1>LabCloud Intelligent</h1>
            <p className="tenue">Ingresa para ver la navegación de tu rol</p>
          </div>
        </div>
        {error && <Aviso>{error}</Aviso>}
        <label>
          Correo
          <input type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} required autoComplete="username" />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        <button className="boton" disabled={enviando}>
          {enviando ? "Ingresando…" : "Ingresar"}
        </button>
        <div className="cuentas">
          <p className="tenue">Cuentas de demostración:</p>
          {CUENTAS_DEMO.map((c) => (
            <button
              type="button"
              key={c.correo}
              className="cuenta"
              onClick={() => {
                setCorreo(c.correo);
                setPassword(c.password);
              }}
            >
              <strong>{c.rol}</strong>
              <span className="tenue">{c.correo}</span>
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
