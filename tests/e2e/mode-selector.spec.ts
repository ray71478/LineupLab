/**
 * E2E Tests for ModeSelector Component
 *
 * Test coverage:
 * - Component renders with correct default mode
 * - Clicking mode toggles state
 * - Active mode displays visual indicator
 * - Responsive behavior on mobile
 * - Mode persists across page navigation
 * - Keyboard navigation (Tab and Enter)
 * - Screen reader accessibility
 */

import { test, expect } from '@playwright/test';

test.describe('ModeSelector Component', () => {
  /**
   * Test 1: Component renders with correct default mode
   */
  test('should render with "Main Slate" selected by default', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForURL('**/dashboard');

    // Wait for ModeSelector to be visible
    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await modeSelector.waitFor({ state: 'visible', timeout: 5000 });

    // Verify "Main Slate" button exists and is active
    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    await expect(mainSlateButton).toBeVisible();

    // Check that main slate has active styling (orange background)
    const buttonStyles = await mainSlateButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
      };
    });

    // Active button should have orange-ish background (rgb values for #ff6b35 or similar)
    expect(buttonStyles.backgroundColor).toMatch(/rgb\(255|rgba\(255/);
  });

  test('should show both mode options', async ({ page }) => {
    await page.goto('/dashboard');

    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    await expect(mainSlateButton).toBeVisible();
    await expect(showdownButton).toBeVisible();
    await expect(mainSlateButton).toContainText('Main Slate');
    await expect(showdownButton).toContainText('Showdown');
  });

  /**
   * Test 2: Clicking mode toggles state
   */
  test('should toggle to Showdown mode when clicked', async ({ page }) => {
    await page.goto('/dashboard');

    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.waitFor({ state: 'visible' });

    // Click showdown button
    await showdownButton.click();

    // Wait for state update
    await page.waitForTimeout(300);

    // Verify showdown button now has active styling
    const buttonStyles = await showdownButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
      };
    });

    // Active button should have orange background
    expect(buttonStyles.backgroundColor).toMatch(/rgb\(255|rgba\(255/);
  });

  test('should toggle back to Main Slate mode', async ({ page }) => {
    await page.goto('/dashboard');

    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    // First switch to showdown
    await showdownButton.click();
    await page.waitForTimeout(300);

    // Then switch back to main slate
    await mainSlateButton.click();
    await page.waitForTimeout(300);

    // Verify main slate is active again
    const buttonStyles = await mainSlateButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
      };
    });

    expect(buttonStyles.backgroundColor).toMatch(/rgb\(255|rgba\(255/);
  });

  /**
   * Test 3: Active mode displays visual indicator
   */
  test('should show visual indicator for active mode', async ({ page }) => {
    await page.goto('/dashboard');

    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    // Check main slate is visually distinct (active)
    const mainStyles = await mainSlateButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
        color: styles.color,
        fontWeight: styles.fontWeight,
      };
    });

    const showdownStyles = await showdownButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
        color: styles.color,
      };
    });

    // Active button should have different styling than inactive
    expect(mainStyles.backgroundColor).not.toBe(showdownStyles.backgroundColor);
  });

  test('should update visual indicator when mode changes', async ({ page }) => {
    await page.goto('/dashboard');

    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    // Get initial styles
    const initialStyles = await showdownButton.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Click to activate
    await showdownButton.click();
    await page.waitForTimeout(300);

    // Get updated styles
    const activeStyles = await showdownButton.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Styles should be different after activation
    expect(activeStyles).not.toBe(initialStyles);
  });

  /**
   * Test 4: Responsive behavior on mobile
   */
  test('should display correctly on mobile viewport', async ({ page }) => {
    // Set mobile viewport (iPhone 12)
    await page.setViewportSize({ width: 390, height: 844 });

    await page.goto('/dashboard');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await modeSelector.waitFor({ state: 'visible' });

    // Verify both buttons are still visible
    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    await expect(mainSlateButton).toBeVisible();
    await expect(showdownButton).toBeVisible();

    // Verify buttons are stacked or properly sized for mobile
    const selectorBox = await modeSelector.boundingBox();
    expect(selectorBox).toBeTruthy();

    // Width should be reasonable for mobile (not too wide)
    if (selectorBox) {
      expect(selectorBox.width).toBeLessThan(400);
    }
  });

  /**
   * Test 5: Mode persists across page navigation
   */
  test('should persist selected mode across navigation', async ({ page }) => {
    await page.goto('/dashboard');

    // Select showdown mode
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    await showdownButton.click();
    await page.waitForTimeout(300);

    // Navigate to players page
    await page.goto('/players');
    await page.waitForURL('**/players');

    // Wait for mode selector to render
    const modeSelectorOnPlayers = page.locator('[data-testid="mode-selector"]');
    await modeSelectorOnPlayers.waitFor({ state: 'visible', timeout: 5000 });

    // Verify showdown is still active
    const showdownButtonOnPlayers = page.locator('[data-testid="mode-button-showdown"]');
    const buttonStyles = await showdownButtonOnPlayers.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.backgroundColor;
    });

    // Should still have active styling
    expect(buttonStyles).toMatch(/rgb\(255|rgba\(255/);
  });

  /**
   * Test 6: Keyboard navigation
   */
  test('should support Tab key navigation between modes', async ({ page }) => {
    await page.goto('/dashboard');

    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');

    // Focus on main slate button
    await mainSlateButton.focus();

    // Verify it has focus
    const hasFocus = await mainSlateButton.evaluate((el) => el === document.activeElement);
    expect(hasFocus).toBe(true);

    // Press Tab to move to showdown button
    await page.keyboard.press('Tab');

    // Verify showdown button now has focus
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');
    const showdownHasFocus = await showdownButton.evaluate((el) => el === document.activeElement);
    expect(showdownHasFocus).toBe(true);
  });

  test('should support Enter key to select mode', async ({ page }) => {
    await page.goto('/dashboard');

    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    // Focus on showdown button
    await showdownButton.focus();

    // Press Enter to activate
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);

    // Verify showdown is now active
    const buttonStyles = await showdownButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.backgroundColor;
    });

    expect(buttonStyles).toMatch(/rgb\(255|rgba\(255/);
  });

  /**
   * Test 7: Screen reader accessibility
   */
  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/dashboard');

    const modeSelector = page.locator('[data-testid="mode-selector"]');
    await modeSelector.waitFor({ state: 'visible' });

    // Check for ARIA label on container
    const ariaLabel = await modeSelector.getAttribute('aria-label');
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).toContain('mode');

    // Check ARIA attributes on buttons
    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    const mainAriaPressed = await mainSlateButton.getAttribute('aria-pressed');
    const showdownAriaPressed = await showdownButton.getAttribute('aria-pressed');

    // One should be pressed (true), the other not (false)
    expect(mainAriaPressed === 'true' || showdownAriaPressed === 'true').toBe(true);
  });

  test('should announce mode changes to screen readers', async ({ page }) => {
    await page.goto('/dashboard');

    const showdownButton = page.locator('[data-testid="mode-button-showdown"]');

    // Click to change mode
    await showdownButton.click();
    await page.waitForTimeout(300);

    // Check that aria-pressed is updated
    const ariaPressed = await showdownButton.getAttribute('aria-pressed');
    expect(ariaPressed).toBe('true');

    // Check main slate button aria-pressed is now false
    const mainSlateButton = page.locator('[data-testid="mode-button-main"]');
    const mainAriaPressed = await mainSlateButton.getAttribute('aria-pressed');
    expect(mainAriaPressed).toBe('false');
  });
});
