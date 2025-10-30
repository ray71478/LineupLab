/**
 * Page Object Models for E2E Tests
 *
 * Provides reusable page objects with common selectors and actions.
 * Follows Playwright best practices for test organization.
 */

import { Page, Locator } from '@playwright/test';

/**
 * BasePage - Common functionality for all pages
 */
export class BasePage {
  constructor(protected page: Page) {}

  /**
   * Navigate to a route
   */
  async goto(path: string = '/'): Promise<void> {
    await this.page.goto(path);
  }

  /**
   * Wait for page to load
   */
  async waitForPageLoad(timeout: number = 5000): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Check if page contains text
   */
  async pageContains(text: string): Promise<boolean> {
    const element = this.page.locator(`text=${text}`);
    return element.isVisible();
  }

  /**
   * Get page URL
   */
  async getUrl(): Promise<string> {
    return this.page.url();
  }
}

/**
 * DashboardPage - Dashboard specific selectors and actions
 */
export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to dashboard
   */
  async goto(): Promise<void> {
    await super.goto('/dashboard');
    await this.page.waitForURL('**/dashboard');
  }

  /**
   * Verify dashboard title
   */
  async getPageTitle(): Promise<string> {
    const heading = this.page.locator('h1, h2').filter({ hasText: /dashboard|Dashboard/i });
    return await heading.textContent() || '';
  }

  /**
   * Check if dashboard is displayed
   */
  async isDashboardDisplayed(): Promise<boolean> {
    const heading = this.page.locator('h1, h2').filter({ hasText: /dashboard|Dashboard/i });
    return heading.isVisible({ timeout: 5000 }).catch(() => false);
  }
}

/**
 * PlayersPage - Players page specific selectors and actions
 */
export class PlayersPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to players page
   */
  async goto(): Promise<void> {
    await super.goto('/players');
    await this.page.waitForURL('**/players');
  }

  /**
   * Get page title
   */
  async getPageTitle(): Promise<string> {
    const heading = this.page.locator('h1, h2').filter({ hasText: /player|Players/i });
    return await heading.textContent() || '';
  }

  /**
   * Check if page is displayed
   */
  async isDisplayed(): Promise<boolean> {
    const heading = this.page.locator('h1, h2').filter({ hasText: /player|Players/i });
    return heading.isVisible({ timeout: 5000 }).catch(() => false);
  }
}

/**
 * WeekSelectorComponent - WeekSelector reusable component
 */
export class WeekSelectorComponent {
  private selectControl: Locator;
  private selectButton: Locator;

  constructor(page: Page) {
    this.selectControl = page.locator('div[class*="MuiFormControl"]').first();
    this.selectButton = this.selectControl.locator('[role="combobox"]').first();
  }

  /**
   * Wait for week selector to be visible
   */
  async waitForVisible(timeout: number = 5000): Promise<void> {
    await this.selectControl.waitFor({ state: 'visible', timeout });
  }

  /**
   * Select a specific week
   */
  async selectWeek(week: number, page: Page): Promise<void> {
    await this.selectButton.click();
    const menuItem = page.locator('[role="option"]').filter({ hasText: new RegExp(`Week\\s*${week}`) }).first();
    await menuItem.waitFor({ state: 'visible', timeout: 5000 });
    await menuItem.click();
    await page.waitForTimeout(300);
  }

  /**
   * Get currently selected week
   */
  async getSelectedWeek(): Promise<string> {
    return await this.selectButton.textContent() || '';
  }

  /**
   * Verify week is selected
   */
  async isWeekSelected(week: number): Promise<boolean> {
    const selected = await this.getSelectedWeek();
    return selected.includes(week.toString());
  }
}

/**
 * NavigationComponent - Navigation menu reusable component
 */
export class NavigationComponent {
  constructor(private page: Page) {}

  /**
   * Navigate to a route by clicking menu or direct navigation
   */
  async navigateTo(path: string): Promise<void> {
    await this.page.goto(path);
  }

  /**
   * Get current URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  /**
   * Check if URL matches expected
   */
  async isOnPage(urlPattern: string): Promise<boolean> {
    return this.page.url().includes(urlPattern);
  }
}

/**
 * ResponseCheckComponent - Verify API responses
 */
export class ResponseCheckComponent {
  constructor(private page: Page) {}

  /**
   * Wait for API response with specific pattern
   */
  async waitForApiResponse(urlPattern: string, timeout: number = 10000): Promise<any> {
    const response = await this.page.waitForResponse(
      response => response.url().includes(urlPattern),
      { timeout }
    );
    return response.json();
  }

  /**
   * Check if API response status is success
   */
  async isResponseSuccess(urlPattern: string, timeout: number = 10000): Promise<boolean> {
    const response = await this.page.waitForResponse(
      response => response.url().includes(urlPattern),
      { timeout }
    );
    return response.ok();
  }
}
