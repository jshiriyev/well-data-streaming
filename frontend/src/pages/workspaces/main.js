import "@shared/main.js";
import "../../styles/workspace-golden.css";

import { createGoldenWorkspace } from "./golden-workspace/createGoldenWorkspace.js";
import {
    registerArchieComponents,
    archieSettingsRegistry
} from "./plotly-configs/archie/archie.js";

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

export function initWorkspaces(root = document) {
    const scope = root && typeof root.querySelector === "function" ? root : document;
    const workspaceTypeSelect = scope.querySelector("#workspaceType");
    const plotTypeSelect = scope.querySelector("#plotType");
    const addPanelButton = scope.querySelector("#addPanelBtn");
    const statusEl = scope.querySelector("#workspaceStatus");
    const settingsContent = scope.querySelector("#settingsContent");
    const goldenLayoutRoot = scope.querySelector("#goldenLayoutRoot");
    const controlResizer = scope.querySelector("#controlResizer");
    const settingsResizer = scope.querySelector("#settingsResizer");
    const disposers = [];
    let workspace = null;

    function addListener(target, type, handler, options) {
        if (!target || !target.addEventListener) return;
        target.addEventListener(type, handler, options);
        disposers.push(() => target.removeEventListener(type, handler, options));
    }

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
        if (!goldenLayoutRoot || !settingsContent) {
            setStatus("Workspace root is missing.");
            return;
        }

        if (workspace) {
            workspace.destroy();
            workspace = null;
        }
        resetSettingsContent();

        workspace = createGoldenWorkspace({
            rootEl: goldenLayoutRoot,
            controlResizer,
            settingsResizer,
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

    addListener(workspaceTypeSelect, "change", () => {
        setStatus("Rebuilding workspace...");
        initWorkspace();
    });

    addListener(plotTypeSelect, "change", () => {
        const plotType = getPlotType();
        setStatus(`Next panel: ${plotType?.label || "Panel"}`);
    });

    addListener(addPanelButton, "click", () => {
        if (!workspace) {
            setStatus("Workspace not ready.");
            return;
        }
        workspace.addPanel();
        const plotType = getPlotType();
        setStatus(`Added ${plotType?.label || "panel"}.`);
    });

    initWorkspace();

    return {
        destroy() {
            if (workspace) {
                workspace.destroy();
                workspace = null;
            }
            while (disposers.length) {
                const dispose = disposers.pop();
                dispose();
            }
        }
    };
}

if (typeof document !== "undefined" && document.body?.dataset?.page === "workbench") {
    initWorkspaces(document);
}
