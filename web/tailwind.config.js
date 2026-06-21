/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
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
        cursor: {
          bg: "#ececef",
          surface: "#ffffff",
          ink: "#18181b",
          muted: "#52525b",
          border: "rgba(24, 24, 27, 0.12)",
        },
        zero: {
          black: "#000000",
          yellow: "#f0ff70",
          muted: "#c4c4c4",
          border: "rgba(255,255,255,0.12)",
        },
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
          900: "var(--ink-primary)",
          800: "var(--ink-primary)",
          700: "var(--ink-primary)",
          600: "var(--ink-primary)",
          muted: "var(--ink-secondary)",
          faint: "var(--ink-tertiary)",
        },
      },
      backdropBlur: { glass: "20px" },
      ringColor: {
        subtle: "var(--border-subtle)",
        strong: "var(--border-strong)",
      },
      borderColor: {
        subtle: "var(--border-subtle)",
        strong: "var(--border-strong)",
      },
      backgroundColor: {
        muted: "var(--surface-muted)",
        glass: {
          DEFAULT: "var(--surface-glass)",
          strong: "var(--surface-glass-strong)",
          hover: "var(--surface-glass-hover)",
        },
      },
      boxShadow: {
        glass: "var(--shadow-glass)",
        "glass-lg": "var(--shadow-glass-lg)",
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
