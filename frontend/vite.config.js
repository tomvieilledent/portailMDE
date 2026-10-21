import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// En développement, l'API et les fichiers envoyés sont proxifiés vers le backend
// (voir VITE_API_PROXY, défini dans docker-compose).
const target = process.env.VITE_API_PROXY ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target, ws: true, changeOrigin: true },
      '/uploads': { target, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    globals: true,
  },
})
