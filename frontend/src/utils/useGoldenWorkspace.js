import { ref, shallowRef, unref, watch } from "vue";
import { storeToRefs } from "pinia";
import { createGoldenLayout } from "@components/workspace/golden-layout/createGoldenLayout.js";
import { archieSettingsRegistry } from "@components/workspace/plotly-configs/archie/archie.js";
import { registerWorkspaceComponents } from "@views/registerArchieComponents.js";
import { useWorkspaceStore } from "@stores/workspaces.js";
import { timeseriesSettingsRegistry } from "@components/workspace/plotly-configs/timeseries/timeseries.js";

function resolveElement(value) {
  const resolved = unref(value);
  return resolved || null;
}

export function useGoldenLayout({
  rootEl,
  controlResizer,
  settingsResizer,
  settingsContent,
} = {}) {
  const store = useWorkspaceStore();
  const { workspaceTypes, plotTypes, workspaceType, plotType, status } = storeToRefs(store);
  const workspace = shallowRef(null);
  const initialized = ref(false);

  function setStatus(text) {
    store.setStatus(text);
  }

  function resetSettingsContent() {
    const settingsEl = resolveElement(settingsContent);
    if (!settingsEl) return;
    settingsEl.innerHTML =
      "<p class=\"sidebar-note\">Select a panel to view and edit its settings.</p>";
  }

  function getPlotType() {
    return store.activePlotType || plotTypes.value?.[0];
  }

  function createPanelConfig(title, description) {
    const selected = getPlotType();
    const baseTitle = title || "Panel";
    const panelTitle = selected?.label ? `${baseTitle}: ${selected.label}` : baseTitle;
    const state = {
      title: panelTitle,
      description: description || "",
      ...(selected?.getState ? selected.getState() : {}),
    };

    if (selected?.componentName) {
      return {
        type: "component",
        componentName: selected.componentName,
        title: panelTitle,
        componentState: state,
      };
    }

    return {
      type: "component",
      componentName: "panel",
      title: panelTitle,
      componentState: state,
    };
  }

  function initGoldenWorkspace() {
    const root = resolveElement(rootEl);
    const settingsEl = resolveElement(settingsContent);
    if (!root || !settingsEl) {
      setStatus("Workspace root is missing.");
      return;
    }

    if (workspace.value) {
      workspace.value.destroy();
      workspace.value = null;
    }

    resetSettingsContent();

    workspace.value = createGoldenLayout({
      rootEl: root,
      controlResizer: resolveElement(controlResizer),
      settingsResizer: resolveElement(settingsResizer),
      settingsContent: settingsEl,
      layoutConfig: ({ createPanelConfig: buildPanelConfig, nextPanelIndex }) => ({
        dimensions: {
          headerHeight: 30,
        },
        content: [
          {
            type: "row",
            content: [
              buildPanelConfig(
                `Panel ${nextPanelIndex}`,
                "Drag tabs or split panes to build your workspace."
              ),
            ],
          },
        ],
      }),
      registerComponents: registerWorkspaceComponents,
      settingsRegistry: {
        ...archieSettingsRegistry,
        ...timeseriesSettingsRegistry,
      },
      createPanelConfig,
    });

    setStatus("Golden Layout ready.");
  }

  function initWorkspace() {
    if (workspaceType.value === "golden") {
      initGoldenWorkspace();
      return;
    }
    setStatus("Workspace type not available yet.");
  }

  function init() {
    if (initialized.value) return;
    initialized.value = true;
    initWorkspace();
  }

  function addPanel() {
    if (!workspace.value) {
      setStatus("Workspace not ready.");
      return;
    }
    workspace.value.addPanel();
    const selected = getPlotType();
    setStatus(`Added ${selected?.label || "panel"}.`);
  }

  function destroy() {
    if (workspace.value) {
      workspace.value.destroy();
      workspace.value = null;
    }
  }

  watch(workspaceType, () => {
    if (!initialized.value) return;
    setStatus("Rebuilding workspace...");
    initWorkspace();
  });

  watch(plotType, () => {
    if (!initialized.value) return;
    const selected = getPlotType();
    setStatus(`Next panel: ${selected?.label || "Panel"}`);
  });

  return {
    workspaceTypes,
    plotTypes,
    workspaceType,
    plotType,
    status,
    init,
    addPanel,
    destroy,
  };
}
