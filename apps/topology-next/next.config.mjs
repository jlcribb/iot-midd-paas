/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  distDir: process.env.NEXT_DIST_DIR || ".next",
  // El stack de Docker se prueba desde el host en 127.0.0.1; permitirlo evita
  // que Next bloquee los recursos de desarrollo necesarios para hidratar OAuth.
  allowedDevOrigins: ["127.0.0.1"]
};

export default nextConfig;
