import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// When running inside Docker, containers reach each other by service name.
// When running manually (npm run dev), they reach each other via localhost.
// VITE_API_TARGET can be set per environment to handle both cases.
const apiTarget = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",       // needed so Docker exposes the port correctly
    proxy: {
      // Forward all /api/* requests to the FastAPI backend
      // e.g. fetch("/api/calculate") → <apiTarget>/calculate
      "/api": {
        target:       apiTarget,
        changeOrigin: true,
        rewrite:      (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
