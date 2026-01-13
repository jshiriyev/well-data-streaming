import { buildApiUrl } from "./config.js";

export async function fetchWells(horizon, dateIso) {
  const params = new URLSearchParams({ horizon, date: dateIso });
  const query = params.toString();
  const baseUrl = buildApiUrl("/api/wells");
  const url = query ? `${baseUrl}?${query}` : baseUrl;
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch wells");
  }
  return await res.json(); // array of wells
}
