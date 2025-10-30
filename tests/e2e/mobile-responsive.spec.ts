import { test, expect, devices } from '@playwright/test';

test('mobile responsive design (iPhone SE)', async ({ page }) => {
  // Set mobile viewport (iPhone SE)
  await page.setViewportSize({ width: 390, height: 844 });

  // Navigate to home page
  await page.goto('/');
  await page.waitForURL('**/dashboard', { timeout: 10000 });

  // Wait for page to load
  await page.waitForTimeout(1000);

  // Verify WeekSelector is visible and accessible on mobile
  const selectControl = page.locator('div[class*="MuiFormControl"]').first();
  await selectControl.waitFor({ state: 'visible', timeout: 5000 });

  // Verify no horizontal scrolling on mobile (page width should match viewport)
  const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const viewportWidth = 390;
  expect(pageWidth).toBeLessThanOrEqual(viewportWidth + 10); // Allow small margin

  // Verify WeekSelector is tappable (has sufficient size)
  const selectorBox = await selectControl.boundingBox();
  expect(selectorBox?.height).toBeGreaterThanOrEqual(40); // Material Design minimum touch target

  // Verify main content is visible
  const mainContent = page.locator('main, [role="main"]');
  await expect(mainContent).toBeVisible({ timeout: 5000 });
});

test('desktop responsive design (1920x1080)', async ({ page }) => {
  // Set desktop viewport
  await page.setViewportSize({ width: 1920, height: 1080 });

  // Navigate to home page
  await page.goto('/');
  await page.waitForURL('**/dashboard', { timeout: 10000 });

  // Wait for page to load
  await page.waitForTimeout(1000);

  // Verify WeekSelector is visible
  const selectControl = page.locator('div[class*="MuiFormControl"]').first();
  await selectControl.waitFor({ state: 'visible', timeout: 5000 });

  // Verify page renders without horizontal scroll at desktop size
  const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const viewportWidth = 1920;
  expect(pageWidth).toBeLessThanOrEqual(viewportWidth + 10);

  // Verify layout adjusts to desktop (main content visible)
  const mainContent = page.locator('main, [role="main"]');
  await expect(mainContent).toBeVisible({ timeout: 5000 });
});

test('tablet responsive design (1024x768)', async ({ page }) => {
  // Set tablet viewport
  await page.setViewportSize({ width: 1024, height: 768 });

  // Navigate to home page
  await page.goto('/');
  await page.waitForURL('**/dashboard', { timeout: 10000 });

  // Wait for page to load
  await page.waitForTimeout(1000);

  // Verify WeekSelector is visible
  const selectControl = page.locator('div[class*="MuiFormControl"]').first();
  await selectControl.waitFor({ state: 'visible', timeout: 5000 });

  // Verify no horizontal scrolling
  const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const viewportWidth = 1024;
  expect(pageWidth).toBeLessThanOrEqual(viewportWidth + 10);

  // Verify main content is visible
  const mainContent = page.locator('main, [role="main"]');
  await expect(mainContent).toBeVisible({ timeout: 5000 });
});
