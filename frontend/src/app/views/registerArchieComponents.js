import { createApp } from "vue";
import ArchiePanel from "./ArchiePanel.vue";
import TimeseriesPanel from "./TimeseriesPanel.vue";

let settingsAutoOpened = false;

function mountVuePanel(container, Component, { className, state } = {}) {
  const element = container.getElement()[0];
  if (!element) return null;

  const mountPoint = document.createElement("div");
  if (className) {
    mountPoint.className = className;
  }
  element.appendChild(mountPoint);

  const app = createApp(Component, { state });
  const vm = app.mount(mountPoint);

  return { app, vm, mountPoint };
}

function registerArchiePanel(layout, helpers = {}) {
  settingsAutoOpened = false;

  layout.registerComponent("archie-log", function (container, state) {
    const mounted = mountVuePanel(container, ArchiePanel, {
      className: "archie-vue-root",
      state,
    });
    if (!mounted) return;

    const { app, vm, mountPoint } = mounted;
    container.__archieInstance = vm;

    container.on("resize", () => {
      if (vm?.resize) vm.resize();
    });

    container.on("destroy", () => {
      if (container.__archieInstance === vm) {
        delete container.__archieInstance;
      }
      app.unmount();
      if (mountPoint.parentNode) mountPoint.parentNode.removeChild(mountPoint);
    });

    if (helpers && (helpers.attachTabSettings || helpers.openPanelSettings)) {
      container.on("tab", (tab) => {
        if (typeof helpers.attachTabSettings === "function") {
          helpers.attachTabSettings(tab, container, state);
        }
        if (typeof helpers.openPanelSettings === "function") {
          const tabElement = tab && tab.element;
          if (!tabElement || !tabElement[0]) return;
          tabElement.off("click.glOpenSettings");
          tabElement.on("click.glOpenSettings", function (event) {
            if (event.target.closest(".lm_settings") || event.target.closest(".lm_close_tab")) return;
            helpers.openPanelSettings(container, state);
          });
        }
      });
    }

    if (!settingsAutoOpened && typeof helpers.openPanelSettings === "function") {
      settingsAutoOpened = true;
      helpers.openPanelSettings(container, state);
    }
  });
}

function registerTimeseriesPanel(layout, helpers = {}) {
  layout.registerComponent("timeseries-plot", function (container, state) {
    const mounted = mountVuePanel(container, TimeseriesPanel, {
      className: "timeseries-vue-root",
      state,
    });
    if (!mounted) return;

    const { app, vm, mountPoint } = mounted;

    container.on("resize", () => {
      if (vm?.resize) vm.resize();
    });

    if (helpers && (helpers.attachTabSettings || helpers.openPanelSettings)) {
      container.on("tab", (tab) => {
        if (typeof helpers.attachTabSettings === "function") {
          helpers.attachTabSettings(tab, container, state);
        }
        if (typeof helpers.openPanelSettings === "function") {
          const tabElement = tab && tab.element;
          if (!tabElement || !tabElement[0]) return;
          tabElement.off("click.glOpenSettings");
          tabElement.on("click.glOpenSettings", function (event) {
            if (event.target.closest(".lm_settings") || event.target.closest(".lm_close_tab")) return;
            helpers.openPanelSettings(container, state);
          });
        }
      });
    }

    container.on("destroy", () => {
      app.unmount();
      if (mountPoint.parentNode) mountPoint.parentNode.removeChild(mountPoint);
    });
  });
}

export function registerWorkspaceComponents(layout, helpers = {}) {
  registerArchiePanel(layout, helpers);
  registerTimeseriesPanel(layout, helpers);
}

export const registerArchieComponents = registerWorkspaceComponents;
