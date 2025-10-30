import { test, expect } from '@playwright/test';

test('week selection persistence across navigation', async ({ page }) => {
  // Navigate to home page
  await page.goto('/');

  // Wait for page to load and check we're on dashboard
  await page.waitForURL('**/dashboard');

  // Wait for WeekSelector to be visible
  const selectControl = page.locator('div[class*="MuiFormControl"]').first();
  await selectControl.waitFor({ state: 'visible', timeout: 5000 });

  // Click the select to open dropdown
  const selectButton = selectControl.locator('[role="combobox"]').first();
  await selectButton.click();

  // Wait for menu to open and select Week 9
  const menuItem = page.locator('[role="option"]').filter({ hasText: /Week\s*9/ }).first();
  await menuItem.waitFor({ state: 'visible', timeout: 5000 });
  await menuItem.click();

  // Wait for selection to update
  await page.waitForTimeout(500);

  // Verify Week 9 is now shown in the select
  await expect(selectButton).toContainText('9', { timeout: 5000 });

  // Navigate to /players route
  await page.goto('/players');
  await page.waitForURL('**/players');

  // Verify WeekSelector is still visible
  await selectControl.waitFor({ state: 'visible', timeout: 5000 });

  // Verify Week 9 is still selected
  await expect(selectButton).toContainText('9', { timeout: 5000 });

  // Navigate back to /dashboard route
  await page.goto('/dashboard');
  await page.waitForURL('**/dashboard');

  // Verify WeekSelector still shows Week 9 (persistence check)
  await selectControl.waitFor({ state: 'visible', timeout: 5000 });
  await expect(selectButton).toContainText('9', { timeout: 5000 });
});
