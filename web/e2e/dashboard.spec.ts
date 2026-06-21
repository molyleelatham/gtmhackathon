import { test, expect } from "./fixtures";

test("dashboard shows stat tiles and navigation", async ({ page }) => {
  await page.goto("/app");
  await expect(page.getByText("Events")).toBeVisible();
  await expect(page.getByText("Connections")).toBeVisible();
  await expect(page.getByRole("link", { name: "Connections" })).toBeVisible();
  await expect(page.getByRole("link", { name: /CRM Leads/i })).toBeVisible();
});
