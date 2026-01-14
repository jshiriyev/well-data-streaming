import {
    createBox,
    createBoxEmpty,
    destroyBox,
    getTraceData,
    rebuildMarkers,
    updateTrace,
} from "./parcel.box.js";
import { fetchRateData } from "./api.js";

export function createPlotWrapper({
    host,
    filter,
    eventTarget = document,
    resizeTarget = window,
    templateRoot,
    listen = true,
} = {}) {
    if (!host) {
        return {
            boxes: [],
            addBox: () => null,
            refreshAll: async () => {},
            refreshBox: async () => {},
            setFields: () => {},
            resize: () => {},
            destroy: () => {},
        };
    }

    const boxes = [];
    const disposers = [];
    let resizeEndTimer = 0;

    const hostContext = {
        host,
        filter: filter || null,
        fields: null,
    };

    async function refreshBox(box, filterOverride) {
        if (!box?.fig) return;

        const filters =
            filterOverride ??
            hostContext.filter?.getEffectiveFilters?.() ??
            {};
        const aggs = box.seriesPicker?.lastAggs || {};

        try {
            const data = await fetchRateData(filters, aggs);
            box.data = data;
            (box.fig.traces || []).forEach((trace) => {
                updateTrace(box, getTraceData(data, trace.name));
            });
        } catch (error) {
            console.error("Failed to refresh plot data", error);
        }
    }

    async function updateAllFigures(filterOverride) {
        if (!boxes.length) return;

        const filter =
            filterOverride ??
            hostContext.filter?.getEffectiveFilters?.() ??
            {};

        await Promise.all(boxes.map((box) => refreshBox(box, filter)));
    }

    function setFields(fields) {
        hostContext.fields = fields;
        boxes.forEach((box) => box.seriesPicker?.fillChoices?.(fields));
    }

    function addBox() {
        const newBox = createBox(hostContext.host, {
            fields: hostContext.fields,
            onAggSelectionsChange: (box) => refreshBox(box),
            index: boxes.length,
            templateRoot,
        });

        if (!newBox) return null;

        if (hostContext.fields && newBox?.seriesPicker?.fillChoices) {
            newBox.seriesPicker.fillChoices(hostContext.fields);
        }

        boxes.push(newBox);
        return newBox;
    }

    const emptyBox = createBoxEmpty(hostContext.host);
    addBox();

    if (emptyBox) {
        emptyBox.addEventListener("click", addBox);
        disposers.push(() => emptyBox.removeEventListener("click", addBox));
    }

    if (listen && eventTarget?.addEventListener) {
        const onFilterChanged = (event) => {
            updateAllFigures(event.detail).catch((err) =>
                console.error("Failed to refresh plots after filter change", err)
            );
        };

        eventTarget.addEventListener("filter-changed", onFilterChanged);
        disposers.push(() => eventTarget.removeEventListener("filter-changed", onFilterChanged));
    }

    if (listen && resizeTarget?.addEventListener) {
        const onResize = () => {
            if (resizeEndTimer) clearTimeout(resizeEndTimer);
            resizeEndTimer = setTimeout(() => {
                boxes.forEach((box) => rebuildMarkers(box));
            }, 250);
        };

        resizeTarget.addEventListener("resize", onResize);
        disposers.push(() => resizeTarget.removeEventListener("resize", onResize));
    }

    function resize() {
        boxes.forEach((box) => rebuildMarkers(box));
    }

    function destroy() {
        if (resizeEndTimer) {
            clearTimeout(resizeEndTimer);
            resizeEndTimer = 0;
        }
        while (disposers.length) {
            const dispose = disposers.pop();
            dispose();
        }
        while (boxes.length) {
            const box = boxes.pop();
            destroyBox(box);
        }
        if (hostContext.host) {
            hostContext.host.innerHTML = "";
        }
    }

    return {
        host: hostContext.host,
        boxes,
        get fields() {
            return hostContext.fields;
        },
        setFields,
        addBox,
        refreshAll: updateAllFigures,
        refreshBox,
        resize,
        destroy,
    };
}
