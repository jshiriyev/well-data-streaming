const PANDAS_AGG_OPTIONS = [
    { value: "sum", label: "Sum" },
    { value: "mean", label: "Mean" },
    { value: "median", label: "Median" },
    { value: "min", label: "Min" },
    { value: "max", label: "Max" },
    { value: "count", label: "Count" },
    { value: "std", label: "Standard deviation" },
    { value: "var", label: "Variance" },
    { value: "first", label: "First" },
    { value: "last", label: "Last" },
];

const DEFAULT_AGG = PANDAS_AGG_OPTIONS[0].value;

const seriesPickerRegistry = new Set();
let globalSeriesPickerListenersAttached = false;

function registerSeriesPicker(instance) {
    seriesPickerRegistry.add(instance);
    if (globalSeriesPickerListenersAttached) return;

    document.addEventListener("pointerdown", (event) => {
        if (event.target.closest(".add-button")) return;
        seriesPickerRegistry.forEach((picker) => {
            if (!picker.isOpen()) return;
            if (picker.contains(event.target)) return;
            picker.hide();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        seriesPickerRegistry.forEach((picker) => {
            if (picker.isOpen()) {
                picker.hide();
            }
        });
    });

    globalSeriesPickerListenersAttached = true;
}

function createSeriesPicker(
    box,
    {
        getFigure,
        getTraceData,
        setTrace,
        removeTrace,
        fields,
        onAggSelectionsChange,
    } = {}
) {
    if (!box) return null;
    if (box.seriesPicker) return box.seriesPicker;

    const picker = box.querySelector(".series-picker");
    if (!picker) return null;

    const template = document.getElementById("series-picker");
    if (!template) return null;

    const root = template.content.cloneNode(true);
    const header = root.querySelector(".series-picker-header");
    const choices = root.querySelector(".series-picker-choices");
    const confirmButton = root.querySelector(".confirmButton");
    const cancelButton = root.querySelector(".cancelButton");

    if (!choices || !confirmButton || !cancelButton) return null;

    const match = box.id?.match(/\d+$/);
    const instanceId = match ? match[0] : Math.random().toString(36).slice(2, 8);
    picker.id = `series-picker-${instanceId}`;

    if (header) {
        header.textContent = `Box #${instanceId}: Series & Aggregation`;
    }

    const resolveFigure = () => {
        return getFigure?.() ?? box.fig ?? null;
    };

    const resolveFields = (fields) => {
        return Array.isArray(fields) ? fields : [];
    };

    const resolveGetTraceData = getTraceData ?? null;
    const resolveSetTrace = setTrace ?? null;
    const resolveRemoveTrace = removeTrace ?? null;

    const aggSelections =
        fields && typeof fields === "object"
            ? fields
            : {};

    const getCurrentTraceNames = () => {
        const current = new Set();
        const fig = resolveFigure();
        fig?.traces?.forEach((trace) => current.add(trace.name));
        return current;
    };

    const syncPickerState = () => {
        const activeNames = getCurrentTraceNames();
        choices.querySelectorAll("label").forEach((label) => {
            const cb = label.querySelector('input[name="choice"]');
            const select = label.querySelector('select[name="agg-select"]');
            if (!cb || !select) return;

            const savedAgg = aggSelections?.[cb.value];
            if (savedAgg) {
                select.value = savedAgg;
            }
            const shouldCheck = activeNames.has(cb.value);
            cb.checked = shouldCheck;
            select.disabled = !cb.checked;
        });
    };

    const fillChoices = (fields) => {
        choices.innerHTML = "";
        const numericFields = resolveFields(fields);
        const activeNames = getCurrentTraceNames();

        numericFields.forEach((key) => {
            const label = document.createElement("label");
            const input = document.createElement("input");
            input.type = "checkbox";
            input.name = "choice";
            input.value = key;

            const select = document.createElement("select");
            select.name = "agg-select";
            select.id = `agg-${instanceId}-${key}`;
            PANDAS_AGG_OPTIONS.forEach(({ value, label }) => {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = label;
                select.appendChild(option);
            });
            select.value = aggSelections?.[key] ?? DEFAULT_AGG;

            input.checked = activeNames.has(key);
            select.disabled = !input.checked;

            input.addEventListener("change", function () {
                if (this.checked) {
                    select.disabled = false;
                    if (aggSelections?.[key]) {
                        select.value = aggSelections[key];
                    }
                } else {
                    select.disabled = true;
                }
            });

            label.appendChild(input);
            label.appendChild(document.createTextNode(key));
            label.appendChild(select);
            choices.appendChild(label);
        });

        syncPickerState();
    };

    const setTraceButton = box.querySelector(".add-button");
    const openPicker = () => {
        syncPickerState();
        picker.style.display = "inline-block";
        picker.style.position = "absolute";
        if (box._seriesPickerPos) {
            applyPosition(box._seriesPickerPos.x, box._seriesPickerPos.y);
        }
        const target = picker.querySelector('input[name="choice"]') ||
            picker.querySelector('select[name="agg-select"]');
        target?.focus();
    };

    if (setTraceButton) {
        setTraceButton.addEventListener("click", (event) => {
            event.stopPropagation();
            openPicker();
        });
    }

    confirmButton.addEventListener("click", async () => {
        const fig = resolveFigure();
        if (!fig) {
            picker.style.display = "none";
            return;
        }

        const checked = Array.from(
            picker.querySelectorAll('input[name="choice"]:checked')
        );
        const selectionSet = new Set();
        const pendingAgg = new Map();

        checked.forEach((cb) => {
            const label = cb.closest("label");
            const agg = label?.querySelector('select[name="agg-select"]')?.value ?? DEFAULT_AGG;
            pendingAgg.set(cb.value, agg);
            selectionSet.add(cb.value);
        });

        const currentNames = new Set(fig?.traces?.map((trace) => trace.name) || []);
        const toRemove = [...currentNames].filter((name) => !selectionSet.has(name));
        const toAdd = [...selectionSet].filter((name) => !currentNames.has(name));

        // Track if aggregations changed for existing traces
        let aggChanged = false;
        pendingAgg.forEach((agg, key) => {
            if (currentNames.has(key) && aggSelections[key] !== agg) {
                aggChanged = true;
            }
            aggSelections[key] = agg;
        });

        Object.keys(aggSelections).forEach((key) => {
            if (!selectionSet.has(key)) {
                delete aggSelections[key];
            }
        });

        confirmButton.disabled = true;

        try {
            if (resolveRemoveTrace) {
                toRemove.forEach((name) => resolveRemoveTrace(box, name));
            }

            if (resolveSetTrace && resolveGetTraceData) {
                toAdd.forEach((name) => resolveSetTrace(box, resolveGetTraceData(name)));
            }

            // Call onAggSelectionsChange if traces changed OR aggregations changed
            if (toRemove.length > 0 || toAdd.length > 0 || aggChanged) {
                const aggChangeResult = onAggSelectionsChange?.(
                    box,
                    aggSelections
                );
                if (aggChangeResult && typeof aggChangeResult.then === "function") {
                    await aggChangeResult;
                }
            }

            picker.style.display = "none";
        } catch (error) {
            console.error("Failed to refresh plots", error);
        } finally {
            confirmButton.disabled = false;
        }
    });

    cancelButton.addEventListener("click", () => {
        picker.style.display = "none";
    });

    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;
    let lastPos = null;

    const getViewportRect = () => ({
        width: document.documentElement.clientWidth,
        height: document.documentElement.clientHeight,
    });

    const getFixedContainingBlock = (el) => {
        let node = el?.parentElement;
        while (node && node !== document.body && node !== document.documentElement) {
            const style = window.getComputedStyle(node);
            const willChange = style.willChange || "";
            if (
                style.transform !== "none" ||
                style.filter !== "none" ||
                style.perspective !== "none" ||
                willChange.includes("transform") ||
                willChange.includes("filter") ||
                willChange.includes("perspective")
            ) {
                return node;
            }
            node = node.parentElement;
        }
        return document.documentElement;
    };

    const applyPosition = (x, y) => {
        const viewportRect = getViewportRect();
        const bounds = picker.getBoundingClientRect();
        const container = getFixedContainingBlock(picker);
        const containerRect = container === document.documentElement
            ? { left: 0, top: 0 }
            : container.getBoundingClientRect();
        const maxX = viewportRect.width - bounds.width;
        const maxY = viewportRect.height - bounds.height;
        const clampedX = Math.min(Math.max(x, 0), maxX);
        const clampedY = Math.min(Math.max(y, 0), maxY);
        picker.style.left = `${clampedX - containerRect.left}px`;
        picker.style.top = `${clampedY - containerRect.top}px`;
        picker.style.position = "fixed";
        lastPos = { x: clampedX, y: clampedY };
    };

    const handleDragStart = (e) => {
        if (e.button !== 0) return;
        if (e.target.closest("input, select, textarea, button, label")) return;
        isDragging = true;
        const rect = picker.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        picker.style.transition = "none";

        const onMouseMove = (evt) => {
            if (!isDragging) return;
            const x = evt.clientX - offsetX;
            const y = evt.clientY - offsetY;
            applyPosition(x, y);
        };

        const onMouseUp = () => {
            isDragging = false;
            picker.style.transition = "";
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
            if (lastPos) {
                box._seriesPickerPos = { ...lastPos };
            }
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    };

    picker.addEventListener("mousedown", handleDragStart);
    picker.appendChild(root);

    const api = {
        root: picker,
        isOpen: () => picker.style.display === "inline-block",
        contains: (node) => picker.contains(node),
        show: openPicker,
        hide: () => {
            picker.style.display = "none";
        },
        destroy: () => {
            picker.removeEventListener("mousedown", handleDragStart);
            seriesPickerRegistry.delete(api);
        },
        fillChoices,
        lastAggs: aggSelections,
    };

    registerSeriesPicker(api);

    return api;
}
