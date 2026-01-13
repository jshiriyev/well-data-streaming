import { getJson } from "../../../../../api/client.js";

const RATES_ENDPOINT = "/api/rates";
const RATES_META_ENDPOINT = "/api/rates/meta";

function normalizeFilterValues(values) {
  if (values === null || values === undefined) return [];
  if (Array.isArray(values)) return values;
  if (values instanceof Set) return Array.from(values);
  return [values];
}

export async function fetchRateMeta() {
  const payload = await getJson(RATES_META_ENDPOINT);
  document.dispatchEvent(new CustomEvent("rate-meta-ready", { detail: payload }));
  return payload;
}

export async function fetchRateData(selectedFilters = {}, aggSelections = {}) {
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
