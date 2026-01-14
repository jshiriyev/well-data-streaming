import { defineConfig } from "vite";
import vueDevTools from 'vite-plugin-vue-devtools'
import vue from "@vitejs/plugin-vue";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const projectDir = dirname(fileURLToPath(import.meta.url));
const srcDir = resolve(projectDir, "src");
const appRoot = resolve(srcDir, "app");
const appEntry = resolve(srcDir, "index.html");

export default defineConfig({
  root: srcDir,
  base: "/",
  appType: "spa",
  plugins: [
    vue()
  ],
  publicDir: resolve(projectDir, "public"),
  resolve: {
    alias: {
      "@app": appRoot,
      "@views": resolve(appRoot, "views"),
      "@pages": resolve(appRoot, "pages"),
      "@composables": resolve(appRoot, "composables"),
      "@stores": resolve(appRoot, "stores"),
      "@api": resolve(srcDir, "api"),
      "@styles": resolve(srcDir, "styles"),
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
      input: appEntry,
      output: {
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
});
