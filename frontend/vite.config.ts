import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// Vite config when running from the `frontend` directory.
// The "@" alias points to `src`, so imports like "@/components/..." work.
export default defineConfig({
  server: {
    host: "::",
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://quantcai.onrender.com',
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: 'https://quantcai.onrender.com',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'https://quantcai.onrender.com',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  publicDir: "./public",
  build: {
    // Emit production build to the shared root `dist` directory
    outDir: "../dist",
    emptyOutDir: true,
  },
});

