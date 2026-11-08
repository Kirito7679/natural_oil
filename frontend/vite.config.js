import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: false,
    // Boshqa kompyuter/telefondan kirish: lokal tarmoq (host: true) va
    // ONLAYN_HAVOLA.bat orqali ochiladigan vaqtinchalik internet havolasi (*.trycloudflare.com)
    host: true,
    allowedHosts: ['.trycloudflare.com', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${process.env.BACKEND_PORT || 8010}`,
        changeOrigin: true,
      },
    },
  },
})
