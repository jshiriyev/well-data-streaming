import './assets/styles.css';
import 'primeicons/primeicons.css';

import { createApp } from "vue";
import PrimeVue from "primevue/config";
import Aura from '@primevue/themes/aura';
import { createPinia } from "pinia";

import App from "./App.vue";
// import router from "@app/router.js";
// import "@api/config.js";

const app = createApp(App);
app.use(createPinia());
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            prefix: 'p',
            darkModeSelector: 'system',
            cssLayer: {
                name: 'primevue',
                order: 'theme, base, primevue'
            }
        }
    },
})
// app.use(router);
app.mount("#app");
