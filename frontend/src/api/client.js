import { buildApiUrl } from "./config.js";

function toSearchParams(params) {
  if (!params) return new URLSearchParams();
  if (params instanceof URLSearchParams) return params;

  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined) return;
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item === null || item === undefined) return;
        search.append(key, String(item));
      });
    } else {
      search.append(key, String(value));
    }
  });
  return search;
}

export function buildUrl(path, params) {
  const base = buildApiUrl(path);
  const search = toSearchParams(params);
  const query = search.toString();
  return query ? `${base}?${query}` : base;
}

export async function getJson(path, { params, init } = {}) {
  const url = buildUrl(path, params);
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}
