import { buildApiUrl } from "./config.js";

const USE_MOCK_WELLS =
  String(import.meta.env.VITE_USE_MOCK_DATA || "").toLowerCase() === "true";

function parseMaybeISODate(s) {
  if (!s) return null;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

// Mock dataset shaped exactly like backend WellOut items:
// { well, horizon, spud_date, lon, lat }
const MOCK_WELLS = [
  { well: "GUN_001", horizon: "QH", spud_date: "2012-03-14T00:00:00", lon: 50.3001, lat: 40.2012, 
    data: ["rates", "logs"],
  },
  { well: "GUN_002", horizon: "QH", spud_date: "2014-07-10T00:00:00", lon: 50.3120, lat: 40.2105,
    data: ["rates", "logs"],
  },
  { well: "GUN_003", horizon: "FH", spud_date: "2016-01-22T00:00:00", lon: 50.2804, lat: 40.1920,
    data: ["rates", "logs"],
   },
  { well: "GUN_004", horizon: "QH", spud_date: "2019-11-05T00:00:00", lon: 50.2952, lat: 40.2159,
    data: ["rates", "logs"],
  },
  { well: "GUN_005", horizon: "FH", spud_date: null, lon: 50.3250, lat: 40.2050,
    data: ["rates", "logs"],
  },
];

function mockFetchWells(horizon, dateIso) {
  // Mirror backend filtering behavior:
  // - if horizon provided, keep only matching props.get("horizon") :contentReference[oaicite:2]{index=2}
  // - if date provided, keep wells with spud_date <= date (when spud_date exists) :contentReference[oaicite:3]{index=3}
  const selectedDate = parseMaybeISODate(dateIso);

  return MOCK_WELLS
    .filter((w) => (horizon ? w.horizon === horizon : true))
    .filter((w) => {
      if (!selectedDate) return true;
      if (!w.spud_date) return true; // backend keeps wells where spud_date is None (it only filters when spud_date exists)
      const spud = parseMaybeISODate(w.spud_date);
      if (!spud) return true;
      return spud <= selectedDate;
    });
}

export async function fetchWells(horizon, dateIso) {
  if (USE_MOCK_WELLS) {
    // async to match real fetch usage
    return Promise.resolve(mockFetchWells(horizon, dateIso));
  }

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
