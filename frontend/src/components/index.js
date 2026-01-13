export function createElement(tag, { className, text, attrs } = {}) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = String(text);
  if (attrs && typeof attrs === "object") {
    Object.entries(attrs).forEach(([key, value]) => {
      if (value === null || value === undefined) return;
      el.setAttribute(key, String(value));
    });
  }
  return el;
}
