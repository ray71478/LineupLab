/**
 * E2E Integration Tests for ModeSelector
 *
 * Task Group 8.1: Mode Selector Integration Tests
 *
 * Test coverage:
 * - ModeSelector appears in header across all pages
 * - ModeSelector persists across page navigation
 * - Mode state syncs with data fetching hooks (when implemented)
 * - Layout works responsively on mobile and desktop
 * - ModeSelector remains independent from WeekNavigation
 */

import { test, expect } from '@playwright/test';

test.describe('ModeSelector Integration', () => {
  /**
   * Test 1: ModeSelector appears in app header on all pages
   */
  test('should appear in header on home page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await expect(modeSelector).toBeVisible();
  });

  test('should appear in header on Smart Score page', async ({ page }) => {
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await expect(modeSelector).toBeVisible();
  });

  test('should appear in header on Player Selection page', async ({ page }) => {
    await page.goto('/player-selection');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await expect(modeSelector).toBeVisible();
  });

  test('should appear in header on Lineup Generation page', async ({ page }) => {
    await page.goto('/lineups');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await expect(modeSelector).toBeVisible();
  });

  /**
   * Test 2: ModeSelector persists across page navigation
   */
  test('should persist mode selection when navigating between pages', async ({ page }) => {
    // Start on Smart Score page
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    // Select Showdown mode
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Navigate to Player Selection page
    await page.goto('/player-selection');
    await page.waitForLoadState('networkidle');

    // Verify Showdown is still selected
    const showdownButtonOnNewPage = page.locator('[data-testid="mode-button-showdown"]');
    const isPressed = await showdownButtonOnNewPage.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  test('should persist mode selection when navigating to Lineups page', async ({ page }) => {
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    // Select Showdown mode
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Navigate to Lineups page
    await page.goto('/lineups');
    await page.waitForLoadState('networkidle');

    // Verify Showdown is still selected
    const showdownButtonOnLineups = page.locator('[data-testid="mode-button-showdown"]');
    const isPressed = await showdownButtonOnLineups.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  test('should restore mode from localStorage on page refresh', async ({ page }) => {
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    // Select Showdown mode
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify Showdown is still selected after reload
    const showdownButtonAfterReload = page.locator('[data-testid="mode-button-showdown"]');
    const isPressed = await showdownButtonAfterReload.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  /**
   * Test 3: Mode state accessible throughout application
   */
  test('should maintain mode state across complex navigation flow', async ({ page }) => {
    // Start on home page
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Switch to Showdown
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Navigate through multiple pages
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    let showdownBtn = page.locator('[data-testid="mode-button-showdown"]');
    let isPressed = await showdownBtn.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');

    await page.goto('/player-selection');
    await page.waitForLoadState('networkidle');

    showdownBtn = page.locator('[data-testid="mode-button-showdown"]');
    isPressed = await showdownBtn.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');

    await page.goto('/lineups');
    await page.waitForLoadState('networkidle');

    showdownBtn = page.locator('[data-testid="mode-button-showdown"]');
    isPressed = await showdownBtn.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');

    // Switch back to Main Slate
    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    await mainSlateButton.click();
    await page.waitForTimeout(500);

    // Navigate back and verify Main Slate is selected
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const mainBtn = page.locator('[data-testid="mode-button-main"]');
    isPressed = await mainBtn.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  /**
   * Test 4: Responsive layout with WeekNavigation
   */
  test('should display side-by-side with WeekNavigation on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });

    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    const weekSelector = page.locator('[data-testid="week-selector"]');

    // Both should be visible
    await expect(modeSelector).toBeVisible();
    await expect(weekSelector).toBeVisible();

    // Get bounding boxes to verify side-by-side layout
    const modeSelectorBox = await modeSelector.boundingBox();
    const weekSelectorBox = await weekSelector.boundingBox();

    expect(modeSelectorBox).toBeTruthy();
    expect(weekSelectorBox).toBeTruthy();

    // They should be at similar vertical positions (same row)
    if (modeSelectorBox && weekSelectorBox) {
      const verticalDiff = Math.abs(modeSelectorBox.y - weekSelectorBox.y);
      expect(verticalDiff).toBeLessThan(50); // Should be within 50px vertically
    }
  });

  test('should maintain proper spacing on tablet viewport', async ({ page }) => {
    // Set tablet viewport (iPad)
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await expect(modeSelector).toBeVisible();

    // Verify it fits within viewport
    const box = await modeSelector.boundingBox();
    expect(box).toBeTruthy();
    if (box) {
      expect(box.x + box.width).toBeLessThanOrEqual(768);
    }
  });

  test('should work properly on mobile viewport', async ({ page }) => {
    // Set mobile viewport (iPhone 12)
    await page.setViewportSize({ width: 390, height: 844 });

    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await expect(modeSelector).toBeVisible();

    // Should still be functional on mobile
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    const isPressed = await showdownButton.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  /**
   * Test 5: Independence from WeekNavigation
   */
  test('should function independently from WeekNavigation', async ({ page }) => {
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    // Switch mode without touching week selector
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Verify mode changed
    let isPressed = await showdownButton.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');

    // Switch back
    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    await mainSlateButton.click();
    await page.waitForTimeout(500);

    // Verify mode changed back
    isPressed = await mainSlateButton.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  test('should not affect WeekNavigation when mode changes', async ({ page }) => {
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const weekSelector = page.locator('[data-testid="week-selector"]');

    // Get initial week selection (if visible)
    const initialWeekText = await weekSelector.textContent().catch(() => null);

    // Switch mode
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Verify week selector unchanged
    const newWeekText = await weekSelector.textContent().catch(() => null);

    if (initialWeekText && newWeekText) {
      expect(newWeekText).toBe(initialWeekText);
    }
  });

  /**
   * Test 6: Mode state sync with data fetching (placeholder for future)
   */
  test('should provide mode state for API calls', async ({ page }) => {
    // Setup request interception to verify mode parameter
    let apiRequestMade = false;
    let contestModeParam = null;

    page.on('request', (request) => {
      const url = request.url();
      // Check if this is a player or lineup API call
      if (url.includes('/api/players') || url.includes('/api/lineups')) {
        apiRequestMade = true;
        const urlObj = new URL(url);
        contestModeParam = urlObj.searchParams.get('contest_mode');
      }
    });

    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    // Select Showdown mode
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(500);

    // Note: This test verifies mode state is accessible
    // Actual API integration will be tested in Task Group 9
    // For now, we verify mode state persists correctly
    const isPressed = await showdownButton.getAttribute('aria-pressed');
    expect(isPressed).toBe('true');
  });

  /**
   * Test 7: Header layout consistency
   */
  test('should maintain consistent header layout across pages', async ({ page }) => {
    const pages = ['/', '/smart-score', '/player-selection', '/lineups'];

    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForLoadState('networkidle');

      const modeSelector = page.locator('[data-testid="mode-selector"]');
      await expect(modeSelector).toBeVisible();

      // Verify it's in the header/toolbar area (top of page)
      const box = await modeSelector.boundingBox();
      expect(box).toBeTruthy();
      if (box) {
        expect(box.y).toBeLessThan(150); // Should be in top 150px (header area)
      }
    }
  });

  /**
   * Test 8: Multiple mode switches
   */
  test('should handle multiple mode switches reliably', async ({ page }) => {
    await page.goto('/smart-score');
    await page.waitForLoadState('networkidle');

    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    // Switch multiple times
    for (let i = 0; i < 5; i++) {
      // Switch to Showdown
      await showdownButton.click();
      await page.waitForTimeout(300);

      let isPressed = await showdownButton.getAttribute('aria-pressed');
      expect(isPressed).toBe('true');

      // Switch to Main Slate
      await mainSlateButton.click();
      await page.waitForTimeout(300);

      isPressed = await mainSlateButton.getAttribute('aria-pressed');
      expect(isPressed).toBe('true');
    }

    // Should end on Main Slate
    const finalState = await mainSlateButton.getAttribute('aria-pressed');
    expect(finalState).toBe('true');
  });
});
