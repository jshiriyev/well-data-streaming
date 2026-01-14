const globalScope = typeof window !== "undefined" ? window : globalThis;
const envBaseUrl =
  (import.meta.env?.VITE_API_BASE_URL ||
    import.meta.env?.VITE_WELLX_API_BASE_URL ||
    "") + "";

function resolveApiBaseUrl() {
  const runtimeValue =
    (globalScope && globalScope.WELLX_API_BASE_URL) ||
    (globalScope && globalScope.API_BASE_URL) ||
    "";
  const raw = String(runtimeValue || envBaseUrl || "").trim();
  return raw.replace(/\/+$/, "");
}

const apiBaseUrl = resolveApiBaseUrl();

function buildApiUrl(path) {
  if (!apiBaseUrl) return path;
  const normalizedPath = path.charAt(0) === "/" ? path : `/${path}`;
  if (apiBaseUrl.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return apiBaseUrl + normalizedPath.slice(4);
  }
  return apiBaseUrl + normalizedPath;
}

const existing = globalScope.WellxConfig || {};
existing.resolveApiBaseUrl = resolveApiBaseUrl;
existing.buildApiUrl = buildApiUrl;
existing.apiBaseUrl = apiBaseUrl;
globalScope.WellxConfig = existing;

export { apiBaseUrl, buildApiUrl, resolveApiBaseUrl };
