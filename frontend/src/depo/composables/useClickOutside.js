import { onBeforeUnmount, unref, watch } from "vue";

export function useClickOutside(targetRef, handler, options = {}) {
  const { enabled, ignore = [] } = options;
  let listening = false;

  const isEnabled = () => (enabled === undefined ? true : unref(enabled));

  const getIgnoreElements = () =>
    (Array.isArray(ignore) ? ignore : [ignore])
      .map((item) => unref(item))
      .filter(Boolean);

  const handlePointer = (event) => {
    if (!isEnabled()) return;
    const target = unref(targetRef);
    if (!target) return;
    const eventTarget = event.target;
    if (!eventTarget) return;

    if (target === eventTarget || target.contains(eventTarget)) {
      return;
    }

    const ignoreElements = getIgnoreElements();
    if (ignoreElements.some((el) => el === eventTarget || el.contains(eventTarget))) {
      return;
    }

    handler?.(event);
  };

  const attach = () => {
    if (listening || typeof document === "undefined") return;
    document.addEventListener("pointerdown", handlePointer);
    listening = true;
  };

  const detach = () => {
    if (!listening || typeof document === "undefined") return;
    document.removeEventListener("pointerdown", handlePointer);
    listening = false;
  };

  watch(
    () => isEnabled(),
    (value) => {
      if (value) {
        attach();
      } else {
        detach();
      }
    },
    { immediate: true }
  );

  onBeforeUnmount(() => {
    detach();
  });

  return {
    detach,
  };
}
