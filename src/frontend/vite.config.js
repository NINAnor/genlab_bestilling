import { resolve } from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // NOTE: same as STATIC_URL
  base: "/static/",
  build: {
    manifest: "manifest.json",
    // NOTE: django app static folder
    outDir: resolve(__dirname, "static/frontend"),
    rollupOptions: {
      input: {
        samples: resolve(__dirname, 'src/samples/main.jsx')
      }
    }
  }
})
