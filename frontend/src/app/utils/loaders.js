const scriptPromises = new Map();
const stylePromises = new Map();

export function loadScriptOnce(src, { async = true } = {}) {
  if (typeof document === "undefined") return Promise.resolve();
  if (scriptPromises.has(src)) return scriptPromises.get(src);

  const existing = document.querySelector(`script[src="${src}"]`);
  if (existing && existing.dataset.loaded === "true") {
    const resolved = Promise.resolve();
    scriptPromises.set(src, resolved);
    return resolved;
  }

  const promise = new Promise((resolve, reject) => {
    const script = existing || document.createElement("script");
    script.src = src;
    script.async = async;

    const handleLoad = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    const handleError = () => reject(new Error(`Failed to load script: ${src}`));

    script.addEventListener("load", handleLoad, { once: true });
    script.addEventListener("error", handleError, { once: true });

    if (!existing) {
      document.head.appendChild(script);
    }
  });

  scriptPromises.set(src, promise);
  return promise;
}

export function loadStyleOnce(href) {
  if (typeof document === "undefined") return Promise.resolve();
  if (stylePromises.has(href)) return stylePromises.get(href);

  const existing = document.querySelector(`link[href="${href}"]`);
  if (existing && existing.dataset.loaded === "true") {
    const resolved = Promise.resolve();
    stylePromises.set(href, resolved);
    return resolved;
  }

  const promise = new Promise((resolve, reject) => {
    const link = existing || document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;

    const handleLoad = () => {
      link.dataset.loaded = "true";
      resolve();
    };
    const handleError = () => reject(new Error(`Failed to load stylesheet: ${href}`));

    link.addEventListener("load", handleLoad, { once: true });
    link.addEventListener("error", handleError, { once: true });

    if (!existing) {
      document.head.appendChild(link);
    }
  });

  stylePromises.set(href, promise);
  return promise;
}
