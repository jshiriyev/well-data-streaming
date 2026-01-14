import { onBeforeUnmount, unref, watch } from "vue";

export function useEscapeKey(handler, options = {}) {
  const { enabled } = options;
  let listening = false;

  const isEnabled = () => (enabled === undefined ? true : unref(enabled));

  const onKeyDown = (event) => {
    if (!isEnabled()) return;
    if (event.key !== "Escape") return;
    handler?.(event);
  };

  const attach = () => {
    if (listening || typeof document === "undefined") return;
    document.addEventListener("keydown", onKeyDown);
    listening = true;
  };

  const detach = () => {
    if (!listening || typeof document === "undefined") return;
    document.removeEventListener("keydown", onKeyDown);
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
}
