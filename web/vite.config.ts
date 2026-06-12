import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // CORS on the Lapwise HTTP API + AgentCore is configured for
    // http://localhost:5173 — keep the port pinned.
    port: 5173,
    strictPort: true,
  },
});
