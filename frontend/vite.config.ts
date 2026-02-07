import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// Vite config when running from the `frontend` directory.
// The "@" alias points to `src`, so imports like "@/components/..." work.
export default defineConfig({
  server: {
    host: "::",
    port: 5173,
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

