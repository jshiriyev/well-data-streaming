import {
    createArchiePanel,
    createArchieState,
    renderArchieSettings as renderArchieSettingsMarkup
} from "../../../plotly/archie.js";

const ARCHIE_TEMPLATE_ID = "archie-log-template";
const ARCHIE_TRAIL_TEMPLATE_ID = "trailSettingsTemplate";
const instances = new WeakMap();
let settingsAutoOpened = false;

export function archieLayoutConfig() {
    return {
        dimensions: {
            headerHeight: 30
        },
        content: [
            {
                type: "row",
                content: [
                    {
                        type: "component",
                        componentName: "archie-log",
                        title: "Log Suite",
                        componentState: {}
                    }
                ]
            }
        ]
    };
}

export function registerArchieComponents(layout, helpers = {}) {
    settingsAutoOpened = false;
    layout.registerComponent("archie-log", function (container, state) {
        const element = container.getElement()[0];
        if (!element) return;

        const instance = createArchiePanel({
            root: element,
            templateId: ARCHIE_TEMPLATE_ID,
            trailTemplateId: ARCHIE_TRAIL_TEMPLATE_ID,
            state: createArchieState(state?.archie || {})
        });

        instances.set(container, instance);

        container.on("resize", () => instance.resize());
        container.on("destroy", () => {
            instances.delete(container);
            instance.destroy();
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
                    tabElement.on("click.glOpenSettings", function (e) {
                        if (e.target.closest(".lm_settings") || e.target.closest(".lm_close_tab")) return;
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

export function renderArchieSettings({ root, container }) {
    if (!root) return;
    renderArchieSettingsMarkup({ root });
    const instance = instances.get(container);
    if (instance) {
        instance.bindSettings(root);
    }
}

export const archieSettingsRegistry = {
    "archie-log": renderArchieSettings
};
