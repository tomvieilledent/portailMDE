/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Identité visuelle du portail (vert de la Maison de l'Économie)
        brand: {
          50: '#f4faea',
          100: '#e4f3d1',
          200: '#cbe8a6',
          300: '#a8d672',
          400: '#7ec843',
          500: '#5da020',
          600: '#4f861b',
          700: '#3f6b16',
          800: '#315512',
          900: '#233d0d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
