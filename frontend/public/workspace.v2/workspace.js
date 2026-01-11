(() => {
    const layoutRoot = document.getElementById("goldenLayoutRoot");
    const btnNewPanel = document.getElementById("createPanel");
    const btnReset = document.getElementById("optimizePanels");
    const sidebarResizer = document.getElementById("sidebarResizer");

    function clamp(n, min, max) {
        return Math.max(min, Math.min(max, n));
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

    function initSidebarResize() {
        let resizing = false;
        let startX = 0;
        let startW = 0;

        sidebarResizer.addEventListener("pointerdown", (e) => {
            resizing = true;
            sidebarResizer.setPointerCapture(e.pointerId);
            startX = e.clientX;
            const cs = getComputedStyle(document.documentElement);
            startW = parseInt(cs.getPropertyValue("--sidebarW"), 10) || 320;
            e.preventDefault();
        });

        sidebarResizer.addEventListener("pointermove", (e) => {
            if (!resizing) return;
            const dx = e.clientX - startX;
            const cs = getComputedStyle(document.documentElement);
            const minW = parseInt(cs.getPropertyValue("--sidebarMin"), 10) || 240;
            const maxW = parseInt(cs.getPropertyValue("--sidebarMax"), 10) || 520;

            const newW = clamp(startW + dx, minW, maxW);
            document.documentElement.style.setProperty("--sidebarW", `${newW}px`);
        });

        sidebarResizer.addEventListener("pointerup", (e) => {
            resizing = false;
            try { sidebarResizer.releasePointerCapture(e.pointerId); } catch { }
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
                    <h3>${safeTitle}</h3>
                    <div class="meta">Golden Layout component</div>
                    <div>${safeDescription}</div>
                </div>
            `;

            const element = container.getElement();
            element.html(html);
        });
    }

    function initialLayoutConfig() {
        return {
            content: [
                {
                    type: "row",
                    content: [
                        createPanelConfig("Overview", "Drag tabs or split panes to rearrange this workspace."),
                        {
                            type: "column",
                            content: [
                                createPanelConfig("Details", "Each panel is a Golden Layout component."),
                                createPanelConfig("Activity", "Use the + New panel button to add more.")
                            ]
                        }
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

        layout.root.contentItems[0].addChild(newPanel);
    }

    function resetLayout() {
        panelCount = 0;
        initLayout();
    }

    initSidebarResize();
    initLayout();

    btnNewPanel.addEventListener("click", addNewPanel);
    btnReset.addEventListener("click", resetLayout);

})();
