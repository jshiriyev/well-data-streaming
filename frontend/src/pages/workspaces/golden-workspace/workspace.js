import { createGoldenWorkspace } from "./createGoldenWorkspace.js";

const workspace = createGoldenWorkspace({
    rootEl: document.getElementById("goldenLayoutRoot"),
    controlResizer: document.getElementById("controlResizer"),
    settingsResizer: document.getElementById("settingsResizer"),
    settingsContent: document.getElementById("settingsContent"),
    createPanelConfig: (title, description) => {
        const safeTitle = String(title || "Panel").trim() || "Panel";
        return {
            type: "component",
            componentName: "panel",
            title: safeTitle,
            componentState: {
                title: safeTitle,
                description: String(description || "")
            }
        };
    }
});

window.goldenWorkspace = workspace;
