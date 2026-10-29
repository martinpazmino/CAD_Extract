import { defineConfig } from "vite";

// Zwei Seiten: index.html (Schritt-App, ueber server/api.py) und viewer.html (Viewer allein, Pruefungen).
// base "./": laeuft auch aus einem Unterordner. Die Entwicklung mit "npm run dev" leitet /api und /dateien an den
// Python-Server weiter (python -m server --kein-browser).
// That Open importiert WebGPU-Symbole (TSL, NodeMaterial, WebGPURenderer) aus "three" und prueft zur
// Laufzeit, ob es sie gibt; mit dem WebGL-Build fehlen sie absichtlich -> Warnung unterdruecken.
export default defineConfig({
  base: "./",
  server: { proxy: { "/api": "http://127.0.0.1:8500", "/dateien": "http://127.0.0.1:8500" } },
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 6000,
    rollupOptions: {
      input: { index: "index.html", viewer: "viewer.html" },
      onwarn(warnung, weiter) {
        if (warnung.code === "MISSING_EXPORT" && warnung.id?.includes("@thatopen")) return;
        weiter(warnung);
      },
    },
  },
});
