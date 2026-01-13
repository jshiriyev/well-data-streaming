import "@shared/main.js";
import "../../../../styles/workspace-golden.css";
import { createGoldenWorkspace } from "../../golden-workspace/createGoldenWorkspace.js";
import {
    archieLayoutConfig,
    registerArchieComponents,
    archieSettingsRegistry
} from "../../golden-workspace/configs/archie.js";
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
