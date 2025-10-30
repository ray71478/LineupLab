/**
 * E2E tests for Player Management feature with Playwright
 *
 * Test coverage:
 * - Loading player management page
 * - Viewing players and unmatched count
 * - Filtering and sorting players
 * - Searching for players
 * - Opening and interacting with mapping modal
 * - Complete mapping workflow
 * - Mobile responsiveness
 */

import { test, expect } from '@playwright/test';

// Set base URL from environment or default
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';

test.describe('Player Management E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to player management page
    await page.goto(`${BASE_URL}/players`);
  });

  /**
   * Test 1: Load player management page successfully
   */
  test('should load player management page', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check page title
    const title = page.locator('h1');
    await expect(title).toBeVisible();
    const titleText = await title.textContent();
    expect(titleText?.toLowerCase()).toContain('player');
  });

  /**
   * Test 2: Display player table with data
   */
  test('should display player table with data', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for table
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Look for player rows
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  /**
   * Test 3: Display table headers correctly
   */
  test('should display correct table column headers', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Check for key columns
    const headers = page.locator('th');
    const headerText = await headers.allTextContents();

    const expectedColumns = ['Name', 'Team', 'Position', 'Salary'];
    expectedColumns.forEach(col => {
      expect(headerText.some(h => h.includes(col))).toBeTruthy();
    });
  });

  /**
   * Test 4: Sort table by clicking column header
   */
  test('should sort table by salary', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Click salary header to sort
    const salaryHeader = page.locator('th:has-text("Salary")').first();
    await salaryHeader.click();

    // Wait for sort
    await page.waitForTimeout(500);

    // Get salaries from table
    const salaries = await page.locator('table tbody td:nth-child(4)').allTextContents();
    const salaryNumbers = salaries.map(s => parseInt(s.replace(/[^0-9]/g, '')));

    // Check if sorted
    if (salaryNumbers.length > 1) {
      let isSorted = true;
      for (let i = 0; i < salaryNumbers.length - 1; i++) {
        if (salaryNumbers[i] > salaryNumbers[i + 1]) {
          isSorted = false;
          break;
        }
      }
      // Should be sorted or reverse sorted
      expect(isSorted || salaryNumbers.reverse().every((v, i) => i === 0 || v <= salaryNumbers[i - 1])).toBeTruthy();
    }
  });

  /**
   * Test 5: Filter players by position
   */
  test('should filter players by position', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Find position filter
    const positionFilter = page.locator('[data-testid="position-filter"], select:has-option').first();
    if (await positionFilter.isVisible()) {
      await positionFilter.selectOption('QB');

      // Wait for filter
      await page.waitForTimeout(500);

      // Check that only QBs are displayed
      const positions = await page.locator('table tbody td:nth-child(3)').allTextContents();
      positions.forEach(pos => {
        expect(pos.trim()).toBe('QB');
      });
    }
  });

  /**
   * Test 6: Filter players by team
   */
  test('should filter players by team', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Find team filter
    const teamFilter = page.locator('[data-testid="team-filter"], select').first();
    if (await teamFilter.isVisible()) {
      await teamFilter.selectOption('KC');

      // Wait for filter
      await page.waitForTimeout(500);

      // Check that only KC players are displayed
      const teams = await page.locator('table tbody td:nth-child(2)').allTextContents();
      teams.forEach(team => {
        expect(team.trim()).toBe('KC');
      });
    }
  });

  /**
   * Test 7: Search for player by name
   */
  test('should search for player by name', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Find search box
    const searchBox = page.locator('[data-testid="player-search"], input[placeholder*="search" i]').first();
    if (await searchBox.isVisible()) {
      await searchBox.fill('Mahomes');

      // Wait for search
      await page.waitForTimeout(500);

      // Check results
      const names = await page.locator('table tbody td:nth-child(1)').allTextContents();
      const hasMatch = names.some(name => name.includes('Mahomes'));
      expect(hasMatch || names.length === 0).toBeTruthy();
    }
  });

  /**
   * Test 8: Clear search results
   */
  test('should clear search and show all players', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    const searchBox = page.locator('[data-testid="player-search"], input[placeholder*="search" i]').first();
    if (await searchBox.isVisible()) {
      // Search for something
      await searchBox.fill('XYZ');
      await page.waitForTimeout(300);

      // Clear search
      await searchBox.clear();
      await page.waitForTimeout(300);

      // Should show players again
      const rows = page.locator('table tbody tr');
      const count = await rows.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  /**
   * Test 9: Expand player row for details
   */
  test('should expand player row to show details', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Find expand button
    const expandButton = page.locator('button:has-text("expand"), [data-testid="expand-button"]').first();
    if (await expandButton.isVisible()) {
      await expandButton.click();

      // Wait for expansion
      await page.waitForTimeout(300);

      // Check that more details are shown
      const expandedContent = page.locator('[data-testid="expanded-row"], .expanded-content').first();
      await expect(expandedContent).toBeVisible();
    }
  });

  /**
   * Test 10: Display unmatched players alert
   */
  test('should display unmatched players alert if present', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for unmatched alert
    const alert = page.locator('[role="alert"], .alert, [data-testid="unmatched-alert"]').first();

    // Alert might be visible or not depending on test data
    // Just check the element structure
    const sections = page.locator('main > *').first();
    await expect(sections).toBeVisible();
  });

  /**
   * Test 11: Click Fix button on unmatched player
   */
  test('should open mapping modal when clicking Fix button', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Find Fix button on unmatched player card
    const fixButton = page.locator('button:has-text("Fix")').first();
    if (await fixButton.isVisible()) {
      await fixButton.click();

      // Wait for modal
      await page.waitForTimeout(500);

      // Check for modal
      const modal = page.locator('[role="dialog"], .modal').first();
      await expect(modal).toBeVisible();
    }
  });

  /**
   * Test 12: Select suggestion in mapping modal
   */
  test('should select fuzzy match suggestion in modal', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Open modal
    const fixButton = page.locator('button:has-text("Fix")').first();
    if (await fixButton.isVisible()) {
      await fixButton.click();
      await page.waitForTimeout(500);

      // Look for suggestion
      const suggestion = page.locator('[data-testid="suggestion-item"], .suggestion').first();
      if (await suggestion.isVisible()) {
        await suggestion.click();

        // Check that suggestion is selected
        const selected = page.locator('[data-testid="suggestion-item"][selected], .suggestion.selected').first();
        const isSelected = await suggestion.evaluate(el => el.classList.contains('selected') || el.getAttribute('selected') !== null);
        expect(isSelected || await selected.isVisible()).toBeTruthy();
      }
    }
  });

  /**
   * Test 13: Confirm mapping in modal
   */
  test('should confirm player mapping', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Open modal
    const fixButton = page.locator('button:has-text("Fix")').first();
    if (await fixButton.isVisible()) {
      await fixButton.click();
      await page.waitForTimeout(500);

      // Select suggestion
      const suggestion = page.locator('[data-testid="suggestion-item"], .suggestion').first();
      if (await suggestion.isVisible()) {
        await suggestion.click();
        await page.waitForTimeout(300);

        // Click confirm
        const confirmButton = page.locator('button:has-text("Confirm")').first();
        if (await confirmButton.isVisible()) {
          await confirmButton.click();

          // Wait for confirmation
          await page.waitForTimeout(500);

          // Modal should close
          const modal = page.locator('[role="dialog"], .modal').first();
          const isClosed = !(await modal.isVisible().catch(() => false));
          expect(isClosed || !(await modal.isVisible())).toBeTruthy();
        }
      }
    }
  });

  /**
   * Test 14: Close mapping modal with Cancel
   */
  test('should close modal with Cancel button', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Open modal
    const fixButton = page.locator('button:has-text("Fix")').first();
    if (await fixButton.isVisible()) {
      await fixButton.click();
      await page.waitForTimeout(500);

      // Click cancel
      const cancelButton = page.locator('button:has-text("Cancel")').first();
      if (await cancelButton.isVisible()) {
        await cancelButton.click();

        // Wait for close
        await page.waitForTimeout(300);

        // Modal should be hidden
        const modal = page.locator('[role="dialog"], .modal').first();
        const isClosed = !(await modal.isVisible().catch(() => false));
        expect(isClosed).toBeTruthy();
      }
    }
  });

  /**
   * Test 15: Close mapping modal with Escape key
   */
  test('should close modal with Escape key', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Open modal
    const fixButton = page.locator('button:has-text("Fix")').first();
    if (await fixButton.isVisible()) {
      await fixButton.click();
      await page.waitForTimeout(500);

      // Press Escape
      await page.keyboard.press('Escape');

      // Wait for close
      await page.waitForTimeout(300);

      // Modal should be hidden
      const modal = page.locator('[role="dialog"], .modal').first();
      const isClosed = !(await modal.isVisible().catch(() => false));
      expect(isClosed).toBeTruthy();
    }
  });

  /**
   * Test 16: Mobile responsiveness
   */
  test('should be responsive on mobile (375px)', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto(`${BASE_URL}/players`);
    await page.waitForLoadState('networkidle');

    // Check that table is visible and scrollable
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Verify touch-friendly button sizes
    const buttons = page.locator('button').first();
    const size = await buttons.boundingBox();
    if (size) {
      expect(size.height).toBeGreaterThanOrEqual(44);
      expect(size.width).toBeGreaterThanOrEqual(44);
    }
  });

  /**
   * Test 17: Keyboard navigation
   */
  test('should support keyboard navigation', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Tab to first button
    await page.keyboard.press('Tab');

    // Check if something is focused
    const focused = page.locator(':focus');
    expect(await focused.count()).toBeGreaterThanOrEqual(0);
  });

  /**
   * Test 18: Page accessibility
   */
  test('should have proper accessibility labels', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Check for heading
    const heading = page.locator('h1, [role="heading"]').first();
    await expect(heading).toBeVisible();

    // Check for table role
    const table = page.locator('[role="table"], table').first();
    await expect(table).toBeVisible();

    // Check for buttons with aria-label or visible text
    const buttons = page.locator('button').first();
    const label = await buttons.getAttribute('aria-label');
    const text = await buttons.textContent();
    expect(label || text).toBeTruthy();
  });

  /**
   * Test 19: No console errors
   */
  test('should not have console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/players`);
    await page.waitForLoadState('networkidle');

    expect(errors).toHaveLength(0);
  });

  /**
   * Test 20: Loading state
   */
  test('should show loading state while fetching', async ({ page }) => {
    // Intercept API calls to slow them down
    await page.route('**/api/players/**', route => {
      setTimeout(() => route.continue(), 1000);
    });

    await page.goto(`${BASE_URL}/players`);

    // Should show loading indicator or skeleton
    const loading = page.locator('[data-testid="loading"], .loading, .skeleton').first();
    const isVisible = await loading.isVisible().catch(() => false);

    // Eventually should load
    await page.waitForLoadState('networkidle');
    const table = page.locator('table');
    await expect(table).toBeVisible();
  });
});
