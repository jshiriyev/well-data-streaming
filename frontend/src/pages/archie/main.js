import "@shared/main.js";
import "../../workspaces/golden-workspace/styles.css";
import { createGoldenWorkspace } from "../../workspaces/golden-workspace/createGoldenWorkspace.js";
import {
    archieLayoutConfig,
    registerArchieComponents,
    archieSettingsRegistry
} from "../../workspaces/golden-workspace/configs/archie.js";
const settingsContent = document.getElementById("settingsContent");

const workspace = createGoldenWorkspace({
    rootEl: document.getElementById("archieLayoutRoot"),
    controlResizer: document.getElementById("controlResizer"),
    settingsResizer: document.getElementById("settingsResizer"),
    settingsContent,
    layoutConfig: archieLayoutConfig,
    registerComponents: registerArchieComponents,
    settingsRegistry: archieSettingsRegistry
});

window.archieWorkspace = workspace;
