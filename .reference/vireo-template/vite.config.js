import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));

/*
 * Vireo — Django edition · asset build only.
 *
 * Django owns templating + routing; Vite owns the Tailwind v4 compile + the
 * Alpine/ApexCharts bundle. The single entry (assets/js/app.js) imports app.css
 * and the verbatim vireo.js runtime. Output lands in static/dist/ with fixed
 * names (vireo.css / vireo.js) + a manifest.json so the Django template can
 * link stable URLs. Run `npm run build` (prod) or `npm run dev` (watch).
 */
export default defineConfig({
  root,
  plugins: [tailwindcss()],
  build: {
    outDir: resolve(root, 'static/dist'),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        // Main bundle → static/dist/vireo.js (+ vireo.css).
        app: resolve(root, 'assets/js/app.js'),
        // Page module for the Leaflet map → static/dist/pages/maps-leaflet.js
        // (loaded by pages/maps/leaflet.html; bare `import L from 'leaflet'`
        //  must go through Vite so leaflet + its CSS resolve).
        'pages/maps-leaflet': resolve(root, 'assets/js/pages/maps-leaflet.js'),
      },
      output: {
        entryFileNames: (chunk) =>
          chunk.name === 'app' ? 'vireo.js' : '[name].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (info) => {
          const name = info.names ? info.names[0] : info.name;
          if (name && name.endsWith('.css')) {
            // Keep the leaflet page CSS separate; main token CSS → vireo.css.
            if (name.includes('leaflet') || name.includes('maps-leaflet')) {
              return 'pages/[name][extname]';
            }
            return 'vireo.css';
          }
          return 'assets/[name][extname]';
        },
      },
    },
  },
});
