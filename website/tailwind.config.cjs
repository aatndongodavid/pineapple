/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        pineapple: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        brand: {
          navy: '#0f172a',
          slate: '#334155',
          gold: '#d97706',
          accent: '#0284c7',
        }
      }
    },
  },
  plugins: [],
}
