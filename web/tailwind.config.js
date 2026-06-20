/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Space Grotesk", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      colors: {
        ember: "#c2410c",
        flame: "#ea580c",
        orange: { DEFAULT: "#f97316", light: "#fb923c" },
        red: { brand: "#dc2626", warm: "#ef4444" },
        amber: "#f59e0b",
        warmth: {
          hot: "#dc2626",
          warm: "#ea580c",
          cold: "#78716c",
        },
        signal: {
          hiring: "#ea580c",
          funding: "#dc2626",
          intent: "#f97316",
        },
        ink: {
          900: "#160d07",
          800: "#1c1109",
          700: "#2a1a0e",
          600: "#3a2615",
          muted: "#57534e",
          faint: "#a8a29e",
        },
      },
      backdropBlur: { glass: "20px" },
      boxShadow: {
        glass: "0 4px 24px rgba(22, 13, 7, 0.08), inset 0 1px 0 rgba(255,255,255,0.9)",
        "glass-lg": "0 12px 40px rgba(22, 13, 7, 0.12)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "drawer-in": {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(0)" },
        },
        "bar-pulse": {
          "0%, 100%": { transform: "scaleY(0.35)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s ease both",
        "drawer-in": "drawer-in 0.25s cubic-bezier(0.22, 1, 0.36, 1) both",
        "bar-pulse": "bar-pulse 0.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
