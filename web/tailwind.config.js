/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        warmth: {
          cold: "#5b8def",
          warm: "#f5a623",
          hot: "#ef5b5b",
        },
        ink: {
          900: "#0d1117",
          800: "#161b22",
          700: "#21262d",
          600: "#30363d",
        },
      },
    },
  },
  plugins: [],
};
