import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,        // écoute sur 0.0.0.0 (accessible hors du conteneur)
    port: 3000,
    strictPort: true,
    open: false,
    // Le navigateur n'a besoin que du port 3000 : les appels /api sont
    // relayés vers le backend en interne (pas de port 8000 à exposer, pas de CORS).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // WebSocket du chat (Socket.IO) relayé vers le backend.
      '/socket.io': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
