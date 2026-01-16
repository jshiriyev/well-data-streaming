import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from '@tailwindcss/vite'
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const projectDir = dirname(fileURLToPath(import.meta.url));
// const appEntry = resolve(projectDir, "index.html");
const srcDir = resolve(projectDir, "src");

export default defineConfig({
  root: projectDir,
  base: "/",
  appType: "spa",
  plugins: [
    vue(),
    tailwindcss(),
  ],
  publicDir: resolve(projectDir, "public"),
  resolve: {
    alias: {
      "@assets": resolve(srcDir, "assets"),
      "@components": resolve(srcDir, "components"),
      "@services": resolve(srcDir, "services"),
      "@views": resolve(srcDir, "views"),
      "@utils": resolve(srcDir, "utils"),
    },
  },
  server: {
    fs: {
      allow: [projectDir],
    },
  },
  build: {
    outDir: resolve(projectDir, "dist"),
    emptyOutDir: true,
    rollupOptions: {
      // input: appEntry,
      output: {
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
});
