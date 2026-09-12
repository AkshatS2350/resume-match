import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function expectNoSeriousAxeViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.filter((violation) => ["serious", "critical"].includes(violation.impact ?? ""))).toEqual([]);
}

test("upload flow is keyboard reachable and has no serious axe violations", async ({ page }) => {
  await page.goto("/");
  const fileInput = page.getByLabel("Resume file");

  await fileInput.focus();
  await expect(fileInput).toBeFocused();
  await expectNoSeriousAxeViolations(page);
});

test("review flow supports keyboard confirmation and has no serious axe violations", async ({ page }) => {
  await page.goto("/review");
  const confirm = page.getByRole("button", { name: "Confirm profile" });

  await confirm.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog", { name: "Empty profile warning" })).toBeVisible();
  await page.getByRole("checkbox", { name: /understand/i }).focus();
  await page.keyboard.press("Space");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveText(/ready to continue/i);
  await expectNoSeriousAxeViolations(page);
});
