import { createRouter, createWebHistory } from "vue-router";
const WorkspacesView = () => import("./pages/WorkspacesView.vue");
const NotFoundView = () => import("./pages/NotFoundView.vue");

const routes = [
  { path: "/", redirect: "/workspaces" },
  { path: "/workspaces", component: WorkspacesView },
  { path: "/:pathMatch(.*)*", component: NotFoundView },
];

const runtimeBase =
  typeof window !== "undefined" && window.location.pathname.startsWith("/app/")
    ? "/app/"
    : import.meta.env.BASE_URL;

const router = createRouter({
  history: createWebHistory(runtimeBase),
  routes,
});

export default router;
