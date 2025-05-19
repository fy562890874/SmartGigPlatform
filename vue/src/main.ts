import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './assets/main.css'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(ElementPlus)  // Use Element Plus components and styles

app.mount('#app')