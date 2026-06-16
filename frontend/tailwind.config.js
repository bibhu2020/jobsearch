const path = require('path')
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    path.join(__dirname, 'index.html'),
    path.join(__dirname, 'src/**/*.{vue,js,ts,jsx,tsx}'),
  ],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#eef2ff', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
