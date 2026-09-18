import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import './styles/main.css'

import App from './App.vue'
import { vuetify } from './plugins/vuetify'

createApp(App).use(createPinia()).use(vuetify).mount('#app')