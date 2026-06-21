import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  if (mode === "production" && !env.VITE_API_BASE_URL && mode !== "test") {
    throw new Error(
      "VITE_API_BASE_URL is required for production builds. Copy web/.env.production.example to web/.env.production.",
    );
  }

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./vitest.setup.ts",
      include: ["src/**/*.test.{ts,tsx}"],
    },
  };
});
