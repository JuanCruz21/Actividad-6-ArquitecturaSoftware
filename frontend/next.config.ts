import type { NextConfig } from "next";

// En producción la interfaz se exporta como archivos estáticos y la sirve el mismo
// proceso de FastAPI (monolito). En desarrollo, `next dev` reenvía /api al backend.
const produccion = process.env.NODE_ENV === "production";
const backend = process.env.LABCLOUD_BACKEND ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  images: { unoptimized: true },
  ...(produccion
    ? { output: "export" }
    : {
        async rewrites() {
          return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
        },
      }),
};

export default nextConfig;
