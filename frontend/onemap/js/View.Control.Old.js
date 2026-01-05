const map = L.map(
	'onemap-map',{
		center: [40.21838483721167, 51.07054395510173],
		...{
			"zoom": 14,
			"zoomControl": false,
			"preferCanvas": false,
			"attributionControl": 0,
		}
	}
);

var tileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
	"minZoom": 0,
	"maxZoom": 19,
	"maxNativeZoom": 19,
	"noWrap": false,
	"attribution": "\u0026copy; \u003ca href=\"https://www.openstreetmap.org/copyright\"\u003eOpenStreetMap\u003c/a\u003e contributors",
	"subdomains": "abc",
	"detectRetina": false,
	"tms": false,
	"opacity": 1,
}).addTo(map);

var filter_sidebar = L.control.sidebar('sidebar-filter', {
	position: 'left',
	autoPan: true,
	closeButton: true,
}).addTo(map);

filter_sidebar.show();

document.addEventListener('keydown', function(e) {
	if (e.shiftKey && (e.key === 'f' || e.key === 'F')) {
		filter_sidebar.toggle();
	}
});

const sidebarRoot = document.getElementById("sidebar-filter");
const host = sidebarRoot.querySelector("#filters-container");

host.innerHTML = "";
const wrap = document.createElement("div");
wrap.className = "efs-wrap";
wrap.innerHTML = `<div class="efs-columns"></div>`;
host.appendChild(wrap);

const colArea = wrap.querySelector(".efs-columns");

function norm(v){ return (v === null || v === undefined) ? "" : String(v).trim(); }

function slugifyAttr(value, fallback = "field") {
	const normalized = norm(value)
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "");
	return normalized || fallback;
}

function formatNumber(value, fractionDigits = 4) {
	if (value === null || value === undefined) return "";
	const numeric = Number(value);
	if (Number.isNaN(numeric)) return "";
	return numeric.toLocaleString(undefined, {
		maximumFractionDigits: fractionDigits,
		minimumFractionDigits: 0
	});
}

function detectColumnTypes(data, threshold = 0.9) {
	const firstRow = data[0];
	const columns = Object.keys(firstRow);
	const columnTypes = {};

	columns.forEach(col => {
		const values = data.map(row => row[col]);
		const numericCount = values.filter(v => !isNaN(parseFloat(v)) && isFinite(v)).length;
		const ratio = numericCount / values.length;
		columnTypes[col] = ratio >= threshold ? "numeric" : "categorical";
	});

	return columnTypes;
}

function createWellDataset(wells) {
	const rowsByWell = new Map();
	const wellIds = [];

	wells.forEach(row => {
		const wellId = norm(row.well);
		if (!wellId) return;
		if (!rowsByWell.has(wellId)) {
			wellIds.push(wellId);
		}
		rowsByWell.set(wellId, row);
	});

	return { rowsByWell, wellIds };
}

function toFiniteNumber(value) {
	if (value === null || value === undefined) return undefined;
	const numeric = Number(value);
	return Number.isFinite(numeric) ? numeric : undefined;
}

function normalizeWellsPayload(raw) {
	let statusColorsOverride;

	const captureStatusColors = candidate => {
		if (!candidate || typeof candidate !== "object") return;
		const entries = Object.entries(candidate).filter(([key, value]) => typeof key === "string" && typeof value === "string" && value.trim());
		if (entries.length) {
			statusColorsOverride = { ...(statusColorsOverride || {}) };
			for (const [key, value] of entries) {
				statusColorsOverride[key] = value.trim();
			}
		}
		if (typeof candidate.default === "string" && candidate.default.trim()) {
			(statusColorsOverride ||= {}).default = candidate.default.trim();
		}
		if (typeof candidate._default === "string" && candidate._default.trim()) {
			(statusColorsOverride ||= {})._default = candidate._default.trim();
		}
	};

	if (raw && typeof raw === "object") {
		captureStatusColors(raw.statusColors);
		// allow nested metadata holders
		captureStatusColors(raw.metadata?.statusColors);
		captureStatusColors(raw?.properties?.statusColors);
	}

	const mapFeatureToRecord = (props = {}, geometry, allowGeometryCoords) => {
		const record = { ...props };

		let lat =
			toFiniteNumber(props.lat) ??
			toFiniteNumber(props.latitude) ??
			toFiniteNumber(props.Latitude);
		let lon =
			toFiniteNumber(props.lon) ??
			toFiniteNumber(props.lng) ??
			toFiniteNumber(props.longitude) ??
			toFiniteNumber(props.Longitude);

		if (allowGeometryCoords && (lat === undefined || lon === undefined)) {
			const coords = Array.isArray(geometry?.coordinates) ? geometry.coordinates : [];
			const geomLon = toFiniteNumber(coords[0]);
			const geomLat = toFiniteNumber(coords[1]);
			if (lat === undefined) lat = geomLat;
			if (lon === undefined) lon = geomLon;
		}

		if (lat === undefined || lon === undefined) {
			return null;
		}

		record.lat = lat;
		record.lon = lon;
		return record;
	};

	if (Array.isArray(raw)) {
		const wells = raw
			.map(item => mapFeatureToRecord(item, null, false))
			.filter(Boolean);
		return { wells, statusColors: statusColorsOverride };
	}

	if (raw && Array.isArray(raw.features)) {
		const crsName = String(raw?.crs?.properties?.name || "");
		const allowGeometryCoords = /4326|CRS84/i.test(crsName);
		const wells = raw.features
			.map(feature => mapFeatureToRecord(feature?.properties || {}, feature?.geometry, allowGeometryCoords))
			.filter(Boolean);
		return { wells, statusColors: statusColorsOverride };
	}

	return { wells: [], statusColors: statusColorsOverride };
}

const DEFAULT_STATUS_COLOR = "#3498db";

const DEFAULT_STATUS_COLORS = Object.freeze({
	"Producing": "#2ecc71",
	"Shut-in": "#e67e22",
	"Workover": "#9b59b6",
	"Suspended": "#c0392b"
});

const markersByWell = new Map();
window._efsMarkersByWell = markersByWell;

const markerColorState = {
	baseResolver: null,
	baseDefault: DEFAULT_STATUS_COLOR,
	activeColumn: null,
	colorsByValue: {},
	defaultColor: DEFAULT_STATUS_COLOR
};
window._efsMarkerColorState = markerColorState;

function resolveMarkerColorForRow(row) {
	const state = markerColorState;
	if (state.activeColumn && row) {
		const column = state.activeColumn;
		const valueKey = norm(row[column]);
		const palette = state.colorsByValue || {};
		if (Object.prototype.hasOwnProperty.call(palette, valueKey)) {
			return palette[valueKey];
		}
		if (Object.prototype.hasOwnProperty.call(palette, "__default")) {
			return palette.__default;
		}
	}

	if (typeof state.baseResolver === "function") {
		const baseColor = state.baseResolver(row);
		if (baseColor) return baseColor;
	}

	if (state.defaultColor) return state.defaultColor;
	return state.baseDefault || DEFAULT_STATUS_COLOR;
}

function applyColorToMarker(marker, color) {
	if (!marker) return;
	const next = color || markerColorState.baseDefault || DEFAULT_STATUS_COLOR;
	if (typeof marker.setStyle === "function") {
		marker.setStyle({ color: next, fillColor: next });
	}
	if (marker.options) {
		marker.options.color = next;
		marker.options.fillColor = next;
	}
	if (marker._defaultStyle) {
		marker._defaultStyle.color = next;
		marker._defaultStyle.fillColor = next;
	} else {
		marker._defaultStyle = {
			color: next,
			fillColor: next,
			fillOpacity: marker.options?.fillOpacity,
			radius: marker.options?.radius,
			weight: marker.options?.weight
		};
	}
}

function applyMarkerColorsToAll() {
	const dataset = window._efsDataset;
	if (!dataset) return;

	for (const [wellId, markers] of markersByWell.entries()) {
		const list = Array.isArray(markers) ? markers : (markers ? [markers] : []);
		if (!list.length) continue;
		const row = dataset.rowsByWell.get(wellId);
		if (!row) continue;
		const resolvedColor = resolveMarkerColorForRow(row);
		for (const marker of list) {
			applyColorToMarker(marker, resolvedColor);
		}
	}
}

function sanitizeColorValue(value) {
	if (typeof value !== "string") return null;
	const trimmed = value.trim();
	return trimmed ? trimmed : null;
}

function createStatusColorResolver(overrides) {
	const palette = {};
	for (const [key, value] of Object.entries(DEFAULT_STATUS_COLORS)) {
		const normalizedKey = norm(key);
		if (normalizedKey) {
			palette[normalizedKey] = value;
		}
	}

	let defaultColor = DEFAULT_STATUS_COLOR;

	if (overrides && typeof overrides === "object") {
		const entries = Object.entries(overrides);
		for (const [key, value] of entries) {
			if (!key) continue;
			if (key === "default" || key === "_default") {
				const color = sanitizeColorValue(value);
				if (color) defaultColor = color;
				continue;
			}
			const color = sanitizeColorValue(value);
			const normalizedKey = norm(key);
			if (color && normalizedKey) {
				palette[normalizedKey] = color;
			}
		}
	}

	const resolver = status => {
		const key = norm(status);
		return Object.prototype.hasOwnProperty.call(palette, key) ? palette[key] : defaultColor;
	};

	return { resolve: resolver, palette, defaultColor };
}

function populateWellPointFeatureGroup(wells, group, statusColorFn, registry) {
	if (registry && typeof registry.clear === "function") {
		registry.clear();
	}

	wells.forEach(w => {
		const wellName = norm(w.well);
		if (!wellName) return;

		const baseColor = typeof statusColorFn === "function" ? statusColorFn(w.status, w) : null;
		const initialColor = markerColorState.activeColumn ? resolveMarkerColorForRow(w) : (baseColor || resolveMarkerColorForRow(w));
		const colorToUse = initialColor || markerColorState.baseDefault || DEFAULT_STATUS_COLOR;

		const marker = L.circleMarker([w.lat, w.lon], {
			bubblingMouseEvents: true,
			color: colorToUse,
			dashArray: null,
			dashOffset: null,
			fill: true,
			fillColor: colorToUse,
			fillOpacity: 1.,
			fillRule: "evenodd",
			lineCap: "round",
			lineJoin: "round",
			opacity: 1.0,
			radius: 4,
			weight: 1,
			stroke: true,		
		})
		.bindPopup(
			`<b>${w.well}</b><br/>
			Field: ${w.field}<br/>
			Platform: ${w.platform}<br/>
			Status: ${w.status}`
		)
		.addTo(group);
		marker.options.__well_id = wellName;
		marker.options.searchKey = wellName;
		marker.feature = marker.feature || { properties: {} };
		marker.feature.properties.searchKey = wellName;
		marker._defaultStyle = {
			color: marker.options.color,
			fillColor: marker.options.fillColor,
			fillOpacity: marker.options.fillOpacity,
			radius: marker.options.radius,
			weight: marker.options.weight
		};

		if (registry) {
			const bucket = registry.get(wellName) || [];
			bucket.push(marker);
			registry.set(wellName, bucket);
		}
	});
}

window.applyMarkerColorScheme = function(options = {}) {
	const columnName = (typeof options.column === "string" && options.column.trim()) ? options.column.trim() : null;
	const colorsInput = (options.colors && typeof options.colors === "object") ? options.colors : null;

	if (!columnName) {
		markerColorState.activeColumn = null;
		markerColorState.colorsByValue = {};
		markerColorState.defaultColor = markerColorState.baseDefault || DEFAULT_STATUS_COLOR;
		applyMarkerColorsToAll();
		document.dispatchEvent(new CustomEvent("efs:marker-colors-applied", {
			detail: { column: null }
		}));
		return;
	}

	const normalizedColors = {};
	if (colorsInput) {
		for (const [rawKey, rawValue] of Object.entries(colorsInput)) {
			const color = sanitizeColorValue(rawValue);
			if (!color) continue;
			const key = rawKey === "__default" ? "__default" : norm(rawKey);
			if (!key && key !== "") continue;
			normalizedColors[key] = color;
		}
	}

	const fallbackColor = sanitizeColorValue(options.defaultColor);
	markerColorState.defaultColor = fallbackColor || markerColorState.baseDefault || DEFAULT_STATUS_COLOR;

	markerColorState.activeColumn = columnName;
	markerColorState.colorsByValue = normalizedColors;

	applyMarkerColorsToAll();

	document.dispatchEvent(new CustomEvent("efs:marker-colors-applied", {
		detail: {
			column: columnName,
			colors: { ...normalizedColors },
			defaultColor: markerColorState.defaultColor
		}
	}));
};

window.getMarkerColoringState = function() {
	return {
		activeColumn: markerColorState.activeColumn,
		colorsByValue: { ...(markerColorState.colorsByValue || {}) },
		defaultColor: markerColorState.defaultColor
	};
};

window.getCategoricalColumnsInfo = function() {
	const state = window._efsState;
	if (!state) return [];

	const result = [];
	const cols = Array.isArray(state.COLS) ? state.COLS : [];
	for (const col of cols) {
		const meta = state.columnEls?.[col];
		if (!meta || meta.type !== "categorical") continue;

		const order = Array.isArray(meta.valueOrder) ? meta.valueOrder : Object.keys(meta.totalCounts || {});
		const labels = meta.labelsByValue || {};
		const counts = meta.totalCounts || {};

		const values = order.map(key => {
			const raw = Object.prototype.hasOwnProperty.call(labels, key) ? labels[key] : key;
			const display = (raw === null || raw === undefined || raw === "") ? "(blank)" : String(raw);
			return {
				key,
				label: display,
				rawLabel: raw,
				count: counts[key] || 0
			};
		});

		result.push({ name: col, values });
	}

	return result;
};

const GEOMETRY_COLUMN_TOKENS = new Set([
	"head",
	"tail",
	"xy",
	"casing",
	"perf",
	"tubing",
]);

function isGeometryColumnName(name) {
	const normalized = norm(name).toLowerCase();
	if (!normalized) return false;
	if (GEOMETRY_COLUMN_TOKENS.has(normalized)) return true;

	const tokens = normalized.split(/[^a-z0-9]+/).filter(Boolean);
	if (!tokens.length) return false;
	return tokens.some(token => GEOMETRY_COLUMN_TOKENS.has(token));
}

function buildFilterControls(wells, types) {
	const selected = {};
	const columnEls = {};

	for (const c in types) {
		if (isGeometryColumnName(c)) continue;
		const sampleRow = wells.find(row => row[c] !== null && row[c] !== undefined);
		const sampleValue = sampleRow ? sampleRow[c] : undefined;
		if (sampleValue && typeof sampleValue === "object") continue;

		const columnType = types[c];

		if (columnType === "categorical") {
			selected[c] = new Set();
			const counts = {};
			const labels = {};

			for (const row of wells) {
				const rawVal = row[c];
				const key = norm(rawVal);
				counts[key] = (counts[key] || 0) + 1;
				if (!(key in labels)) {
					labels[key] = rawVal;
				}
			}

			const box = document.createElement("div");
			box.className = "efs-col";
			const columnSlug = slugifyAttr(c);
			const searchName = `filter-${columnSlug}-search`;
			const searchId = `${searchName}-${Math.random().toString(36).slice(2,8)}`;

			const head = document.createElement("div");
			head.className = "efs-head";

			const title = document.createElement("div");
			title.className = "efs-title";
			title.textContent = c;
			head.appendChild(title);
			box.appendChild(head);

			const searchEl = document.createElement("input");
			searchEl.className = "efs-search";
			searchEl.type = "text";
			searchEl.id = searchId;
			searchEl.name = searchName;
			searchEl.placeholder = `Search ${c}...`;
			box.appendChild(searchEl);

			const listEl = document.createElement("div");
			listEl.className = "efs-list";
			box.appendChild(listEl);

			colArea.appendChild(box);

			const checkboxes = new Map();
			const countSpans = new Map();

			const selAllId = `efs-${c}-all-${Math.random().toString(36).slice(2,8)}`;
			const selAll = document.createElement("label");
			selAll.className = "efs-item efs-all"; // mark as 'select all'
			selAll.setAttribute("data-role", "select-all"); // used by search to keep visible

			const selAllChk = document.createElement("input");
			selAllChk.type = "checkbox";
			selAllChk.id = selAllId;
			selAllChk.dataset.col = c;
			selAllChk.dataset.role = "all";

			// start in the "all selected" state
			selAllChk.checked = true;

			const selAllTxt = document.createElement("span");
			selAllTxt.textContent = "Select all";

			selAll.appendChild(selAllChk);
			selAll.appendChild(selAllTxt);
			listEl.appendChild(selAll);

			const valueKeys = Object.keys(counts);
			const blankIndex = valueKeys.indexOf("");
			if (blankIndex > -1) {
				valueKeys.splice(blankIndex, 1);
				valueKeys.unshift("");
			}

			const updateSelectAllState = () => {
				const total = checkboxes.size;
				let checkedCount = 0;
				for (const input of checkboxes.values()) {
					if (input.checked) checkedCount += 1;
				}
				selAllChk.checked = checkedCount === total;
				selAllChk.indeterminate = checkedCount > 0 && checkedCount < total;
			};

			const triggerFilters = () => {
				if (typeof window.applyWellVisibilityFilters === "function") {
					window.applyWellVisibilityFilters();
				}
			};

			for (const valKey of valueKeys) {
				const display = labels[valKey];
				const labelText = (display === null || display === undefined || display === "") ? "(blank)" : String(display);
				const id = `efs-${c}-${Math.random().toString(36).slice(2,8)}`;
				const row = document.createElement("label");
				row.className = "efs-item";
				row.setAttribute("data-value", valKey);
				row.setAttribute("data-label", labelText.toLowerCase());

				const chk = document.createElement("input");
				chk.type = "checkbox";
				chk.id = id;
				chk.dataset.col = c;
				chk.dataset.val = valKey;

				chk.checked = true;		// start checked
				selected[c].add(valKey);	  // seed selection with all values

				const txt = document.createElement("span");
				txt.textContent = labelText;

				const cnt = document.createElement("span");

				// initial counts are (total/total)
				const tot = counts[valKey] || 0;
				cnt.className = "efs-count";
				cnt.textContent = `(${tot}/${tot})`;

				row.appendChild(chk);
				row.appendChild(txt);
				row.appendChild(cnt);

				listEl.appendChild(row);

				checkboxes.set(valKey, chk);
				countSpans.set(valKey, cnt);

				chk.addEventListener("change", () => {
					if (chk.checked) {
						selected[c].add(valKey);
					} else {
						selected[c].delete(valKey);
					}
					updateSelectAllState();
					triggerFilters();
				});
			}

			updateSelectAllState();

			selAllChk.addEventListener("change", () => {
				const shouldCheck = selAllChk.checked;
				for (const [valKey, input] of checkboxes.entries()) {
					if (input.checked !== shouldCheck) {
						input.checked = shouldCheck;
					}
					if (shouldCheck) {
						selected[c].add(valKey);
					} else {
						selected[c].delete(valKey);
					}
				}
				selAllChk.indeterminate = false;
				triggerFilters();
			});

			searchEl.addEventListener("input", () => {
				const q = searchEl.value.trim().toLowerCase();
				for (const item of listEl.children) {
				// keep the Select All row visible
					if (item.classList.contains("efs-all") || item.getAttribute("data-role") === "select-all") {
						item.style.display = "";
						continue;
					}
					const v = item.getAttribute("data-label") || "";
					item.style.display = v.includes(q) ? "" : "none";
				}
			});

			columnEls[c] = {
				type: "categorical",
				listEl,
				searchEl,
				checkboxes,
				countSpans,
				selectAll: selAllChk,
				totalCounts: counts,
				labelsByValue: labels,
				valueOrder: valueKeys.slice()
			};
			continue;
		}

		if (columnType === "numeric") {
			const columnValues = wells.map(row => row[c]);
			const numericValues = columnValues
				.map(val => (typeof val === "number" ? val : parseFloat(val)))
				.filter(val => !Number.isNaN(val));

			if (numericValues.length === 0) continue;

			numericValues.sort((a, b) => a - b);

			const minValue = numericValues[0];
			const maxValue = numericValues[numericValues.length - 1];
			const stepAttr = numericValues.some(val => !Number.isInteger(val)) ? "any" : "1";

			const valueRange = maxValue - minValue;
			const paddingBase = valueRange === 0 ? Math.max(Math.abs(minValue), Math.abs(maxValue)) : valueRange;
			const padding = (paddingBase || 1) * 0.01;
			let sliderMin = minValue - padding;
			let sliderMax = maxValue + padding;
			if (stepAttr === "1") {
				sliderMin = Math.floor(sliderMin);
				sliderMax = Math.ceil(sliderMax);
			}
			const sliderRange = sliderMax - sliderMin;

			selected[c] = { min: minValue, max: maxValue };

			const box = document.createElement("div");
			box.className = "efs-col";
			const columnSlug = slugifyAttr(c);
			const minName = `range-${columnSlug}-min`;
			const maxName = `range-${columnSlug}-max`;
			const minId = `${minName}-${Math.random().toString(36).slice(2,8)}`;
			const maxId = `${maxName}-${Math.random().toString(36).slice(2,8)}`;

			const head = document.createElement("div");
			head.className = "efs-head";
			const title = document.createElement("div");
			title.className = "efs-title";
			title.textContent = c;
			head.appendChild(title);
			box.appendChild(head);

			const rangeWrap = document.createElement("div");
			rangeWrap.className = "efs-range";

			const valuesWrap = document.createElement("div");
			valuesWrap.className = "efs-range-values";

			const minValueEl = document.createElement("span");
			minValueEl.className = "efs-range-min-value";
			minValueEl.textContent = formatNumber(minValue, 2);

			const maxValueEl = document.createElement("span");
			maxValueEl.className = "efs-range-max-value";
			maxValueEl.textContent = formatNumber(maxValue, 2);

			valuesWrap.appendChild(minValueEl);
			valuesWrap.appendChild(maxValueEl);

			const sliderTrack = document.createElement("div");
			sliderTrack.className = "efs-range-slider";

			const sliderProgress = document.createElement("div");
			sliderProgress.className = "efs-range-progress";
			sliderTrack.appendChild(sliderProgress);

			const pointersWrap = document.createElement("div");
			pointersWrap.className = "efs-range-pointers";

			const minInput = document.createElement("input");
			minInput.className = "efs-range-min";
			minInput.type = "range";
			minInput.id = minId;
			minInput.name = minName;
			minInput.min = String(sliderMin);
			minInput.max = String(sliderMax);
			minInput.step = stepAttr;
			minInput.value = String(sliderMin);

			const maxInput = document.createElement("input");
			maxInput.className = "efs-range-max";
			maxInput.type = "range";
			maxInput.id = maxId;
			maxInput.name = maxName;
			maxInput.min = String(sliderMin);
			maxInput.max = String(sliderMax);
			maxInput.step = stepAttr;
			maxInput.value = String(sliderMax);

			pointersWrap.appendChild(minInput);
			pointersWrap.appendChild(maxInput);

			rangeWrap.appendChild(valuesWrap);
			rangeWrap.appendChild(sliderTrack);
			rangeWrap.appendChild(pointersWrap);

			box.appendChild(rangeWrap);
			colArea.appendChild(box);
			const setActiveHandle = (active) => {
				minInput.classList.toggle("is-top", active === minInput);
				maxInput.classList.toggle("is-top", active === maxInput);
			};
			setActiveHandle(maxInput);

			const syncMin = (val) => {
				const maxVal = parseFloat(maxInput.value);
				if (val > maxVal) {
					val = maxVal;
					minInput.value = String(val);
				}
				selected[c].min = val;
				minValueEl.textContent = formatNumber(val, 2);
				if (sliderProgress && sliderRange !== 0) {
					const relative = Math.max(0, Math.min(1, (val - sliderMin) / sliderRange));
					sliderProgress.style.left = (relative * 100).toFixed(2) + "%";
				}
			};

			const syncMax = (val) => {
				const minVal = parseFloat(minInput.value);
				if (val < minVal) {
					val = minVal;
					maxInput.value = String(val);
				}
				selected[c].max = val;
				maxValueEl.textContent = formatNumber(val, 2);
				if (sliderProgress && sliderRange !== 0) {
					const relative = Math.max(0, Math.min(1, (val - sliderMin) / sliderRange));
					sliderProgress.style.right = (100 - relative * 100).toFixed(2) + "%";
				}
			};

			minInput.addEventListener("input", () => {
				const value = parseFloat(minInput.value);
				if (Number.isNaN(value)) return;
				syncMin(value);
				setActiveHandle(minInput);
				if (typeof window.applyWellVisibilityFilters === "function") {
					window.applyWellVisibilityFilters();
				}
			});

			maxInput.addEventListener("input", () => {
				const value = parseFloat(maxInput.value);
				if (Number.isNaN(value)) return;
				syncMax(value);
				setActiveHandle(maxInput);
				if (typeof window.applyWellVisibilityFilters === "function") {
					window.applyWellVisibilityFilters();
				}
			});

			["pointerdown", "touchstart", "mousedown", "focus"].forEach(evt => {
				minInput.addEventListener(evt, () => setActiveHandle(minInput));
				maxInput.addEventListener(evt, () => setActiveHandle(maxInput));
			});

			syncMin(minValue);
			syncMax(maxValue);

			columnEls[c] = {
				type: "numeric",
				minInput,
				maxInput,
				minDisplay: minValueEl,
				maxDisplay: maxValueEl
			};

			const includeNullLabel = document.createElement("label");
			includeNullLabel.className = "efs-include-null";

			const includeNullCheckbox = document.createElement("input");
			includeNullCheckbox.type = "checkbox";
			includeNullCheckbox.id = `include-null-${columnSlug}`;
			includeNullCheckbox.name = `range-${columnSlug}-include-null`;

			const includeNullText = document.createElement("span");
			includeNullText.textContent = "Include non-numerical data";

			includeNullLabel.appendChild(includeNullCheckbox);
			includeNullLabel.appendChild(includeNullText);
			box.appendChild(includeNullLabel);
		}
	}

	return {
		selected,
		columnEls,
		cols: Object.keys(wells[0]),
		wellsList: wells.map(w => w.well)
	};
}

function configureTailFeatureSearch(mapInstance, wellPointFeatureGroup) {
	const control = new L.Control.Search({
		layer: wellPointFeatureGroup,
		propertyName: 'searchKey',
		collapsed: true,
		textPlaceholder: 'Search Well...',
		position:'topleft',
		initial: true,
		zoom: 16,
		hideMarkerOnCollapse: true
	});

	const resetTailStyles = () => {
		wellPointFeatureGroup.eachLayer(layer => {
			if (typeof layer.setStyle === "function" && layer._defaultStyle) {
				layer.setStyle(layer._defaultStyle);
				if (typeof layer.setRadius === "function" && typeof layer._defaultStyle.radius === "number") {
					layer.setRadius(layer._defaultStyle.radius);
				}
			}
		});
	};

	control.on('search:locationfound', function(e) {
		resetTailStyles();
		if (typeof e.layer.setStyle === "function") {
			e.layer.setStyle({
				// color: '#ffff00',
				// fillColor: '#ffff00',
				fillOpacity: 1
			});
			if (typeof e.layer.bringToFront === "function") {
				e.layer.bringToFront();
			}
		}
		if (e.layer._popup)
			e.layer.openPopup();
	});
	control.on('search:collapsed', function() {
		resetTailStyles();
	});

	resetTailStyles(); // ensure initial styles cached
	mapInstance.addControl(control);

	if (control._container) {
		control._container.classList.add('well-search-control');
	}
	if (control._tooltip) {
		control._tooltip.classList.add('well-search-tooltip');
	}

	const topLeft = mapInstance._controlCorners.topleft;
  	topLeft.insertBefore(control.getContainer(), topLeft.firstChild);

	return control;
}

function applyWellVisibilityFilters() {
	const state = window._efsState;
	const dataset = window._efsDataset;
	if (!state || !dataset) return;

	const { selected, COLS, columnTypes } = state;
	const { rowsByWell, wellIds } = dataset;

	const visible = new Set();

	for (const wid of wellIds) {
		const row = rowsByWell.get(wid);
		if (!row) continue;

		let include = true;
		for (const col of COLS) {
			const control = selected[col];
			if (!control) continue;

			const type = columnTypes?.[col];
			if (type === "categorical") {
				if (control.size === 0) { include = false; break; }
				const rowVal = norm(row[col]);
				if (!control.has(rowVal)) { include = false; break; }
			} else if (type === "numeric") {
				const value = Number(row[col]);
				if (!Number.isFinite(value)) { include = false; break; }
				const min = Number(control.min);
				const max = Number(control.max);
				if (Number.isFinite(min) && value < min) { include = false; break; }
				if (Number.isFinite(max) && value > max) { include = false; break; }
			}
		}

		if (include) {
			visible.add(wid);
		}
	}

	const visibilityState = window._efsVisibilityState ||= new Map();
	for (const wid of wellIds) {
		const shouldShow = visible.has(wid);
		if (visibilityState.get(wid) === shouldShow) continue;
		if (typeof window.toggleWellMarkerVisibility === "function") {
			window.toggleWellMarkerVisibility(wid, shouldShow);
		}
		visibilityState.set(wid, shouldShow);
	}

	if (typeof window.recomputeAvailableCounts === "function") {
		const availableCounts = window.recomputeAvailableCounts(visible);
		if (availableCounts && state.columnEls) {
			for (const col of state.COLS) {
				const columnEl = state.columnEls[col];
				if (!columnEl || columnEl.type !== "categorical") continue;
				const spans = columnEl.countSpans;
				const totals = columnEl.totalCounts || {};
				const colCounts = availableCounts[col] || {};
				for (const [valKey, span] of spans.entries()) {
					const total = totals[valKey] || 0;
					const selectedTotal = colCounts[valKey] || 0;
					span.textContent = `(${selectedTotal}/${total})`;
				}
			}
		}
	}
}

window.applyWellVisibilityFilters = applyWellVisibilityFilters;

fetch("/wells")
	.then(response => response.json())
	.then(raw => {
		const { wells, statusColors: statusColorOverrides } = normalizeWellsPayload(raw);
		const {
			resolve: statusColor,
			palette: statusColorPalette,
			defaultColor: statusColorDefault
		} = createStatusColorResolver(statusColorOverrides);

		window._efsStatusColors = {
			palette: statusColorPalette,
			defaultColor: statusColorDefault
		};

		markerColorState.baseResolver = row => statusColor(row.status);
		markerColorState.baseDefault = statusColorDefault || DEFAULT_STATUS_COLOR;
		if (!markerColorState.activeColumn) {
			markerColorState.defaultColor = statusColorDefault || DEFAULT_STATUS_COLOR;
		}
		if (!markerColorState.colorsByValue || typeof markerColorState.colorsByValue !== "object") {
			markerColorState.colorsByValue = {};
		}

		const wellPointFeatureGroup = L.featureGroup().addTo(map);

		if (wells.length === 0) {
			console.warn("No wells returned; skipping layer setup.");
			return;
		}

		const types = detectColumnTypes(wells);
		const dataset = createWellDataset(wells);
		window._efsDataset = dataset;

		markersByWell.clear();
		populateWellPointFeatureGroup(wells, wellPointFeatureGroup, statusColor, markersByWell);

		const {
			selected,
			columnEls,
			cols: COLS,
			wellsList: WELLS
		} = buildFilterControls(wells, types);

		window._efsState = { selected, columnEls, COLS, WELLS, columnTypes: types };

		document.dispatchEvent(new CustomEvent("efs:dataset-ready", {
			detail: {
				columnTypes: types,
				totalWells: dataset.wellIds.length
			}
		}));

		applyMarkerColorsToAll();

		configureTailFeatureSearch(map, wellPointFeatureGroup);
		applyWellVisibilityFilters();

	})
	.catch(err => console.error("Error loading wells info:", err));

function runHorizonControl(query) {
	const nextFormation = (query ?? "").toString().trim();
	if (!nextFormation) {
		console.warn("Formation query is empty; ignoring submission.");
		return;
	}

	const currentUrl = new URL(window.location.href);
	currentUrl.searchParams.set("field", nextFormation);
	const targetUrl = `${currentUrl.pathname}${currentUrl.search}${currentUrl.hash}`;
	const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;

	if (targetUrl === currentPath) {
		return;
	}

	window.location.assign(targetUrl);
}

const horizonNames = [
	'Fasila',
	'Balakhany',
	'Surakhani',
	'Sabunchi',
];

const horizonControl = new L.Control.Search({
	propertyName: 'searchKey',
	collapsed: true,
	textPlaceholder: 'Search Horizon...',
	position:'topleft',
	initial: true,
	zoom: 16,
	hideMarkerOnCollapse: true,

	// called on submit / type depending on options (see notes below)
	sourceData: function (text, callResponse) {
		const query = text.trim().toLowerCase();
		const results = {};
		horizonNames.forEach((name) => {
			if (!query || name.toLowerCase().includes(query)) {
				results[name] = name;
			}
		});
		callResponse(results);       // return empty results so nothing else happens
		return results;
	},
	formatData: function (value) {
		return value;
	},
	moveToLocation: function () {}, // disable auto pan/zoom
}).addTo(map);

if (horizonControl._container) {
	horizonControl._container.classList.add('horizon-search-control');
}
if (horizonControl._tooltip) {
	horizonControl._tooltip.classList.add('horizon-search-tooltip');
}

horizonControl._button.style.backgroundImage =
  "url('data:image/svg+xml,%3Csvg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"%3E%3Crect x=\"5\" y=\"5\" width=\"14\" height=\"14\" rx=\"2\" ry=\"2\" fill=\"%23000\"/%3E%3C/svg%3E')";
horizonControl._button.style.backgroundSize = '16px 16px';
horizonControl._button.style.backgroundRepeat = 'no-repeat';
horizonControl._button.style.backgroundPosition = 'center';

L.control.zoom({position: 'topleft'}).addTo(map);

(function(){
	const BASE_RECENTER = L.latLng(40.21838483721167, 51.07054395510173);
	const BASE_RECENTER_ZOOM = 14;

	function recenterWithSidebarAwareness(map) {
		const sidebarVisible = filter_sidebar?.isVisible?.();
		let targetCenter = BASE_RECENTER;

		if (sidebarVisible) {
			const sidebarOffset = filter_sidebar.getOffset?.() || 0;
			if (sidebarOffset !== 0) {
				const projected = map.project(BASE_RECENTER, BASE_RECENTER_ZOOM);
				const shifted = projected.add(L.point(-sidebarOffset / 2, 0));
				targetCenter = map.unproject(shifted, BASE_RECENTER_ZOOM);
			}
		}

		const currentCenter = map.getCenter();
		const currentZoom = map.getZoom();
		const needsCenterUpdate = Math.abs(currentCenter.lat - targetCenter.lat) > 1e-6 ||
			Math.abs(currentCenter.lng - targetCenter.lng) > 1e-6;
		const needsZoomUpdate = currentZoom !== BASE_RECENTER_ZOOM;

		if (needsCenterUpdate || needsZoomUpdate) {
			map.setView(targetCenter, BASE_RECENTER_ZOOM, { animate: false });
		}
	}

	const Recenter = L.Control.extend({
	options: { position: 'topleft' },
	onAdd: function(map) {
		var container = L.DomUtil.create('div', 'leaflet-control leaflet-control-recenter');

		// button element
		var btn = L.DomUtil.create('a', 'recenter-btn', container);
		btn.href = '#';
		btn.title = 'Re-center';
		btn.setAttribute('role','button');
		btn.setAttribute('aria-label','Re-center map');

		// crisp “target” SVG icon (white strokes)
		btn.innerHTML = `
		<svg viewBox="0 0 24 24" aria-hidden="true">
			<circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/>
			<path d="M12 4v3 M12 17v3 M4 12h3 M17 12h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
		</svg>
		`;

		// prevent map interactions when clicking/scrolling on the control
		L.DomEvent.disableClickPropagation(container);
		L.DomEvent.disableScrollPropagation(container);

		// click -> reset view
		L.DomEvent.on(btn, 'click', function(e){
			if (e) L.DomEvent.stop(e);
			recenterWithSidebarAwareness(map);
		});

		// keyboard (Enter/Space)
		L.DomEvent.on(btn, 'keydown', function(e){
		if (e.key === 'Enter' || e.key === ' ') {
			if (e) L.DomEvent.stop(e);
			recenterWithSidebarAwareness(map);
		}
		});

		return container;
		}
	});
	map.addControl(new Recenter());
})();

var measureControl = new L.Control.Measure({
	"position": "bottomright",
	"primaryLengthUnit": "meters",
	"secondaryLengthUnit": "kilometers",
	"primaryAreaUnit": "sqmeters",
	"secondaryAreaUnit": "hectares",
	"activeColor": "#ABE67E",
	"completedColor": "#C8F2BE",
	"collapsed": false,
});

map.addControl(measureControl);

// Workaround for using this plugin with Leaflet>=1.8.0
// https://github.com/ljagis/leaflet-measure/issues/171
L.Control.Measure.include({
	_setCaptureMarkerIcon: function () {
		// disable autopan
		this._captureMarker.options.autoPanOnFocus = false;
		// default function
		this._captureMarker.setIcon(
			L.divIcon({
				iconSize: this._map.getSize().multiplyBy(2)
			})
		);
	},
});

// HELPER FUNCTIONS

window.computeMatchedWells = function(){
	// NEW: if literally no boxes are checked anywhere, match nothing
	const totalSelected = COLS.reduce((n, c) => n + selected[c].size, 0);
	if (totalSelected === 0) return new Set();

	// AND across columns: for each column, if selection empty => pass
	// else row[c] must be in selected[c]
	const matched = new Set();
	for (const wid of WELLS) {
		const r = ROWS[wid];
		let ok = true;
		for (const c of COLS) {
			const set = selected[c];
			if (set.size === 0) continue; // no restriction
			const val = norm(r[c]);
			if (!set.has(val)) { ok = false; break; }
	  	}
	  	if (ok) matched.add(wid);
	}
	return matched;
}

window.recomputeAvailableCounts = function(visibleWells){
	const state = window._efsState;
	const dataset = window._efsDataset;
	if (!state || !dataset) return null;

	const { selected, COLS, columnTypes } = state;
	const { rowsByWell, wellIds } = dataset;

	const buildCountsFromSet = (wellSet) => {
		const result = {};
		for (const col of COLS) {
			if (columnTypes?.[col] !== "categorical") continue;

			const columnCounts = {};
			for (const wid of wellSet) {
				const row = rowsByWell.get(wid);
				if (!row) continue;
				const valKey = norm(row[col]);
				columnCounts[valKey] = (columnCounts[valKey] || 0) + 1;
			}
			result[col] = columnCounts;
		}
		return result;
	};

	if (visibleWells instanceof Set) {
		return buildCountsFromSet(visibleWells);
	}

	const countsByColumn = {};
	for (const col of COLS) {
		if (columnTypes?.[col] !== "categorical") continue;

		const columnCounts = {};
		for (const wid of wellIds) {
			const row = rowsByWell.get(wid);
			if (!row) continue;

			let include = true;
			for (const otherCol of COLS) {
				if (otherCol === col) continue;
				const control = selected[otherCol];
				if (!control) continue;

				const type = columnTypes?.[otherCol];
				if (type === "categorical") {
					if (!(control instanceof Set)) { include = false; break; }
					if (control.size === 0) { include = false; break; }
					const val = norm(row[otherCol]);
					if (!control.has(val)) { include = false; break; }
				} else if (type === "numeric") {
					const value = Number(row[otherCol]);
					if (!Number.isFinite(value)) { include = false; break; }
					const min = Number(control.min);
					const max = Number(control.max);
					if (Number.isFinite(min) && value < min) { include = false; break; }
					if (Number.isFinite(max) && value > max) { include = false; break; }
				}
			}

			if (!include) continue;
			const valueKey = norm(row[col]);
			columnCounts[valueKey] = (columnCounts[valueKey] || 0) + 1;
		}
		countsByColumn[col] = columnCounts;
	}

	return countsByColumn;
}

window.classifyLayer = function(l){
	const p = l?.options?.pane;
	if (p === "wellLabelDisplayed") return "label";
	if (p === "wellHeadInteractive") return "head";
	if (p === "wellTailInteractive") return "tail";
	if (p === "wellSurveyDisplayed") return "survey";

	if (typeof l.getLatLng === "function") {
		const el = (l.getElement && l.getElement()) || l._icon || null;
		if (el && (el.matches?.(".well-label") || el.querySelector?.(".well-label"))) return "label";
		if (l?.options?.icon?.options && ("html" in l.options.icon.options)) return "label";
		return "marker";
	}
	if (typeof l.getLatLngs === "function") return "path";
	return "other";
}

indexLayers = function(){

	LAYERS_BY_WELL = {}; // reset cleanly

	function visit(layer){
		if (!layer) return;

		// Try to get id from options
		let wid = layer?.options?.__well_id;

		// 2) fallback from DOM (DivIcon label)
		const el = (layer.getElement && layer.getElement()) || layer._icon || null;

		if (!wid && el) {
			// try <div class="well-label" data-well-id="...">
			const tag = el.matches?.(".well-label") ? el : el.querySelector?.(".well-label");
			const domId = tag?.dataset?.wellId || el?.dataset?.wellId;
			if (domId) {
				wid = domId;
				if (layer.options) layer.options.__well_id = wid; // cache for next runs
			}
		}

		if (wid) {
			(LAYERS_BY_WELL[wid] ||= []).push(layer);
			layer._efs_kind = classifyLayer(layer);
		}

		// Recurse into groups
		if (typeof layer.eachLayer === "function") {
			layer.eachLayer(visit);
		}
	}

	// Walk all top-level layers; this finds children inside FeatureGroups, too.
	map.eachLayer(visit);

}

indexLayers();

window.toggleWellMarkerVisibility = function (wellName, show) {
	window._efsWellMarkerCache ||= new Map();

	const normalized = (wellName || '').trim().toLowerCase();
	if (!normalized) {
		console.warn('toggleWellMarkerVisibility: supply a well name');
		return;
	}

	let targets = window._efsWellMarkerCache.get(normalized) || [];

	if (!targets.length) {
		const found = [];
		map.eachLayer(layer => {
		if (layer instanceof L.CircleMarker) {
			const key = (layer.options?.searchKey || '').toLowerCase();
			if (key === normalized) found.push(layer);
		}
		});
		if (found.length) {
			targets = found;
			window._efsWellMarkerCache.set(normalized, found);
		}
	}

	if (!targets.length) {
		console.warn(`toggleWellMarkerVisibility: no marker found for "${wellName}"`);
		return;
	}

	const makeVisibleExplicit = (typeof show === 'boolean');
	const anyHidden = targets.some(layer => layer._efsHidden);
	const makeVisible = makeVisibleExplicit ? show : anyHidden;

	targets.forEach(layer => {
		const parent =
			layer._efsParentGroup ||
			Object.values(layer._eventParents || {})[0] ||
			null;
		if (parent) layer._efsParentGroup = parent;

		if (makeVisible) {
			if (parent && !parent.hasLayer(layer)) parent.addLayer(layer);
			else if (!layer._map) layer.addTo(map);

			if (layer._defaultStyle && layer.setStyle) layer.setStyle(layer._defaultStyle);
			if (layer._defaultStyle?.radius && layer.setRadius) layer.setRadius(layer._defaultStyle.radius);
			if (layer._path) layer._path.style.display = '';
			layer._efsHidden = false;
		} else {
			layer._efsHidden = true;
			if (parent && parent.hasLayer(layer)) parent.removeLayer(layer);
			else if (layer._map) layer.remove();
		}
	});
};
