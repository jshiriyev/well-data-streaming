(() => {
    // const canvas = document.getElementById("canvas");
    const gridBg = document.getElementById("gridBg");
    const dockItems = document.getElementById("dockItems");

    // Sidebar resize
    const sidebarResizer = document.getElementById("sidebarResizer");

    // ----- Sidebar resizable -----
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
    initSidebarResize();

    // Top buttons
    const btnNewPanel = document.getElementById("createPanel");
    const btnSpacePanel = document.getElementById("optimizePanels");

    // Grid controls
    const gridSizeSel = document.getElementById("gridSizeRange");

    let zTop = 10;
    let panelCount = 0;
    let gridModeOn = false;
    let gridSnapOn = false;
    let gridSnapMode = "none";

    function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

    function escapeHtml(str) {
        return String(str).replace(/[&<>"']/g, (m) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[m]));
    }

    function focusPanel(panel) {
        [...canvas.querySelectorAll(".panel")].forEach(p => p.dataset.focused = "false");
        panel.dataset.focused = "true";
        panel.style.zIndex = String(++zTop);
    }

    function getCanvasRect() {
        return canvas.getBoundingClientRect();
    }

    function getGridSize() {
        return parseInt(gridSizeSel.value, 10) || 32;
    }

    function snap(n) {
        if (gridSnapMode !== "snap") return n;
        const s = getGridSize();
        return Math.round(n / s) * s;
    }

    function setGridSizeCss() {
        document.documentElement.style.setProperty("--gridSize", `${getGridSize()}px`);
    }
    setGridSizeCss();

    // ----- Dock (minimized panels) -----
    function addToDock(panel) {
        // already exists?
        if (dockItems.querySelector(`[data-dock-for="${panel.id}"]`)) return;

        const pill = document.createElement("div");
        pill.className = "dock-pill";
        pill.dataset.dockFor = panel.id;

        const title = panel.querySelector(".panel-title span").textContent || panel.id;

        pill.innerHTML = `
            <span>${escapeHtml(title)}</span>
            <span class="mini-x" title="Close">×</span>
          `;

        pill.addEventListener("click", (e) => {
            // close from dock
            if (e.target.closest(".mini-x")) {
                panel.remove();
                pill.remove();
                return;
            }
            // restore
            restoreFromDock(panel);
        });

        dockItems.appendChild(pill);
    }

    function removeFromDock(panel) {
        const pill = dockItems.querySelector(`[data-dock-for="${panel.id}"]`);
        if (pill) pill.remove();
    }

    function minimizeToDock(panel) {
        // (4) can't minimize if maximized
        if (panel.dataset.maximized === "true") return;

        panel.dataset.minimized = "true";
        addToDock(panel);
    }

    function restoreFromDock(panel) {
        panel.dataset.minimized = "false";
        removeFromDock(panel);
        // ensure inside bounds
        const c = getCanvasRect();
        const rect = panel.getBoundingClientRect();
        const w = rect.width;
        const h = rect.height;
        const left = clamp(parseFloat(panel.style.left || "12"), 0, c.width - w);
        const top = clamp(parseFloat(panel.style.top || "12"), 0, c.height - h);
        panel.style.left = `${left}px`;
        panel.style.top = `${top}px`;
        canvas.appendChild(panel);
        focusPanel(panel);
    }

    // ----- Panel creation -----
    function createPanel({ title = "Panel", body = "" } = {}) {
        panelCount += 1;
        const id = `panel-${panelCount}`;

        const panel = document.createElement("section");
        panel.className = "panel";
        panel.id = id;

        const c = getCanvasRect();
        const left = snap(24 + (panelCount * 18) % Math.max(1, (c.width - 460)));
        const top = snap(24 + (panelCount * 14) % Math.max(1, (c.height - 320)));
        panel.style.left = `${left}px`;
        panel.style.top = `${top}px`;
        panel.style.zIndex = String(++zTop);
        panel.dataset.minimized = "false";
        panel.dataset.maximized = "false";
        panel.dataset.focused = "false";

        panel.innerHTML = `
            <header class="panel-header" data-drag-handle="true">
              <div class="panel-title">
                <span>${escapeHtml(title)}</span>
                <span class="panel-badge">#${panelCount}</span>
              </div>
              <div class="panel-controls">
                <button class="icon-btn" title="Minimize" data-action="minimize">–</button>
                <button class="icon-btn" title="Maximize" data-action="maximize">□</button>
                <button class="icon-btn" title="Close" data-action="close">×</button>
              </div>
            </header>
            <div class="panel-body">
              <div class="placeholder">
                ${body || "Empty panel. Replace this with Plotly, tables, forms, logs, etc."}
              </div>
            </div>
            <div class="resize-handle" data-resize-handle="true" title="Resize"></div>
          `;

        panel._restore = null;

        // focus
        panel.addEventListener("mousedown", () => focusPanel(panel));

        // double click header: maximize toggle
        panel.querySelector(".panel-header").addEventListener("dblclick", (e) => {
            e.preventDefault();
            toggleMaximize(panel);
        });

        // actions
        panel.addEventListener("click", (e) => {
            const btn = e.target.closest("button[data-action]");
            if (!btn) return;
            const action = btn.dataset.action;

            if (action === "close") {
                removeFromDock(panel);
                panel.remove();
            }

            if (action === "minimize") {
                minimizeToDock(panel);
            }

            if (action === "maximize") {
                toggleMaximize(panel);
            }
        });

        enableDrag(panel);
        enableResize(panel);

        canvas.appendChild(panel);
        focusPanel(panel);
        syncMinimizeDisabled(panel);
        return panel;
    }

    function syncMinimizeDisabled(panel) {
        const minBtn = panel.querySelector('button[data-action="minimize"]');
        const isMax = panel.dataset.maximized === "true";
        minBtn.disabled = isMax; // (4)
        minBtn.title = isMax ? "Cannot minimize while maximized" : "Minimize";
    }

    function toggleMaximize(panel) {
        const isMax = panel.dataset.maximized === "true";

        // if minimized, restore first
        if (panel.dataset.minimized === "true") {
            restoreFromDock(panel);
        }

        if (!isMax) {
            panel._restore = {
                left: panel.style.left,
                top: panel.style.top,
                width: panel.style.width,
                height: panel.style.height
            };
            panel.dataset.maximized = "true";
        } else {
            panel.dataset.maximized = "false";
            if (panel._restore) {
                panel.style.left = panel._restore.left;
                panel.style.top = panel._restore.top;
                panel.style.width = panel._restore.width;
                panel.style.height = panel._restore.height;
            }
        }
        focusPanel(panel);
        syncMinimizeDisabled(panel);
    }

    // ----- Dragging -----
    function enableDrag(panel) {
        const header = panel.querySelector('[data-drag-handle="true"]');
        let dragging = false;
        let startX = 0, startY = 0;
        let startLeft = 0, startTop = 0;

        header.addEventListener("pointerdown", (e) => {
            if (e.target.closest("button")) return;
            if (panel.dataset.maximized === "true") return;
            if (panel.dataset.minimized === "true") return;

            dragging = true;
            focusPanel(panel);
            header.setPointerCapture(e.pointerId);

            const rect = panel.getBoundingClientRect();
            const c = getCanvasRect();

            startX = e.clientX;
            startY = e.clientY;
            startLeft = rect.left - c.left;
            startTop = rect.top - c.top;
            e.preventDefault();
        });

        header.addEventListener("pointermove", (e) => {
            if (!dragging) return;

            const c = getCanvasRect();
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            const rect = panel.getBoundingClientRect();
            const w = rect.width;
            const h = rect.height;

            let left = clamp(startLeft + dx, 0, c.width - w);
            let top = clamp(startTop + dy, 0, c.height - h);

            left = snap(left);
            top = snap(top);

            panel.style.left = `${left}px`;
            panel.style.top = `${top}px`;
        });

        header.addEventListener("pointerup", (e) => {
            dragging = false;
            try { header.releasePointerCapture(e.pointerId); } catch { }
        });
    }

    // ----- Resizing -----
    function enableResize(panel) {
        const handle = panel.querySelector('[data-resize-handle="true"]');
        let resizing = false;
        let startX = 0, startY = 0;
        let startW = 0, startH = 0;
        let startLeft = 0, startTop = 0;

        handle.addEventListener("pointerdown", (e) => {
            if (panel.dataset.maximized === "true") return;
            if (panel.dataset.minimized === "true") return;

            resizing = true;
            focusPanel(panel);
            handle.setPointerCapture(e.pointerId);

            const rect = panel.getBoundingClientRect();
            const c = getCanvasRect();

            startX = e.clientX;
            startY = e.clientY;
            startW = rect.width;
            startH = rect.height;
            startLeft = rect.left - c.left;
            startTop = rect.top - c.top;

            e.preventDefault();
        });

        handle.addEventListener("pointermove", (e) => {
            if (!resizing) return;

            const c = getCanvasRect();
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            const maxW = c.width - startLeft;
            const maxH = c.height - startTop;

            let newW = clamp(startW + dx, 260, maxW);
            let newH = clamp(startH + dy, 160, maxH);

            if (gridSnapMode === "snap") {
                const s = getGridSize();
                newW = Math.max(260, Math.round(newW / s) * s);
                newH = Math.max(160, Math.round(newH / s) * s);
                newW = clamp(newW, 260, maxW);
                newH = clamp(newH, 160, maxH);
            }

            panel.style.width = `${newW}px`;
            panel.style.height = `${newH}px`;
        });

        handle.addEventListener("pointerup", (e) => {
            resizing = false;
            try { handle.releasePointerCapture(e.pointerId); } catch { }
        });
    }

    // ----- Optimize panel locations (replaces "close all") -----
    // (5) "optimize" = smart tiled layout within canvas (not the same as "Grid layout" button, but similar)
    function optimizePanels() {
        const panels = [...canvas.querySelectorAll(".panel")].filter(p => p.dataset.minimized !== "true");
        if (panels.length === 0) return;

        // If someone is maximized, unmaximize it first (otherwise tiling makes no sense)
        for (const p of panels) {
            if (p.dataset.maximized === "true") {
                p.dataset.maximized = "false";
                if (p._restore) {
                    p.style.left = p._restore.left;
                    p.style.top = p._restore.top;
                    p.style.width = p._restore.width;
                    p.style.height = p._restore.height;
                }
                syncMinimizeDisabled(p);
            }
        }

        const c = getCanvasRect();
        const gap = 12;
        const n = panels.length;

        // choose cols/rows to approach aspect ratio
        let cols = Math.ceil(Math.sqrt(n));
        let rows = Math.ceil(n / cols);

        const cellW = Math.floor((c.width - gap * (cols + 1)) / cols);
        const cellH = Math.floor((c.height - gap * (rows + 1)) / rows);

        panels.forEach((p, i) => {
            const r = Math.floor(i / cols);
            const col = i % cols;

            const left = gap + col * (cellW + gap);
            const top = gap + r * (cellH + gap);

            p.style.left = `${snap(left)}px`;
            p.style.top = `${snap(top)}px`;
            p.style.width = `${cellW}px`;
            p.style.height = `${cellH}px`;
            p.style.zIndex = String(++zTop);
        });
    }

    gridSizeSel.addEventListener("change", () => {
        setGridSizeCss();
    });

    // // ----- Buttons -----
    btnNewPanel.addEventListener("click", () => {
        createPanel({
            title: "New test panel",
            body: "Blank workspace panel. Put anything here later."
        });
    });

    btnSpacePanel.addEventListener("click", optimizePanels);

    // Create initial panel
    createPanel({
        title: "Welcome",
        body: "Light mode + resizable sidebar + docked minimization + optimize + grid overlay/snap."
    });

    var acc = document.getElementsByClassName("accordion");
    var i;

    for (i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
                panel.style.borderStyle = "none";
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
                panel.style.borderStyle = "solid";
            }
        });
    }

    const gridModeToggle = document.getElementById("gridModeToggle");

    gridModeToggle.addEventListener("click", function () {
        gridModeToggle.classList.toggle('on');

        const knobElement = gridModeToggle.querySelector(".knob")

        if (knobElement) {
            knobElement.classList.toggle('on');
        }

        gridModeOn = !gridModeOn;
        gridBg.classList.toggle("on", gridModeOn);
    });

    const gridSnapToggle = document.getElementById("gridSnapToggle");

    gridSnapToggle.addEventListener("click", function () {
        gridSnapToggle.classList.toggle('on');

        const knobElement = gridSnapToggle.querySelector(".knob")

        if (knobElement) {
            knobElement.classList.toggle('on');
        }
        gridSnapOn = !gridSnapOn;
        gridSnapMode = gridSnapOn ? "snap" : "none";
    });

})();