# E2E Testing Guide

This guide covers how to run end-to-end tests for the Cortex DFS Lineup Optimizer using Playwright.

## Prerequisites

- Node.js 18+ installed
- Playwright and browsers installed: `npm install -D @playwright/test` and `npx playwright install chromium`
- Backend API running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:5173` (or configure BASE_URL)

## Running E2E Tests

### Run All E2E Tests

Execute all tests in headless mode (CI/CD compatible):

```bash
npm run test:e2e
```

This runs all tests in `tests/e2e/*.spec.ts` using Chromium, Firefox, and WebKit browsers.

### Run Tests in Headed Mode

See the browser window while tests execute (useful for debugging):

```bash
npm run test:e2e:headed
```

This runs tests with the browser UI visible so you can see interactions and debugging.

### Debug Tests Interactively

Use Playwright Inspector to step through test execution:

```bash
npm run test:e2e:debug
```

This launches the Playwright Inspector where you can:
- Step through test execution line by line
- Pause on specific lines
- View element selectors and interactions
- Inspect page state

### View Test Report

After running tests, generate and view HTML report:

```bash
npm run test:e2e:report
```

This opens an interactive HTML report showing:
- Test pass/fail status
- Screenshots on failure
- Video recordings on failure
- Test duration

### Run Specific Test File

Execute only one test file:

```bash
npm run test:e2e -- week-selection.spec.ts
```

Or with pattern matching:

```bash
npm run test:e2e -- --grep "week selection"
```

### Run Tests Against Different BASE_URL

Override the base URL to test against different environments:

```bash
# Local development (default)
BASE_URL=http://localhost:5173 npm run test:e2e

# Staging environment
BASE_URL=https://staging.cortex.app npm run test:e2e

# Production environment
BASE_URL=https://cortex.app npm run test:e2e
```

## Test Scenarios

The E2E test suite includes the following focused tests:

### 1. Week Selection Persistence (`week-selection.spec.ts`)

Verifies that selected week persists across page navigation.

**Test Steps:**
1. Navigate to dashboard
2. Open WeekSelector dropdown
3. Select Week 9
4. Navigate to /players page
5. Verify Week 9 still selected
6. Navigate back to /dashboard
7. Verify Week 9 persistence (Zustand state)

**Expected Result:** Selected week remains consistent across page navigation

### 2. Navigation Flow (`navigation.spec.ts`)

Verifies that all routes are accessible and render correctly.

**Test Steps:**
1. Navigate to root (/) and verify redirect to /dashboard
2. Verify dashboard page renders
3. Navigate to /players and verify page renders
4. Navigate to /smart-score and verify page renders
5. Navigate to /lineups and verify page renders
6. Navigate to invalid route /nonexistent
7. Verify 404 page renders

**Expected Result:** All routes accessible, invalid routes show 404 page

### 3. Responsive Design (`mobile-responsive.spec.ts`)

Verifies UI renders correctly at different viewport sizes.

**Test Viewports:**
- Mobile: 390x844 (iPhone SE) - primary target
- Tablet: 1024x768 - secondary target
- Desktop: 1920x1080 - tertiary target

**Test Checks:**
- No horizontal scrolling at any viewport
- WeekSelector visible and accessible
- Main content visible and readable
- Touch targets sized appropriately (>40px height)

**Expected Result:** UI responsive and accessible at all viewport sizes

## Test Fixtures and Helpers

### Sample Data Files

The E2E tests can use sample XLSX files from the backend's `tests/conftest.py`:

- **LineStar**: 153 players with projections and ownership
- **DraftKings**: 174 players with salary and projections
- **Comprehensive Stats**: 2690 player-week stats entries

These fixtures are available in Python's `tests/conftest.py` and can be generated for E2E tests as needed.

### Database Helpers

For advanced E2E tests, you can query the database to verify imports:

```python
# Python script to verify import in database
import psycopg2
conn = psycopg2.connect("postgresql://cortex:cortex@localhost:5432/cortex")
cur = conn.cursor()

# Query player count after import
cur.execute("SELECT COUNT(*) FROM player_pools WHERE week_id = 1 AND source = 'LineStar'")
count = cur.fetchone()[0]
print(f"Players imported: {count}")
```

### Page Object Patterns

For organizing selectors and actions, use Playwright's page object pattern:

```typescript
// utils/page-objects/WeekSelector.ts
export class WeekSelectorPage {
  constructor(private page: Page) {}

  async selectWeek(week: number): Promise<void> {
    const selectButton = this.page.locator('[role="combobox"]').first();
    await selectButton.click();

    const menuItem = this.page.locator('[role="option"]').filter({ hasText: new RegExp(`Week\\s*${week}`) });
    await menuItem.click();
  }

  async getSelectedWeek(): Promise<string> {
    const selectButton = this.page.locator('[role="combobox"]').first();
    return await selectButton.textContent();
  }
}

// Usage in test
import { WeekSelectorPage } from './utils/page-objects/WeekSelector';

test('week selection', async ({ page }) => {
  const weekSelector = new WeekSelectorPage(page);
  await weekSelector.selectWeek(9);
  const selected = await weekSelector.getSelectedWeek();
  expect(selected).toContain('9');
});
```

## CI/CD Integration

### Running Tests in CI/CD Pipeline

The E2E tests are designed to run in headless mode for CI/CD compatibility:

```bash
# In GitHub Actions, GitLab CI, etc.
npm run test:e2e  # Automatically runs in headless mode
```

### Environment Variables for CI/CD

Configure these environment variables in your CI/CD system:

```bash
# Required
BASE_URL=http://localhost:5173  # or your staging/production URL
DATABASE_URL=postgresql://user:pass@localhost:5432/cortex  # for database verification

# Optional
CI=true  # Enables extra retries and stricter timeout behavior
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=false  # Ensure browsers are installed
```

### Test Artifacts

After test execution, the following artifacts are generated:

- **test-results/** - Test result JSON
- **blob-report/** - Shared report data
- **playwright-report/** - HTML report (open with `npm run test:e2e:report`)

Configure CI/CD to upload these artifacts for analysis.

## Troubleshooting

### Common Failures

#### Timeout Errors

```
Error: Timeout 30000ms exceeded
```

**Causes:**
- Backend API not running (`npm run dev` on backend)
- Frontend dev server not running (`npm run dev` on frontend)
- Selectors changed or element not found

**Solutions:**
1. Verify backend: `curl http://localhost:8000/api/weeks`
2. Verify frontend: Open `http://localhost:5173` in browser
3. Run test in headed mode: `npm run test:e2e:headed`
4. Check browser console for errors

#### Selector Not Found

```
Error: locator.click() failed: No element matches the selector
```

**Causes:**
- Component structure changed
- Element not rendered yet
- Wrong selector used

**Solutions:**
1. Run with headed mode to see what's rendering
2. Use `page.pause()` to stop execution and inspect
3. Check Material-UI version for breaking changes

#### Database Connection Errors

For tests that verify database state:

```
Error: Could not connect to database
```

**Solutions:**
1. Verify PostgreSQL running: `docker-compose ps`
2. Check connection string: `echo $DATABASE_URL`
3. Verify credentials match: `psql postgresql://cortex:cortex@localhost:5432/cortex`

### Reading Test Output

Test output shows:
- Test name and status (PASSED/FAILED)
- Duration in milliseconds
- Assertion failures with expected vs actual
- Browser console messages
- Screenshot path if available

Example:
```
 week-selection.spec.ts (3 tests) 2.1s
   ✓ week selection persistence across navigation (1.2s)
   ✓ navigation between all routes works correctly (0.5s)
   ✓ mobile responsive design (iPhone SE) (0.4s)

 3 tests passed (3)
```

### Using Screenshots for Debugging

When a test fails, Playwright captures a screenshot:

```
1. Open test results: npm run test:e2e:report
2. Click failed test
3. View screenshot showing exact failure point
4. Check what element was/wasn't found
5. Update selector or add waits as needed
```

### Using Videos for Debugging

Video recordings help understand test flow:

```
1. Videos saved to: test-results/
2. Open in any video player
3. Watch test execution step by step
4. Identify exact point of failure
```

## Best Practices

1. **Wait Explicitly**: Always use `waitFor()` instead of relying on `waitForTimeout()`
2. **Use Semantic Selectors**: Prefer `[role="..."]` and `data-testid` over class names
3. **Handle Async**: Use `async/await` properly and wait for navigation
4. **Keep Tests Focused**: Each test should verify one workflow
5. **Use Page Objects**: Organize selectors in reusable page object classes
6. **Clean Database**: Reset database between test runs if needed
7. **Limit Browser Projects**: Use Chromium primarily, add Firefox/WebKit for critical paths
8. **Screenshot on Failure**: Always enabled for quick debugging

## Further Reading

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Selectors](https://playwright.dev/docs/locators)
- [Material-UI Testing](https://mui.com/material-ui/guides/testing/)
- [React Testing Best Practices](https://react.dev/learn#testing)
