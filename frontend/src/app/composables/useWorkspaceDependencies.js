import { ref } from "vue";
import { loadScriptOnce, loadStyleOnce } from "../utils/loaders.js";

let loadPromise = null;

export function useWorkspaceDependencies() {
  const ready = ref(false);
  const error = ref(null);
  const loading = ref(false);

  async function load() {
    if (ready.value) return;
    if (loading.value && loadPromise) return loadPromise;

    loading.value = true;
    error.value = null;

    loadPromise = Promise.all([
      loadStyleOnce("https://unpkg.com/golden-layout@1.5.9/src/css/goldenlayout-base.css"),
      loadStyleOnce("https://unpkg.com/golden-layout@1.5.9/src/css/goldenlayout-light-theme.css"),
      loadScriptOnce("https://code.jquery.com/jquery-3.7.1.min.js"),
      loadScriptOnce("https://unpkg.com/golden-layout@1.5.9/dist/goldenlayout.min.js"),
      loadScriptOnce("https://cdn.plot.ly/plotly-2.30.0.min.js"),
    ])
      .then(() => {
        ready.value = true;
      })
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
