/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Rajdhani', 'sans-serif'],
        mono: ['"Share Tech Mono"', 'monospace'],
      },
      colors: {
        bg: '#050505',
        surface: '#0a0f14',
        surfaceHighlight: '#121820',
        primary: '#00f0ff', // Cyan neon
        secondary: '#ff003c', // Red neon
        tertiary: '#fcee0a', // Yellow neon
        text: '#e0e0e0',
        muted: '#5f6c7b',
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, #1f2937 1px, transparent 1px), linear-gradient(to bottom, #1f2937 1px, transparent 1px)",
        'scanline': "linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.2))",
      },
      boxShadow: {
        'neon-blue': '0 0 5px #00f0ff, 0 0 10px #00f0ff, 0 0 20px rgba(0, 240, 255, 0.5)',
        'neon-red': '0 0 5px #ff003c, 0 0 10px #ff003c, 0 0 20px rgba(255, 0, 60, 0.5)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '0.8', boxShadow: '0 0 5px #00f0ff' },
          '50%': { opacity: '1', boxShadow: '0 0 15px #00f0ff' },
        },
      },
    },
  },
  plugins: [],
}
