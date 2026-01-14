import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "@app/App.vue";
import router from "@app/router.js";
import "@api/config.js";
import "@styles/shared-vars.css";
import "@styles/shared-base.css";
import "@styles/shared-layout.css";
import "@styles/shared-components.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
