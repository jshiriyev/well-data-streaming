import "@shared/main.js";
import "../../workspaces/golden-workspace/styles.css";
import { createGoldenWorkspace } from "../../workspaces/golden-workspace/createGoldenWorkspace.js";
import {
    registerArchieComponents,
    archieSettingsRegistry
} from "../../workspaces/golden-workspace/configs/archie.js";

const workspaceTypeSelect = document.getElementById("workspaceType");
const plotTypeSelect = document.getElementById("plotType");
const addPanelButton = document.getElementById("addPanelBtn");
const statusEl = document.getElementById("workspaceStatus");
const settingsContent = document.getElementById("settingsContent");

const workspaceTypes = [
    { id: "golden", label: "Golden Layout" }
];

const plotTypes = [
    {
        id: "archie-log",
        label: "Archie Log (Plotly)",
        componentName: "archie-log",
        getState: () => ({ archie: {} })
    }
];

const settingsRegistry = {
    ...archieSettingsRegistry
};

let workspace = null;

function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
}

function resetSettingsContent() {
    if (!settingsContent) return;
    settingsContent.innerHTML = "<p class=\"sidebar-note\">Select a panel to view and edit its settings.</p>";
}

function getPlotType() {
    const selected = plotTypeSelect?.value;
    return plotTypes.find((plot) => plot.id === selected) || plotTypes[0];
}

function createPanelConfig(title, description) {
    const plotType = getPlotType();
    const baseTitle = title || "Panel";
    const panelTitle = plotType?.label ? `${baseTitle}: ${plotType.label}` : baseTitle;
    const state = {
        title: panelTitle,
        description: description || "",
        ...(plotType?.getState ? plotType.getState() : {})
    };

    if (plotType?.componentName) {
        return {
            type: "component",
            componentName: plotType.componentName,
            title: panelTitle,
            componentState: state
        };
    }

    return {
        type: "component",
        componentName: "panel",
        title: panelTitle,
        componentState: state
    };
}

function initGoldenWorkspace() {
    if (workspace) {
        workspace.destroy();
        workspace = null;
    }
    resetSettingsContent();

    workspace = createGoldenWorkspace({
        rootEl: document.getElementById("goldenLayoutRoot"),
        controlResizer: document.getElementById("controlResizer"),
        settingsResizer: document.getElementById("settingsResizer"),
        settingsContent,
        layoutConfig: ({ createPanelConfig: buildPanelConfig, nextPanelIndex }) => ({
            dimensions: {
                headerHeight: 30
            },
            content: [
                {
                    type: "row",
                    content: [
                        buildPanelConfig(
                            `Panel ${nextPanelIndex}`,
                            "Drag tabs or split panes to build your workspace."
                        )
                    ]
                }
            ]
        }),
        registerComponents: registerArchieComponents,
        settingsRegistry,
        createPanelConfig
    });

    setStatus("Golden Layout ready.");
}

function initWorkspace() {
    const workspaceType = workspaceTypeSelect?.value;
    if (workspaceType === "golden") {
        initGoldenWorkspace();
        return;
    }
    setStatus("Workspace type not available yet.");
}

function populateSelect(selectEl, options) {
    if (!selectEl) return;
    selectEl.innerHTML = "";
    options.forEach((option) => {
        const el = document.createElement("option");
        el.value = option.id;
        el.textContent = option.label;
        selectEl.appendChild(el);
    });
}

populateSelect(workspaceTypeSelect, workspaceTypes);
populateSelect(plotTypeSelect, plotTypes);

workspaceTypeSelect?.addEventListener("change", () => {
    setStatus("Rebuilding workspace...");
    initWorkspace();
});

plotTypeSelect?.addEventListener("change", () => {
    const plotType = getPlotType();
    setStatus(`Next panel: ${plotType?.label || "Panel"}`);
});

addPanelButton?.addEventListener("click", () => {
    if (!workspace) {
        setStatus("Workspace not ready.");
        return;
    }
    workspace.addPanel();
    const plotType = getPlotType();
    setStatus(`Added ${plotType?.label || "panel"}.`);
});

initWorkspace();
