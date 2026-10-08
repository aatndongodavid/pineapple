import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://pineapple.cm',
  integrations: [tailwind()],
  build: {
    format: 'directory'
  }
});
