/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Gris de la première version du site.
        slate: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
          950: '#0b0f19',
        },
        // Identité visuelle du portail (vert de la Maison de l'Économie)
        brand: {
          50: '#f3faea',
          100: '#e3f3d0',
          200: '#c9e8a4',
          300: '#a5d86e',
          400: '#7ec843',
          500: '#6bb133',
          600: '#5da020',
          700: '#4a7a1a',
          800: '#3b6215',
          900: '#2d4a10',
        },
      },
      // Angles quasi droits : un outil interne, pas une application grand public.
      borderRadius: {
        sm: '2px',
        DEFAULT: '3px',
        md: '3px',
        lg: '4px',
        xl: '5px',
        '2xl': '6px',
        '3xl': '8px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
