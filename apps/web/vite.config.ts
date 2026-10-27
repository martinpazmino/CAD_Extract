import { defineConfig } from "vite";

// base "./": der Viewer laeuft auch aus einem Unterordner (statisches Hosting).
// That Open importiert WebGPU-Symbole (TSL, NodeMaterial, WebGPURenderer) aus "three" und prueft zur
// Laufzeit, ob es sie gibt; mit dem WebGL-Build fehlen sie absichtlich -> Warnung unterdruecken.
export default defineConfig({
  base: "./",
  build: {
    target: "es2022",
    chunkSizeWarningLimit: 6000,
    rollupOptions: {
      onwarn(warnung, weiter) {
        if (warnung.code === "MISSING_EXPORT" && warnung.id?.includes("@thatopen")) return;
        weiter(warnung);
      },
    },
  },
});
