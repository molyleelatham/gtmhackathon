import { test, expect } from "./fixtures";

test("connections list and detail navigation", async ({ page }) => {
  await page.goto("/app/connections");
  await expect(page.getByRole("heading", { name: /Connections/i })).toBeVisible();

  const firstLink = page.locator("a[href*='/app/connections/']").first();
  if (await firstLink.count() > 0) {
    await firstLink.click();
    await expect(page).toHaveURL(/\/app\/connections\//);
  }
});
