export async function fetchWells(horizon, dateIso) {
  const params = new URLSearchParams({ horizon, date: dateIso });
  const res = await fetch(`/api/wells?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch wells");
  }
  return await res.json(); // array of wells
}