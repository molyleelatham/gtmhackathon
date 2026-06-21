import { test, expect } from "./fixtures";

test("settings shows ICP section", async ({ page }) => {
  await page.goto("/app/settings");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /ICP/i })).toBeVisible();
});
