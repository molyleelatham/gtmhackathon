import { test, expect } from "./fixtures";

test("leads page loads", async ({ page }) => {
  await page.goto("/app/leads");
  await expect(page.getByRole("heading", { name: /CRM Leads/i })).toBeVisible();
});
