import { ref } from "vue";

let loadPromise = null;

async function ensureJquery() {
  const module = await import("jquery");
  const jquery = module.default ?? module;
  if (typeof window !== "undefined") {
    window.$ = jquery;
    window.jQuery = jquery;
  }
  return jquery;
}

async function ensureGoldenLayout() {
  const module = await import("golden-layout");
  const GoldenLayout = module.default ?? module;
  if (typeof window !== "undefined") {
    window.GoldenLayout = GoldenLayout;
  }
  return GoldenLayout;
}

async function ensureGoldenLayoutStyles() {
  await Promise.all([
    import("golden-layout/src/css/goldenlayout-base.css"),
    import("golden-layout/src/css/goldenlayout-light-theme.css"),
  ]);
}

export function useWorkspaceDependencies() {
  const ready = ref(false);
  const error = ref(null);
  const loading = ref(false);

  async function load() {
    if (ready.value) return;
    if (loading.value && loadPromise) return loadPromise;

    loading.value = true;
    error.value = null;

    loadPromise = (async () => {
      await ensureGoldenLayoutStyles();
      await ensureJquery();
      await ensureGoldenLayout();
      ready.value = true;
    })()
      .catch((err) => {
        error.value = err;
        throw err;
      })
      .finally(() => {
        loading.value = false;
      });

    return loadPromise;
  }

  return {
    ready,
    error,
    loading,
    load,
  };
}
