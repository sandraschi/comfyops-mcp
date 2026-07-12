import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 11088,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: "http://localhost:11087",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:11087",
        changeOrigin: true,
      },
    },
  },
});
