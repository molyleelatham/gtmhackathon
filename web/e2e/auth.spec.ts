import { test, expect } from "./fixtures";

test("authenticated user reaches dashboard", async ({ page }) => {
  await page.goto("/app");
  await expect(page.getByText("Events")).toBeVisible();
  await expect(page.getByText("Connections")).toBeVisible();
});
