import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The browser calls /api/... on the frontend's own address and Vite forwards it to the backend,
// so no CORS setup is needed in development.
// Local: backend on localhost:8000. Docker Compose sets API_PROXY_TARGET=http://backend:8000.
const apiTarget = process.env.API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
    },
  },
});
