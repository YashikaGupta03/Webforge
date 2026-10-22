import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // Rewrite /api/health -> /health (while keeping /api/issues as /api/issues)
        rewrite: (path) => path.replace(/^\/api\/health/, '/health'),
      },
    },
  },
})