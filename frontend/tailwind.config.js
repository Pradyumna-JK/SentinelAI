/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070b14',
          900: '#0b1220',
          850: '#0f1830',
          800: '#131c2e',
          700: '#1b2740',
          600: '#25334f',
          500: '#334463',
        },
        border: '#25334f',
        safety: {
          orange: '#f97316',
          yellow: '#eab308',
          red: '#ef4444',
          green: '#22c55e',
          blue: '#3b82f6',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        panel: '0 1px 2px 0 rgba(0,0,0,0.4), 0 0 0 1px rgba(37,51,79,0.6)',
        glow: '0 0 0 3px rgba(249,115,22,0.25)',
      },
      borderRadius: {
        xl: '0.875rem',
      },
    },
  },
  plugins: [],
}
