import { defineConfig } from "vite";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const projectDir = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(projectDir, "src");
const pagesDir = resolve(rootDir, "pages");

export default defineConfig({
  root: projectDir,
  base: "/",
  publicDir: resolve(projectDir, "public"),
  resolve: {
    alias: {
      "@shared": resolve(rootDir, "shared"),
      "@pages": resolve(rootDir, "pages"),
    },
  },
  build: {
    outDir: resolve(projectDir, "dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        onemap: resolve(pagesDir, "onemap/index.html"),
        timeseries: resolve(pagesDir, "timeseries/index.html"),
        archie: resolve(pagesDir, "archie/index.html"),
        workbench: resolve(pagesDir, "workbench/index.html"),
        fluidlab: resolve(pagesDir, "fluidlab/index.html"),
        deliverables: resolve(pagesDir, "deliverables/index.html"),
        impulse: resolve(pagesDir, "impulse/index.html"),
        datahub: resolve(pagesDir, "datahub/index.html"),
      },
      output: {
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
        manualChunks(id) {
          if (id.includes("/shared/") || id.includes("\\shared\\")) {
            return "shared";
          }
          return undefined;
        },
      },
    },
  },
});
