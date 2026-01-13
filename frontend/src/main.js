import "./styles/launcher.css";

const page = document.body?.dataset?.page;
if (page === "launcher") {
    const base = import.meta.env.BASE_URL || "/";
    const isDev = import.meta.env.DEV;
    const launcherLinks = document.querySelectorAll("a[data-app]");

    launcherLinks.forEach((link) => {
        const app = link.getAttribute("data-app");
        if (!app) return;
        if (isDev) {
            link.setAttribute("href", `/src/pages/${app}/`);
        } else {
            link.setAttribute("href", `${base}${app}/`);
        }
    });
}
