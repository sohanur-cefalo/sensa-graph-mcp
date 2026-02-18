import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
  server: {
    port: 3000,
    host: true, // Allow external connections (needed for ngrok)
    allowedHosts: [
      '.ngrok-free.app',
      '.ngrok.io',
      '.ngrok.app',
      'localhost',
    ],
    proxy: {
      // Proxy all API requests to the backend
      '/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/graph': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/tools': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 3000,
    host: true, // Allow external connections (needed for ngrok)
    allowedHosts: [
      '.ngrok-free.app',
      '.ngrok.io',
      '.ngrok.app',
      'localhost',
    ],
    proxy: {
      // Proxy all API requests to the backend
      '/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/graph': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/tools': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    exclude: ['@neo4j-nvl/layout-workers'],
    include: [
      '@neo4j-nvl/layout-workers > cytoscape',
      '@neo4j-nvl/layout-workers > cytoscape-cose-bilkent',
      '@neo4j-nvl/layout-workers > @neo4j-bloom/dagre',
      '@neo4j-nvl/layout-workers > bin-pack',
      '@neo4j-nvl/layout-workers > graphlib',
    ],
    esbuildOptions: {
      target: 'es2020',
    },
  },
});
