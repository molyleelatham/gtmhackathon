import { defineConfig, devices } from "@playwright/test";

const API_URL = "http://127.0.0.1:8000";
const WEB_URL = "http://127.0.0.1:5173";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: WEB_URL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "cd .. && uv run python scripts/e2e_api_server.py",
      url: `${API_URL}/health`,
      reuseExistingServer: false,
      timeout: 120000,
      env: {
        REQUIRE_FIREBASE_AUTH: "false",
        SEED_DEMO_DATA: "true",
        USE_FIRESTORE_STORE: "false",
      },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173 --mode test",
      url: WEB_URL,
      reuseExistingServer: false,
      timeout: 120000,
      env: {
        VITE_API_BASE_URL: API_URL,
        VITE_E2E_BYPASS_AUTH: "true",
      },
    },
  ],
});
