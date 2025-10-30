import { test, expect } from '@playwright/test';

test('navigation between all routes works correctly', async ({ page }) => {
  // Navigate to root and verify redirect to dashboard
  await page.goto('/');
  await page.waitForURL('**/dashboard', { timeout: 10000 });

  // Verify dashboard page content
  const dashboardHeading = page.locator('h1, h2').filter({ hasText: /dashboard|Dashboard/i });
  await expect(dashboardHeading).toBeVisible({ timeout: 5000 });

  // Navigate to /players route
  await page.goto('/players');
  await page.waitForURL('**/players', { timeout: 10000 });

  // Verify players page renders
  const playersHeading = page.locator('h1, h2').filter({ hasText: /player|Players/i });
  await expect(playersHeading).toBeVisible({ timeout: 5000 });

  // Navigate to /smart-score
  await page.goto('/smart-score');
  await page.waitForURL('**/smart-score', { timeout: 10000 });

  // Verify smart score page renders
  const smartScoreHeading = page.locator('h1, h2').filter({ hasText: /smart\s*score|SmartScore/i });
  await expect(smartScoreHeading).toBeVisible({ timeout: 5000 });

  // Navigate to /lineups
  await page.goto('/lineups');
  await page.waitForURL('**/lineups', { timeout: 10000 });

  // Verify lineups page renders
  const lineupsHeading = page.locator('h1, h2').filter({ hasText: /lineup|Lineups/i });
  await expect(lineupsHeading).toBeVisible({ timeout: 5000 });

  // Navigate to invalid route /nonexistent
  await page.goto('/nonexistent');

  // Verify 404 page renders (look for "Not Found" or similar message)
  const notFoundText = page.locator('body').filter({ hasText: /not found|404|nonexistent|doesn't exist/i });
  await expect(notFoundText).toBeVisible({ timeout: 5000 });
});
