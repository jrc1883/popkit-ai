import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [tailwind()],
  output: 'static',
  // Can be configured via env var or changed later when domain is set up
  site: process.env.SITE_URL || 'https://popkit.thehouseofdeals.com',
});
