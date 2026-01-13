import {
    createBox,
    createBoxEmpty,
    getTraceData,
    rebuildMarkers,
    updateTrace,
} from "./parcel.box.js";
import { fetchRateData } from "./api.js";

const boxes = [];

let hostContext = {
    host: null,
    filter: null,
    fields: null,
};

async function refreshBox(box, filterOverride) {
    if (!box?.fig) return;

    const filters =
        filterOverride ??
        hostContext.filter?.getEffectiveFilters?.() ??
        {};
    const aggs = box.seriesPicker.lastAggs || {};

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

function createPlotWrapper({
    host,
    filter,
} = {}) {
    if (!host) {
        return { boxes, addBox: () => null, refreshAll: updateAllFigures };
    }

    hostContext = {
        host: host,
        filter: filter || null,
        fields: hostContext.fields || null,
    };

    const emptyBox = createBoxEmpty(host);
    const firstBox = createBox(host, {
            onAggSelectionsChange: (box) => refreshBox(box),
            index: boxes.length,
        });

    boxes.push(firstBox);

    function setFields(fields) {
		hostContext.fields = fields;
        boxes.forEach((box) => box.seriesPicker?.fillChoices(fields));
	}

    function addBox() {
        const newBox = createBox(host, {
            onAggSelectionsChange: (box) => refreshBox(box),
            index: boxes.length,
        });
        // Fill choices after box creation is complete
        if (hostContext.fields && newBox?.seriesPicker?.fillChoices) {
            newBox.seriesPicker.fillChoices(hostContext.fields);
        }
        boxes.push(newBox);
        return newBox;
    }

    emptyBox.addEventListener("click", () => {
        addBox();
    });

    return {
        host: host,
        boxes,
        get fields() {
            return hostContext.fields;
        },
        setFields,
        addBox,
        refreshAll: updateAllFigures,
        refreshBox,
    };
}

document.addEventListener("filter-changed", (event) => {
    updateAllFigures(event.detail).catch((err) =>
        console.error("Failed to refresh plots after filter change", err)
    );
});

let resizeEndTimer;

window.addEventListener('resize', () => {
    clearTimeout(resizeEndTimer);
    resizeEndTimer = setTimeout(() => {
        boxes.forEach(box => rebuildMarkers(box));
    }, 250);
});

export { createPlotWrapper };
