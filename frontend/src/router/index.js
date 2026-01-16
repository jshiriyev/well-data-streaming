import { createRouter, createWebHistory } from "vue-router";
const DatahubView = () => import("./views/DatahubView.vue");
const OnemapView = () => import("./views/OnemapView.vue");
const WorkspaceView = () => import("./views/WorkspaceView.vue");
const NotFoundView = () => import("./views/NotFoundView.vue");

const routes = [
  { path: "/", redirect: "/onemap" },
  { path: "/datahub", component: DatahubView },
  { path: "/onemap", component: OnemapView },
  { path: "/workspace", component: WorkspaceView },
  { path: "/:pathMatch(.*)*", component: NotFoundView },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
