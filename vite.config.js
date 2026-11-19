import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Frontend calls /api/*; Vite forwards to FastAPI (no CORS setup needed in dev).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true, rewrite: p => p.replace(/^\/api/, '') } },
  },
});
