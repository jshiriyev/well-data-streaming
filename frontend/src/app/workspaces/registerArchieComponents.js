import { createApp } from "vue";
import ArchiePanel from "../components/workspaces/ArchiePanel.vue";

let settingsAutoOpened = false;

export function registerArchieComponents(layout, helpers = {}) {
  settingsAutoOpened = false;

  layout.registerComponent("archie-log", function (container, state) {
    const element = container.getElement()[0];
    if (!element) return;

    const mountPoint = document.createElement("div");
    mountPoint.className = "archie-vue-root";
    element.appendChild(mountPoint);

    const app = createApp(ArchiePanel, { state });
    const vm = app.mount(mountPoint);

    container.on("resize", () => {
      if (vm?.resize) vm.resize();
    });

    container.on("destroy", () => {
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
