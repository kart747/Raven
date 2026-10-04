import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  },
  build: {
    // Tabs and profile windows are lazy-loaded; the remaining main chunk is mostly recharts + leaflet,
    // which the dashboard needs on first paint.
    chunkSizeWarningLimit: 850,
  },
})
