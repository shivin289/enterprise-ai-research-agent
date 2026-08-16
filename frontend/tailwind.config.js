/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0f172a',
        paper: '#f8fafc',
        accent: '#2563eb',
        accentSoft: '#dbeafe',
        warn: '#b45309',
        conflict: '#be123c',
      },
    },
  },
  plugins: [],
}
