import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development, Vite serves the React app and forwards /api calls to Flask (port 5000),
// so cookies and sessions work exactly as they do in the built app.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
