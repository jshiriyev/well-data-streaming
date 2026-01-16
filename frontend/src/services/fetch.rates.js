import { getJson } from "./client.js";

const RATES_ENDPOINT = "/api/rates";
const RATES_META_ENDPOINT = "/api/rates/meta";

const USE_MOCK_RATES = String(import.meta.env.VITE_USE_MOCK_DATA || "").toLowerCase() === "true";

function normalizeFilterValues(values) {
  if (values === null || values === undefined) return [];
  if (Array.isArray(values)) return values;
  if (values instanceof Set) return Array.from(values);
  return [values];
}

function makeMockMeta() {
  return {
    date_column: "date",
    numeric_fields: ["oil_rate", "water_rate", "gas_rate", "choke"],
    categorical_fields: ["well", "operation"],
    categories: {
      well: ["GUN_001", "GUN_002", "GUN_004", "GUN_005"],
      operation: ["prod", "inject"],
    },
    category_counts: {
      well: 4,
      operation: 2,
    },
  };
}

function mulberry32(seed) {
  // deterministic small PRNG so UI is stable between reloads
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function toISODate(d) {
  // YYYY-MM-DD
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function parseMaybeISODate(s) {
  if (!s) return null;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
}

function lastNDaysDates(n, endDate = new Date()) {
  const dates = [];
  const end = new Date(endDate);
  end.setHours(0, 0, 0, 0);
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(end);
    d.setDate(end.getDate() - i);
    dates.push(toISODate(d));
  }
  return dates;
}

/**
 * Create mock rates *after aggregation-by-date* (so it matches your /rates output).
 * Supports:
 * - date range via params.start / params.end (optional)
 * - limit via params.limit (optional)
 * - filters (well/operation) via selectedFilters (optional)
 *
 * NOTE: Your backend supports agg params per field (e.g., oil_rate:sum). In mock mode
 * we keep it simple: we produce one value per date already (like "sum" result).
 */
function makeMockRatesPayload({ selectedFilters = {}, aggSelections = {}, start, end, limit } = {}) {
  const meta = makeMockMeta();

  // Determine which dates to return (similar spirit to DEFAULT_LOOKBACK_DAYS in backend)
  const defaultDays = 60; // keep frontend payload lighter than 365 for dev
  const endDate = parseMaybeISODate(end) || new Date();
  const startDate = parseMaybeISODate(start);

  let dates;
  if (startDate) {
    // build inclusive range [start..end]
    const s = new Date(startDate);
    s.setHours(0, 0, 0, 0);
    const e = new Date(endDate);
    e.setHours(0, 0, 0, 0);
    dates = [];
    for (let d = new Date(s); d <= e; d.setDate(d.getDate() + 1)) {
      dates.push(toISODate(d));
    }
  } else {
    dates = lastNDaysDates(defaultDays, endDate);
  }

  if (typeof limit === "number" && limit > 0 && dates.length > limit) {
    dates = dates.slice(dates.length - limit);
  }

  // Respect the "empty filter means empty payload" behavior you already have
  const hasEmptyFilter = Object.entries(selectedFilters).some(([, values]) => {
    const normalized = normalizeFilterValues(values);
    return normalized.length === 0;
  });
  if (hasEmptyFilter) {
    const emptyPayload = { date: [] };
    Object.keys(aggSelections || {}).forEach((field) => {
      if (field) emptyPayload[field] = [];
    });
    return emptyPayload;
  }

  // Choose a deterministic seed from filters so series looks consistent per selection
  const seedBase = JSON.stringify(selectedFilters) + JSON.stringify(aggSelections);
  let seed = 0;
  for (let i = 0; i < seedBase.length; i++) seed = (seed * 31 + seedBase.charCodeAt(i)) >>> 0;
  const rand = mulberry32(seed || 1);

  // Determine which wells/ops are selected; if none passed, use all (common frontend expectation)
  const selectedWells = normalizeFilterValues(selectedFilters.well);
  const selectedOps = normalizeFilterValues(selectedFilters.operation);
  const wells = selectedWells.length ? selectedWells : meta.categories.well;
  const ops = selectedOps.length ? selectedOps : meta.categories.operation;

  // Build payload columns
  const payload = { date: dates.slice() };

  // Decide which numeric fields to emit:
  // - if aggSelections provided, emit those keys
  // - else emit a default set
  const fieldsToEmit = Object.keys(aggSelections || {}).filter(Boolean);
  const numericFields = fieldsToEmit.length ? fieldsToEmit : ["oil_rate", "water_rate", "gas_rate"];

  for (const f of numericFields) payload[f] = [];

  // Create plausible daily series
  // (You can tweak these ranges whenever you want)
  for (let i = 0; i < dates.length; i++) {
    // simulate some seasonality/trend
    const t = i / Math.max(1, dates.length - 1);
    const activityFactor = 0.7 + 0.6 * Math.sin(2 * Math.PI * t);

    // simulate that more wells selected -> higher summed rates
    const wellFactor = Math.max(1, wells.length);
    const opFactor = ops.includes("inject") && !ops.includes("prod") ? 0.2 : 1.0;

    // base values
    const oil = Math.round((800 + 400 * activityFactor + 150 * (rand() - 0.5)) * wellFactor * opFactor);
    const water = Math.round((500 + 300 * (1 - activityFactor) + 120 * (rand() - 0.5)) * wellFactor);
    const gas = Math.round((200 + 120 * activityFactor + 60 * (rand() - 0.5)) * wellFactor);

    for (const f of numericFields) {
      if (f === "oil_rate") payload[f].push(Math.max(0, oil));
      else if (f === "water_rate") payload[f].push(Math.max(0, water));
      else if (f === "gas_rate") payload[f].push(Math.max(0, gas));
      else if (f === "choke") payload[f].push(Math.round(16 + 8 * rand())); // example
      else payload[f].push(Math.round(100 * rand())); // fallback
    }
  }

  return payload;
}

export async function fetchRateMeta() {
  const payload = USE_MOCK_RATES ? makeMockMeta() : await getJson(RATES_META_ENDPOINT);
  document.dispatchEvent(new CustomEvent("rate-meta-ready", { detail: payload }));
  return payload;
}

export async function fetchRateData(selectedFilters = {}, aggSelections = {}, options = {}) {
  // options can include: { start, end, limit }
  const { start, end, limit } = options || {};

  if (USE_MOCK_RATES) {
    const payload = makeMockRatesPayload({ selectedFilters, aggSelections, start, end, limit });
    document.dispatchEvent(new CustomEvent("rate-data-ready", { detail: payload }));
    return payload;
  }

  const hasEmptyFilter = Object.entries(selectedFilters).some(([, values]) => {
    const normalized = normalizeFilterValues(values);
    return normalized.length === 0;
  });

  if (hasEmptyFilter) {
    const emptyPayload = { date: [] };
    Object.keys(aggSelections || {}).forEach((field) => {
      if (field) emptyPayload[field] = [];
    });
    document.dispatchEvent(new CustomEvent("rate-data-ready", { detail: emptyPayload }));
    return emptyPayload;
  }

  const params = {};
  Object.entries(selectedFilters).forEach(([field, values]) => {
    const normalized = normalizeFilterValues(values);
    if (normalized.length) {
      params[field] = normalized;
    }
  });

  const aggParams = Object.entries(aggSelections)
    .filter(([field, agg]) => field && agg)
    .map(([field, agg]) => `${field}:${agg}`);
  if (aggParams.length) {
    params.agg = aggParams;
  }

  const payload = await getJson(RATES_ENDPOINT, { params });
  document.dispatchEvent(new CustomEvent("rate-data-ready", { detail: payload }));
  return payload;
}

export { normalizeFilterValues };
