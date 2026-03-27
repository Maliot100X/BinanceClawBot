/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        neon: { green: '#00ff88', blue: '#00d4ff', purple: '#a855f7' },
        dark:  { bg: '#020408', card: '#0a1020' },
      },
      fontFamily: { inter: ['Inter', 'sans-serif'] },
    },
  },
  plugins: [],
}
