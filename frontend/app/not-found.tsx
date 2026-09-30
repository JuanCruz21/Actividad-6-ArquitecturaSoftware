import Link from "next/link";

export default function NoEncontrada() {
  return (
    <div className="login">
      <div className="tarjeta">
        <h1>Página no encontrada</h1>
        <p className="tenue">La ruta solicitada no existe en LabCloud Intelligent.</p>
        <Link className="boton" href="/">Volver al inicio</Link>
      </div>
    </div>
  );
}
