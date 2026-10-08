/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        pineapple: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          DEFAULT: '#f59e0b',
        },
        brand: {
          navy: '#0f172a',
          slate: '#334155',
          gold: '#d97706',
          accent: '#0284c7',
        },
        background: {
          light: '#f8fafc',
          dark: '#0f172a',
        },
      },
      boxShadow: {
        'neo-extruded': '8px 8px 16px #cbd5e1, -8px -8px 16px #ffffff',
        'neo-inset': 'inset 8px 8px 16px #cbd5e1, inset -8px -8px 16px #ffffff',
        'neo-pressed': 'inset 4px 4px 8px #cbd5e1, inset -4px -4px 8px #ffffff',
        'neo-dark-extruded': '8px 8px 16px #020617, -8px -8px 16px #1e293b',
        'neo-dark-inset': 'inset 8px 8px 16px #020617, inset -8px -8px 16px #1e293b',
        'neo-dark-pressed': 'inset 4px 4px 8px #020617, inset -4px -4px 8px #1e293b',
      },
    },
  },
  plugins: [],
};