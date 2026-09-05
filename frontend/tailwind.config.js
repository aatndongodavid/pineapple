// frontend/tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pineapple: {
          DEFAULT: '#10B981',
          dark: '#14312a',
          light: '#A7F3D0',
        },
        background: {
          light: '#E0E5EC',
          dark: '#0F172A',
        },
      },
      boxShadow: {
        'neo-extruded': '8px 8px 16px #b8bec7, -8px -8px 16px #ffffff',
        'neo-inset': 'inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff',
        'neo-pressed': 'inset 2px 2px 4px #b8bec7, inset -2px -2px 4px #ffffff',
        'neo-dark-extruded': '8px 8px 16px #0a0f18, -8px -8px 16px #14203a',
        'neo-dark-inset': 'inset 4px 4px 8px #0a0f18, inset -4px -4px 8px #14203a',
        'neo-dark-pressed': 'inset 2px 2px 4px #0a0f18, inset -2px -2px 4px #14203a',
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05))',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};