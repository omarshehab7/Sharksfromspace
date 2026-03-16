/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./screens/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        // Ocean-inspired palette
        ocean: {
          50: "#E6F4F9",
          100: "#C2E5F1",
          200: "#8ECDE5",
          300: "#5AB5D9",
          400: "#2E9DCD",
          500: "#1482B4",
          600: "#0F6690",
          700: "#0B4D6D",
          800: "#073449",
          900: "#0A1628",
        },
        shark: {
          warn: "#FF6B35",
          danger: "#E63946",
          safe: "#06D6A0",
          info: "#118AB2",
        },
      },
      fontFamily: {
        sans: ["Inter", "System"],
        heading: ["Outfit", "System"],
      },
    },
  },
  plugins: [],
};
