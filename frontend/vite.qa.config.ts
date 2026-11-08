import { defineConfig, mergeConfig } from 'vite'
import base from './vite.config'

// Explicit manual QA entry point; the normal config and application stay unchanged.
export default defineConfig(mergeConfig(base, {
  define: { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('http://localhost:8001') },
  server: { host: '127.0.0.1', port: 5175, strictPort: true },
  plugins: [{
    name: 'manual-qa-label',
    transformIndexHtml(html: string) {
      return html.replace('<body>', '<body><aside role="status" style="position:sticky;top:0;z-index:99999;padding:9px;text-align:center;background:#fbbf24;color:#15212e;font:600 13px sans-serif">PRUEBA LOCAL · Datos temporales · No es Atlas · Se borran al reiniciar</aside>')
    },
  }],
}))
