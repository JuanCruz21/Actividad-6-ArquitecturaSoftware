import type { Metadata } from "next";
import { SesionProvider } from "@/lib/sesion";
import "./globals.css";

export const metadata: Metadata = {
  title: "LabCloud Intelligent",
  description: "Gestión de laboratorio clínico con navegación adaptativa por rol",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <SesionProvider>{children}</SesionProvider>
      </body>
    </html>
  );
}
