export function createFilterSidebar({
	host,
	pillHost,
	eventName = "filter-changed",
	legacyEventName,
	onChange,
	templateRoot,
} = {}) {
	const noop = () => {};
	if (!host) {
		return {
			setFields: noop,
			getEffectiveFilters: () => ({}),
			updateFilterPill: noop,
			destroy: noop,
		};
	}

	host.innerHTML = "";
	const wrap = document.createElement("div");
	wrap.className = "efs-wrap";
	wrap.innerHTML = `<div class="efs-columns"></div>`;
	host.appendChild(wrap);

	const colArea = wrap.querySelector(".efs-columns");
	const pill = buildFilterPill(pillHost, templateRoot);

	let fields = [];
	const fieldStates = new Map();

	function setFields(meta) {
		const normalized = normalizeMetadata(meta);
		fields = normalized.fields;
		buildFilterControls();
		updateFilterPill({ emit: false });
	}

	function getEffectiveFilters() {
		const normalized = {};

		fields.forEach((field) => {
			const state = fieldStates.get(field.key);
			if (!state) return;
			const selectedValues = state.values.filter((_, idx) =>
				state.selected.has(idx)
			);
			const hasAllValues =
				state.values.length &&
				state.values.every((_, idx) => state.selected.has(idx));

			if (!hasAllValues) {
				normalized[field.key] = selectedValues;
			}
		});

		return Object.keys(normalized).length ? normalized : {};
	}

	function updateFilterPill({ emit = true } = {}) {
		const filters = getEffectiveFilters();
		const entries = [];

		fields.forEach((field) => {
			const state = fieldStates.get(field.key);
			if (!state) return;
			const hasAllValues =
				state.values.length &&
				state.values.every((_, idx) => state.selected.has(idx));
			if (hasAllValues) return;
			const selectedLabels = state.labels.filter((_, idx) =>
				state.selected.has(idx)
			);
			entries.push({
				label: field.label || field.key,
				values: selectedLabels,
			});
		});

		const summary =
			entries.length > 0
				? entries
						.map((entry) =>
							`${entry.label}: ${entry.values.length ? entry.values.join(", ") : "[ ]"}`
						)
						.join(" | ")
				: "All data";

		if (pill?.chipLabel) {
			pill.chipLabel.textContent = summary;
		}

		if (emit) {
			if (typeof onChange === "function") {
				onChange(filters);
			}
			if (eventName) {
				document.dispatchEvent(new CustomEvent(eventName, { detail: filters }));
			}
			if (legacyEventName && legacyEventName !== eventName) {
				document.dispatchEvent(
					new CustomEvent(legacyEventName, { detail: filters })
				);
			}
		}

		const dropdown = pill?.dropdown;
		const list = pill?.list;

		if (!dropdown || !list) return;

		list.innerHTML = "";

		if (!Object.keys(filters).length) {
			const empty = document.createElement("div");
			empty.className = "filter-empty";
			empty.textContent = "All data (no filter applied)";
			list.appendChild(empty);
			return;
		}

		entries.forEach((entry) => {
			const row = document.createElement("div");
			row.className = "filter-row";

			const fieldEl = document.createElement("div");
			fieldEl.className = "filter-row-field";
			fieldEl.textContent = entry.label;

			const valuesEl = document.createElement("div");
			valuesEl.className = "filter-row-values";
			valuesEl.textContent = entry.values.length ? entry.values.join(", ") : "[ ]";

			row.appendChild(fieldEl);
			row.appendChild(valuesEl);
			list.appendChild(row);
		});
	}

	function buildFilterControls() {
		colArea.innerHTML = "";
		fieldStates.clear();

		fields.forEach((field) => {
			const values = moveBlankToFront(normalizeValues(field.values));
			const labels = values.map((value) => formatFilterValue(value));
			const selected = new Set(values.map((_, idx) => idx));

			fieldStates.set(field.key, {
				key: field.key,
				label: field.label || field.key,
				values,
				labels,
				selected,
			});

			const box = document.createElement("div");
			box.className = "efs-col";

			const head = document.createElement("div");
			head.className = "efs-head";
			const title = document.createElement("div");
			title.className = "efs-title";
			title.textContent = field.label || field.key;
			head.appendChild(title);
			box.appendChild(head);

			const searchEl = document.createElement("input");
			searchEl.className = "efs-search";
			searchEl.type = "text";
			searchEl.name = `filter-${slugifyCategoryName(field.key)}-search`;
			searchEl.id = `${searchEl.name}-${Math.random().toString(36).slice(2, 8)}`;
			searchEl.placeholder = `Search ${field.label || field.key}...`;
			box.appendChild(searchEl);

			const listEl = document.createElement("div");
			listEl.className = "efs-list";

			const selAll = document.createElement("label");
			selAll.className = "efs-item efs-all";
			selAll.setAttribute("data-role", "select-all");

			const selAllChk = document.createElement("input");
			selAllChk.type = "checkbox";
			selAllChk.id = `efs-${field.key}-all-${Math.random()
				.toString(36)
				.slice(2, 8)}`;
			selAllChk.dataset.col = field.key;
			selAllChk.dataset.role = "all";
			selAllChk.checked = true;

			const selAllTxt = document.createElement("span");
			selAllTxt.textContent = "Select all";

			selAll.appendChild(selAllChk);
			selAll.appendChild(selAllTxt);
			listEl.appendChild(selAll);

			const updateSelectAllState = () => {
				let totalVisible = 0;
				let checkedVisible = 0;
				for (const item of listEl.children) {
					if (item.classList.contains("efs-all")) continue;
					if (item.style.display === "none") continue;
					totalVisible += 1;
					const input = item.querySelector("input[type='checkbox']");
					if (input?.checked) checkedVisible += 1;
				}
				selAllChk.checked = totalVisible > 0 && checkedVisible === totalVisible;
				selAllChk.indeterminate =
					checkedVisible > 0 && checkedVisible < totalVisible;
			};

			values.forEach((val, idx) => {
				const labelText = labels[idx];
				const id = `efs-${field.key}-${Math.random()
					.toString(36)
					.slice(2, 8)}`;
				const row = document.createElement("label");
				row.className = "efs-item";
				row.setAttribute("data-index", String(idx));
				row.setAttribute("data-label", labelText.toLowerCase());

				const chk = document.createElement("input");
				chk.type = "checkbox";
				chk.id = id;
				chk.dataset.col = field.key;
				chk.dataset.index = String(idx);
				chk.checked = true;

				chk.addEventListener("change", () => {
					const index = Number(chk.dataset.index);
					if (!Number.isFinite(index)) return;
					if (chk.checked) {
						selected.add(index);
					} else {
						selected.delete(index);
					}
					updateSelectAllState();
					updateFilterPill();
				});

				const txt = document.createElement("span");
				txt.textContent = labelText;

				row.appendChild(chk);
				row.appendChild(txt);

				listEl.appendChild(row);
			});

			box.appendChild(listEl);
			colArea.appendChild(box);

			selAllChk.addEventListener("change", () => {
				const shouldCheck = selAllChk.checked;
				for (const item of listEl.children) {
					if (item.classList.contains("efs-all")) continue;
					if (item.style.display === "none") continue;
					const input = item.querySelector("input[type='checkbox']");
					const index = input ? Number(input.dataset.index) : NaN;
					if (!input || !Number.isFinite(index)) continue;
					if (input.checked !== shouldCheck) {
						input.checked = shouldCheck;
					}
					if (shouldCheck) {
						selected.add(index);
					} else {
						selected.delete(index);
					}
				}
				selAllChk.indeterminate = false;
				updateFilterPill();
			});

			searchEl.addEventListener("input", () => {
				const q = searchEl.value.trim().toLowerCase();
				for (const item of listEl.children) {
					if (
						item.classList.contains("efs-all") ||
						item.getAttribute("data-role") === "select-all"
					) {
						item.style.display = "";
						continue;
					}
					const v = item.getAttribute("data-label") || "";
					item.style.display = v.includes(q) ? "" : "none";
				}
				updateSelectAllState();
			});

			updateSelectAllState();
		});
	}

	return {
		setFields,
		getEffectiveFilters,
		updateFilterPill,
		destroy: () => {
			pill?.destroy?.();
		},
	};
}

function buildFilterPill(pillHost, templateRoot) {
	if (!pillHost) return null;

	const existingChip = pillHost.querySelector(".filter-chip");
	if (!existingChip) {
		const temp = resolveTemplate(templateRoot, "filter-pill");
		if (temp?.content) {
			const node = temp.content.cloneNode(true);
			pillHost.appendChild(node);
		}
	}

	const chip = pillHost.querySelector(".filter-chip");
	const chipLabel = pillHost.querySelector(".filter-chip-label");
	const dropdown = pillHost.querySelector(".filter-dropdown");
	const list = pillHost.querySelector(".filter-dropdown-content");
	const cleanup = [];

	if (chip && dropdown) {
		const closeDropdown = () => {
			chip.setAttribute("aria-expanded", "false");
			dropdown.hidden = true;
		};

		const toggleDropdown = () => {
			const willOpen = dropdown.hidden;
			chip.setAttribute("aria-expanded", willOpen ? "true" : "false");
			dropdown.hidden = !willOpen;
		};

		const onChipClick = (event) => {
			event.stopPropagation();
			toggleDropdown();
		};

		const onDocClick = (event) => {
			if (dropdown.hidden) return;
			const target = event.target;
			if (!dropdown.contains(target) && !chip.contains(target)) {
				closeDropdown();
			}
		};

		const onDocKeydown = (event) => {
			if (event.key === "Escape" && !dropdown.hidden) {
				closeDropdown();
				chip.focus();
			}
		};

		chip.addEventListener("click", onChipClick);
		document.addEventListener("click", onDocClick);
		document.addEventListener("keydown", onDocKeydown);

		cleanup.push(() => chip.removeEventListener("click", onChipClick));
		cleanup.push(() => document.removeEventListener("click", onDocClick));
		cleanup.push(() => document.removeEventListener("keydown", onDocKeydown));
	}

	return { chip, chipLabel, dropdown, list, destroy: () => cleanup.forEach((fn) => fn()) };
}

function resolveTemplate(templateRoot, id) {
	if (templateRoot?.querySelector) {
		const scoped =
			templateRoot.querySelector(`[data-template="${id}"]`) ||
			templateRoot.querySelector(`#${id}`);
		if (scoped) return scoped;
	}
	if (typeof document === "undefined") return null;
	return document.getElementById(id);
}

function formatFilterValue(value) {
	if (value === null || value === undefined || value === "") return "(blank)";
	return String(value);
}

function normalizeValues(values) {
	if (values === null || values === undefined) return [];
	if (Array.isArray(values)) return values.slice();
	if (values instanceof Set) return Array.from(values);
	return [values];
}

function moveBlankToFront(values) {
	const list = Array.isArray(values) ? values.slice() : [];
	const blankIndex = list.indexOf("");
	if (blankIndex > 0) {
		const [blank] = list.splice(blankIndex, 1);
		list.unshift(blank);
	}
	return list;
}

function normalizeMetadata(meta) {
	if (!meta) return { fields: [] };

	if (Array.isArray(meta.fields)) {
		const valuesByField =
			meta.valuesByField && typeof meta.valuesByField === "object"
				? meta.valuesByField
				: meta.categories && typeof meta.categories === "object"
					? meta.categories
					: {};
		return {
			fields: meta.fields
				.map((field) => {
					if (typeof field === "string" || typeof field === "number") {
						const text = String(field);
						return { key: text, label: text, values: valuesByField?.[text] ?? [] };
					}
					const key =
						field?.key ??
						field?.name ??
						field?.id ??
						field?.label;
					if (!key) return null;
					const label = field?.label ?? field?.name ?? key;
					const values =
						field?.values ??
						field?.options ??
						valuesByField?.[key] ??
						[];
					return { key, label, values };
				})
				.filter(Boolean),
		};
	}

	const categories =
		meta.categories && typeof meta.categories === "object"
			? meta.categories
			: meta.valuesByField && typeof meta.valuesByField === "object"
				? meta.valuesByField
				: {};
	const fieldNames = Array.isArray(meta.categorical_fields)
		? meta.categorical_fields
		: Object.keys(categories);

	return {
		fields: fieldNames.map((name) => ({
			key: name,
			label: name,
			values: categories?.[name] ?? [],
		})),
	};
}

function slugifyCategoryName(value, fallback = "field") {
	const normalized = (
		value === null || value === undefined
			? ""
			: String(value).trim()
	)
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "");
	return normalized || fallback;
}
