const layoutRoot = document.getElementById("goldenLayoutRoot");
const controlResizer = document.getElementById("controlResizer");
const settingsResizer = document.getElementById("settingsResizer");
const settingsContent = document.getElementById("settingsContent");
let activeSettingsContainer = null;

// Popouts require same-origin; file:// breaks it.
const allowPopout = ["http:", "https:"].includes(window.location.protocol);
let resizeRaf = 0;

function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
}

function scheduleLayoutResize() {
    if (!layout) return;
    if (resizeRaf) return;
    resizeRaf = window.requestAnimationFrame(() => {
        resizeRaf = 0;
        const rect = layoutRoot.getBoundingClientRect();
        if (rect.width && rect.height) {
            layout.updateSize(rect.width, rect.height);
        } else {
            layout.updateSize();
        }
    });
}

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (m) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[m]));
}

function renamePanel(container, state, titleElement) {
    const currentTitle = state.title || "Panel";
    const nextTitle = window.prompt("Rename panel", currentTitle);
    if (nextTitle === null) return;
    applyPanelTitle(container, state, titleElement, nextTitle);
}

function getPanelElements(container) {
    if (!container || typeof container.getElement !== "function") {
        return { titleEl: null, descriptionEl: null };
    }
    const element = container.getElement()[0];
    if (!element) return { titleEl: null, descriptionEl: null };
    return {
        titleEl: element.querySelector(".gl-panel-title"),
        descriptionEl: element.querySelector(".gl-panel-description")
    };
}

function applyPanelTitle(container, state, titleElement, nextTitle) {
    const trimmed = String(nextTitle || "").trim();
    if (!trimmed) return;
    state.title = trimmed;
    if (typeof container.setTitle === "function") {
        container.setTitle(escapeHtml(trimmed));
    }
    if (titleElement) {
        titleElement.textContent = trimmed;
    }
    if (settingsContent && activeSettingsContainer === container) {
        const header = settingsContent.querySelector('[data-setting="panel-title"]');
        if (header) {
            header.textContent = trimmed;
        }
    }
}

function applyPanelDescription(container, state, descriptionElement, nextDescription) {
    const value = String(nextDescription || "");
    state.description = value;
    if (descriptionElement) {
        descriptionElement.textContent = value;
    }
}

function openPanelSettings(container, state) {
    if (!settingsContent) return;
    activeSettingsContainer = container;

    const elements = getPanelElements(container);
    const titleValue = state.title || "Panel";
    const descriptionValue = state.description || "";

    settingsContent.innerHTML = `
        <div class="settings-panel">
            <div class="settings-heading">Panel: <span data-setting="panel-title"></span></div>
            <label class="settings-field">
                <span class="settings-label">Title</span>
                <input class="settings-input" data-setting="title" type="text" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Description</span>
                <textarea class="settings-input settings-textarea" data-setting="description" rows="3"></textarea>
            </label>
        </div>
    `;

    const panelTitle = settingsContent.querySelector('[data-setting="panel-title"]');
    const titleInput = settingsContent.querySelector('[data-setting="title"]');
    const descriptionInput = settingsContent.querySelector('[data-setting="description"]');

    if (panelTitle) panelTitle.textContent = titleValue;
    if (titleInput) titleInput.value = titleValue;
    if (descriptionInput) descriptionInput.value = descriptionValue;

    if (titleInput) {
        titleInput.addEventListener("input", () => {
            applyPanelTitle(container, state, elements.titleEl, titleInput.value);
        });
    }

    if (descriptionInput) {
        descriptionInput.addEventListener("input", () => {
            applyPanelDescription(container, state, elements.descriptionEl, descriptionInput.value);
        });
    }
}

function initSidebarResize(resizer, widthVar, direction) {
    if (!resizer) return;
    let resizing = false;
    let startX = 0;
    let startW = 0;

    resizer.addEventListener("pointerdown", (e) => {
        resizing = true;
        resizer.setPointerCapture(e.pointerId);
        startX = e.clientX;
        const cs = getComputedStyle(document.documentElement);
        startW = parseInt(cs.getPropertyValue(widthVar), 10) || 320;
        e.preventDefault();
    });

    resizer.addEventListener("pointermove", (e) => {
        if (!resizing) return;
        const dx = e.clientX - startX;
        const cs = getComputedStyle(document.documentElement);
        const minW = parseInt(cs.getPropertyValue("--sidebarMin"), 10) || 240;
        const maxW = parseInt(cs.getPropertyValue("--sidebarMax"), 10) || 520;

        const newW = clamp(startW + (dx * direction), minW, maxW);
        document.documentElement.style.setProperty(widthVar, `${newW}px`);
        scheduleLayoutResize();
    });

    resizer.addEventListener("pointerup", (e) => {
        resizing = false;
        scheduleLayoutResize();
        try { resizer.releasePointerCapture(e.pointerId); } catch { }
    });
}

function showFallback(message) {
    layoutRoot.innerHTML = `
        <div class="gl-fallback">
            <div>
                <strong>Golden Layout failed to load.</strong>
                <div class="meta">${escapeHtml(message)}</div>
            </div>
        </div>
    `;
}

function createPanelConfig(title, description) {
    return {
        type: "component",
        componentName: "panel",
        title,
        componentState: {
            title,
            description
        }
    };
}

function registerComponents(layout) {
    layout.registerComponent("panel", function (container, state) {
        const safeTitle = escapeHtml(state.title || "Panel");
        const safeDescription = escapeHtml(state.description || "");

        const html = `
            <div class="gl-panel">
                <h3 class="gl-panel-title">${safeTitle}</h3>
                <div class="meta">Golden Layout component</div>
                <div class="gl-panel-description">${safeDescription}</div>
            </div>
        `;

        const element = container.getElement();
        element.html(html);
        const titleEl = element[0].querySelector(".gl-panel-title");
        if (typeof container.setTitle === "function") {
            container.setTitle(escapeHtml(state.title || "Panel"));
        }
        if (titleEl) {
            titleEl.title = "Double-click to rename";
            titleEl.addEventListener("dblclick", (e) => {
                e.preventDefault();
                e.stopPropagation();
                renamePanel(container, state, titleEl);
            });
        }
        container.on("tab", function (tab) {
            const tabElement = tab && tab.element;
            if (!tabElement || !tabElement[0]) return;
            const titleNode = tabElement.find(".lm_title")[0] || tabElement[0];
            titleNode.title = "Double-click to rename";
            let settingsButton = tabElement.find(".lm_settings").first();
            if (!settingsButton.length) {
                settingsButton = window.$(`
                    <span class="lm_settings" role="button" aria-label="Open settings" title="Open settings">
                        ⚙
                    </span>
                    `
                );
                const closeTab = tabElement.find(".lm_close_tab").first();
                if (closeTab.length) {
                    settingsButton.insertBefore(closeTab);
                } else {
                    settingsButton.insertAfter(titleNode);
                }
            }
            settingsButton.off("click.glSettings dblclick.glSettings");
            settingsButton.on("click.glSettings", function (e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();

                if (tab && tab.header && tab.header.parent && typeof tab.header.parent.setActiveContentItem === "function") {
                    tab.header.parent.setActiveContentItem(tab.contentItem);
                }

                openPanelSettings(container, state);
            });
            settingsButton.on("dblclick.glSettings", function (e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
            });
            tabElement.off("dblclick.glRename");
            tabElement.on("dblclick.glRename", function (e) {
                if (e.target.closest(".lm_settings") || e.target.closest(".lm_close_tab")) return;
                e.preventDefault();
                e.stopPropagation();
                renamePanel(container, state, titleEl);
            });
        });
    });
}

function initLayoutAutoResize() {
    if (!layoutRoot) return;
    if ("ResizeObserver" in window) {
        const observer = new ResizeObserver(() => scheduleLayoutResize());
        observer.observe(layoutRoot);
    } else {
        window.addEventListener("resize", scheduleLayoutResize);
    }
}

function initialLayoutConfig() {
    panelCount += 1;
    return {
        settings: {
            showPopoutIcon: allowPopout
        },
        dimensions: {
            headerHeight: 30, // Set the desired height in pixels
        },
        content: [
            {
                type: "row",
                content: [
                    createPanelConfig(
                        `Panel ${panelCount}`,
                        "Drag tabs or split panes to rearrange this workspace."),
                ]
            }
        ]
    };
}

let layout = null;
let panelCount = 0;

function initLayout() {
    if (!window.GoldenLayout) {
        showFallback("GoldenLayout is not available on window. Check the script tags in workspace.html.");
        return;
    }

    if (!window.$) {
        showFallback("jQuery is required for Golden Layout v1. The CDN script may not have loaded.");
        return;
    }

    if (layout) {
        layout.destroy();
    }

    layout = new window.GoldenLayout(initialLayoutConfig(), window.$(layoutRoot));
    registerComponents(layout);
    layout.init();
}

function addNewPanel() {
    if (!layout || !layout.root) return;
    panelCount += 1;
    const newPanel = createPanelConfig(
        `Panel ${panelCount}`,
        "This panel was added dynamically. Try dragging it into a new stack or row."
    );

    const rootItems = layout.root.contentItems || [];
    if (!rootItems.length) {
        layout.root.addChild({
            type: "row",
            content: [newPanel]
        });
        return;
    }

    rootItems[0].addChild(newPanel);
}

initSidebarResize(controlResizer, "--controlW", 1);
initSidebarResize(settingsResizer, "--settingsW", -1);
initLayout();
initLayoutAutoResize();
