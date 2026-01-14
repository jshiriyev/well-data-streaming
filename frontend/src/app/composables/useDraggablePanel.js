import { onBeforeUnmount, unref, watch } from "vue";

function getFixedContainingBlock(el) {
  let node = el?.parentElement;
  while (node && node !== document.body && node !== document.documentElement) {
    const style = window.getComputedStyle(node);
    const willChange = style.willChange || "";
    if (
      style.transform !== "none" ||
      style.filter !== "none" ||
      style.perspective !== "none" ||
      willChange.includes("transform") ||
      willChange.includes("filter") ||
      willChange.includes("perspective")
    ) {
      return node;
    }
    node = node.parentElement;
  }
  return document.documentElement;
}

function getViewportRect() {
  return {
    width: document.documentElement.clientWidth,
    height: document.documentElement.clientHeight,
  };
}

export function useDraggablePanel(panelRef, options = {}) {
  const {
    enabled,
    onPositionChange,
    position,
    ignoreSelector = "input, select, textarea, button, label",
  } = options;

  let dragging = false;
  let offsetX = 0;
  let offsetY = 0;
  let current = null;
  let moveHandler = null;
  let upHandler = null;

  const isEnabled = () => (enabled === undefined ? true : unref(enabled));

  const applyPosition = (pos) => {
    const panel = unref(panelRef);
    if (!panel || !pos) return;
    const { width, height } = getViewportRect();
    const bounds = panel.getBoundingClientRect();
    const container = getFixedContainingBlock(panel);
    const containerRect =
      container === document.documentElement
        ? { left: 0, top: 0 }
        : container.getBoundingClientRect();
    const maxX = width - bounds.width;
    const maxY = height - bounds.height;
    const clampedX = Math.min(Math.max(pos.x, 0), maxX);
    const clampedY = Math.min(Math.max(pos.y, 0), maxY);
    panel.style.left = `${clampedX - containerRect.left}px`;
    panel.style.top = `${clampedY - containerRect.top}px`;
    panel.style.position = "fixed";
    current = { x: clampedX, y: clampedY };
  };

  const handleDragStart = (event) => {
    if (!isEnabled()) return;
    if (event.button !== 0) return;
    const panel = unref(panelRef);
    if (!panel) return;
    if (event.target?.closest(ignoreSelector)) return;

    dragging = true;
    const rect = panel.getBoundingClientRect();
    offsetX = event.clientX - rect.left;
    offsetY = event.clientY - rect.top;
    panel.style.transition = "none";

    moveHandler = (evt) => {
      if (!dragging) return;
      const x = evt.clientX - offsetX;
      const y = evt.clientY - offsetY;
      applyPosition({ x, y });
    };

    upHandler = () => {
      dragging = false;
      panel.style.transition = "";
      if (moveHandler) {
        document.removeEventListener("mousemove", moveHandler);
        moveHandler = null;
      }
      if (upHandler) {
        document.removeEventListener("mouseup", upHandler);
        upHandler = null;
      }
      if (current) {
        if (position) {
          position.value = { ...current };
        }
        onPositionChange?.({ ...current });
      }
    };

    document.addEventListener("mousemove", moveHandler);
    document.addEventListener("mouseup", upHandler);
  };

  const attach = (panel) => {
    if (!panel?.addEventListener) return;
    panel.addEventListener("mousedown", handleDragStart);
  };

  const detach = (panel) => {
    if (!panel?.removeEventListener) return;
    panel.removeEventListener("mousedown", handleDragStart);
  };

  watch(
    () => unref(panelRef),
    (panel, prev) => {
      if (prev) detach(prev);
      if (panel) attach(panel);
    },
    { immediate: true }
  );

  onBeforeUnmount(() => {
    const panel = unref(panelRef);
    detach(panel);
    if (moveHandler) document.removeEventListener("mousemove", moveHandler);
    if (upHandler) document.removeEventListener("mouseup", upHandler);
  });

  return {
    applyPosition,
  };
}
