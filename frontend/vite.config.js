import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const projectDir = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(projectDir, "src");
const appRoot = resolve(rootDir, "app");
const pagesRoot = resolve(rootDir, "pages");
const onemapRoot = resolve(rootDir, "onemap");
const htmlInputs = {
  app: resolve(appRoot, "index.html"),
  onemap: resolve(onemapRoot, "index.html"),
  datahub: resolve(pagesRoot, "datahub", "index.html"),
  workspaces: resolve(pagesRoot, "workspaces", "index.html"),
  workspaceGolden: resolve(pagesRoot, "workspaces", "golden-workspace", "index.html"),
  workspaceGrid: resolve(pagesRoot, "workspaces", "grid-workspace", "workspace.html"),
  workspaceArchie: resolve(pagesRoot, "workspaces", "plotly-configs", "archie", "index.html"),
  workspaceTimeseries: resolve(pagesRoot, "workspaces", "plotly-configs", "timeseries", "index.html"),
};

export default defineConfig({
  root: rootDir,
  base: "/",
  plugins: [vue()],
  publicDir: resolve(projectDir, "public"),
  resolve: {
    alias: {
      "@app": appRoot,
      "@api": resolve(rootDir, "api"),
      "@components": resolve(rootDir, "components"),
      "@shared": resolve(rootDir, "shared"),
      "@pages": resolve(rootDir, "pages"),
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
      input: htmlInputs,
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
