import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    server: {
      deps: {
        // Vuetify importa CSS de componentes desde node_modules.
        // Inlining hace que Vite procese esos assets durante Vitest
        // en lugar de delegarlos al import nativo de Node.
        inline: [/vuetify/],
      },
    },
  },
})