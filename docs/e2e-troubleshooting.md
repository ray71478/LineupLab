# E2E Testing Troubleshooting Guide

This guide helps diagnose and fix common E2E testing failures in Cortex.

## Quick Diagnostic Checklist

Before diving into troubleshooting, verify:

1. **Backend Running**: `curl http://localhost:8000/api/weeks`
   - Should return 200 with weeks data
   - If fails, start backend: `uvicorn backend.main:app --reload`

2. **Frontend Dev Server Running**: Open `http://localhost:5173` in browser
   - Should see dark mode UI
   - Should see WeekSelector dropdown
   - If fails, start frontend: `cd frontend && npm run dev`

3. **Playwright Installed**: `npx playwright --version`
   - Should show version (e.g., v1.40.0)
   - If not installed: `npm install -D @playwright/test && npx playwright install chromium`

4. **Test Files Exist**: `ls tests/e2e/*.spec.ts`
   - Should list: week-selection.spec.ts, navigation.spec.ts, mobile-responsive.spec.ts
   - If missing, create them per spec

## Common Failure Scenarios

### 1. Timeout Errors

**Error Message:**
```
Error: Timeout 30000ms exceeded waiting for locator to be visible
```

**Root Causes:**
- Backend API not responding
- Frontend not rendering UI
- Selector changed or element not found
- Network latency or slow performance

**Diagnostic Steps:**

1. **Check Backend Health:**
   ```bash
   curl -v http://localhost:8000/api/weeks
   # Should return 200 and JSON array
   ```
   If fails, check backend logs:
   ```bash
   # In backend terminal
   tail -f backend/main.py
   ```

2. **Check Frontend Rendering:**
   ```bash
   # Open in real browser
   open http://localhost:5173
   # Should see dark UI with WeekSelector
   ```

3. **Run Test in Headed Mode:**
   ```bash
   npm run test:e2e:headed
   # Watch browser - see what's NOT rendering
   ```

4. **Add Debug Output:**
   ```typescript
   // In test file, before timeout
   const pageContent = await page.content();
   console.log('Page HTML:', pageContent.substring(0, 500));

   // Or use pause to inspect
   await page.pause();
   ```

**Solutions:**

- Increase timeout for slow networks:
  ```typescript
  await page.goto('/', { timeout: 30000 });
  await selectButton.click({ timeout: 10000 });
  ```

- Wait for network to be idle:
  ```typescript
  await page.waitForLoadState('networkidle');
  ```

- Use more reliable selectors:
  ```typescript
  // Bad: relies on class names that might change
  page.locator('.MuiSelect-root')

  // Good: uses semantic selectors
  page.locator('[role="combobox"]')
  ```

---

### 2. Selector Not Found

**Error Message:**
```
Error: locator.click() failed: No element matches the selector "..."
```

**Root Causes:**
- Component structure changed
- Element rendered in different DOM location
- Element needs wait before clicking
- Selector too specific or too generic

**Diagnostic Steps:**

1. **Debug with Headed Mode:**
   ```bash
   npm run test:e2e:headed
   # Watch to see if element exists but is hidden
   ```

2. **Inspect Element in Browser:**
   ```bash
   open http://localhost:5173
   # Open DevTools
   # Right-click element → Inspect
   # Check element's role, data attributes, classes
   ```

3. **Try Different Selectors:**
   ```typescript
   // Option 1: By role (most reliable)
   page.locator('[role="combobox"]')

   // Option 2: By text
   page.locator('text=Week 9')

   // Option 3: By data-testid (if added to component)
   page.locator('[data-testid="week-selector"]')

   // Option 4: By class (least reliable, changes often)
   page.locator('[class*="MuiSelect"]')
   ```

4. **Check Element Visibility:**
   ```typescript
   const element = page.locator('[role="option"]');
   const isVisible = await element.isVisible();
   const isHidden = await element.isHidden();
   const count = await element.count();
   console.log(`Visible: ${isVisible}, Hidden: ${isHidden}, Count: ${count}`);
   ```

**Solutions:**

- Add explicit waits before clicking:
  ```typescript
  const button = page.locator('[role="combobox"]');
  await button.waitFor({ state: 'visible', timeout: 5000 });
  await button.click();
  ```

- Use page.pause() to inspect:
  ```typescript
  await page.pause(); // Browser pauses, you can inspect
  ```

- Check element count before clicking:
  ```typescript
  const count = await menuItem.count();
  if (count === 0) {
    console.error('Menu item not found!');
  }
  ```

---

### 3. Navigation Failures

**Error Message:**
```
Error: Timeout waiting for page.waitForURL("**/dashboard")
```

**Root Causes:**
- App.tsx routing not working
- Route component not rendering
- Navigation happening slowly
- URL pattern doesn't match

**Diagnostic Steps:**

1. **Check Current URL:**
   ```typescript
   const url = page.url();
   console.log(`Current URL: ${url}`);
   ```

2. **Verify Routes in Browser:**
   ```bash
   open http://localhost:5173/dashboard
   # Should show dashboard content

   open http://localhost:5173/players
   # Should show players content
   ```

3. **Check React Router Setup:**
   ```bash
   # Look at App.tsx
   cat frontend/src/App.tsx | grep -A5 "Routes"
   ```

4. **Test with More Lenient Wait:**
   ```typescript
   // Instead of specific waitForURL
   await page.waitForTimeout(1000);
   const url = page.url();
   expect(url).toContain('dashboard');
   ```

**Solutions:**

- Make URL pattern more flexible:
  ```typescript
  // Too strict
  await page.waitForURL('/dashboard');

  // Better
  await page.waitForURL('**/dashboard');

  // Most flexible
  await page.waitForURL('**/dashboard', { timeout: 10000 });
  ```

- Navigate and wait for content instead:
  ```typescript
  await page.goto('/dashboard');

  // Wait for page to be interactive
  await page.waitForLoadState('domcontentloaded');

  // Wait for content
  await page.locator('h1, h2').first().waitFor({ state: 'visible' });
  ```

---

### 4. Element Size / Touch Target Failures

**Error Message:**
```
AssertionError: expected 20 to be greater than or equal to 44
```

**Root Causes:**
- Material-UI component height too small
- Mobile viewport rendering components at wrong size
- CSS padding/margin too small

**Diagnostic Steps:**

1. **Inspect Element Size:**
   ```bash
   open http://localhost:5173
   # Right-click element → Inspect
   # Check computed size (width x height)
   ```

2. **Check MUI Component Props:**
   ```typescript
   // In WeekSelector.tsx
   // Verify <FormControl> has proper margin
   ```

3. **View in Mobile DevTools:**
   ```bash
   open http://localhost:5173
   # DevTools → Toggle device toolbar (Cmd+Shift+M)
   # Check size on mobile viewport
   ```

**Solutions:**

- Lower touch target threshold:
  ```typescript
  // Current: 44px is Material Design standard
  expect(selectorBox?.height).toBeGreaterThanOrEqual(44);

  // More lenient: 40px
  expect(selectorBox?.height).toBeGreaterThanOrEqual(40);
  ```

- Add explicit size styling to component:
  ```tsx
  <FormControl
    fullWidth
    sx={{ minHeight: 56 }} // Ensure minimum height
  >
  ```

---

### 5. Database Connection Failures

**Error Message:**
```
Error: Could not connect to database at postgresql://...
```

**Root Causes:**
- PostgreSQL container not running
- Wrong connection string
- Credentials incorrect
- Database not initialized

**Diagnostic Steps:**

1. **Check PostgreSQL Status:**
   ```bash
   docker-compose ps
   # Should show cortex-postgres RUNNING
   ```

2. **Test Connection:**
   ```bash
   psql postgresql://cortex:cortex@localhost:5432/cortex
   # Should connect successfully
   # Type \q to quit
   ```

3. **Check Connection String:**
   ```bash
   echo $DATABASE_URL
   # Should output postgresql://cortex:cortex@localhost:5432/cortex
   ```

4. **Check Tables Exist:**
   ```bash
   psql postgresql://cortex:cortex@localhost:5432/cortex
   # \dt
   # Should list tables: weeks, player_pools, etc.
   ```

**Solutions:**

- Start PostgreSQL:
  ```bash
  docker-compose up -d
  docker-compose logs postgres
  ```

- Wait for database to be healthy:
  ```bash
  docker-compose ps
  # Wait for "healthy" status
  ```

- Run migrations:
  ```bash
  alembic upgrade head
  ```

---

### 6. Flaky Tests (Intermittent Failures)

**Symptoms:**
- Test passes sometimes, fails other times
- Different failures each run
- Passes in headed mode, fails in headless

**Root Causes:**
- Race conditions (element appears/disappears)
- Timing-dependent code
- Network latency variable
- State not reset between tests

**Diagnostic Steps:**

1. **Run Test Multiple Times:**
   ```bash
   for i in {1..5}; do npm run test:e2e:headed; done
   # Note which tests fail
   ```

2. **Check for Async/Await Issues:**
   ```bash
   # Look for missing awaits in test code
   grep -n "page\." tests/e2e/*.spec.ts | grep -v "await"
   ```

3. **Review Test Isolation:**
   ```bash
   # Each test should be independent
   # No shared state between tests
   ```

**Solutions:**

- Add explicit waits instead of timeouts:
  ```typescript
  // Bad: relies on timing
  await page.waitForTimeout(1000);

  // Good: waits for actual change
  await page.locator('text=Week 9').waitFor({ state: 'visible' });
  ```

- Use waitForLoadState:
  ```typescript
  await page.waitForLoadState('networkidle');
  ```

- Reset state between tests:
  ```typescript
  test.beforeEach(async ({ page }) => {
    // Clear localStorage
    await page.evaluate(() => localStorage.clear());

    // Navigate to fresh state
    await page.goto('/');
  });
  ```

---

### 7. Screenshot Not Generated

**Problem:**
- Test fails but no screenshot in test-results/

**Root Causes:**
- playwright.config.ts not configured for screenshots
- test-results/ directory permissions issue
- Screenshot generation disabled

**Solutions:**

1. **Verify Config:**
   ```typescript
   // playwright.config.ts should have:
   use: {
     screenshot: 'only-on-failure',
     video: 'retain-on-failure',
   },
   ```

2. **Check Directory Permissions:**
   ```bash
   ls -la test-results/
   chmod 755 test-results/
   ```

3. **Force Report Generation:**
   ```bash
   npm run test:e2e:report
   ```

---

## Performance Troubleshooting

### Tests Running Too Slow

**Cause:** Running all browser projects and tests in series

**Solutions:**

1. **Run Only Chromium:**
   ```typescript
   // playwright.config.ts
   projects: [
     { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
     // Remove Firefox and WebKit for speed
   ],
   ```

2. **Increase Workers:**
   ```bash
   # In CI, set more workers
   CI=false npm run test:e2e  # Uses default workers
   ```

3. **Profile Test:**
   ```bash
   npm run test:e2e -- --reporter=list
   # Shows timing for each test
   ```

---

## Getting Help

### Enable Verbose Logging

```bash
DEBUG=pw:api npm run test:e2e
```

### Use Playwright Inspector

```bash
npm run test:e2e:debug
# Pause test execution and step through
```

### Check Browser Logs

In headed mode, check DevTools Console for errors:

```bash
npm run test:e2e:headed
# Watch console for errors
```

### Report Issues

Include in bug reports:
1. Test output (full error message)
2. Screenshot from test-results/
3. Video from test-results/ (if available)
4. Backend logs
5. Frontend console logs

### Useful Commands

```bash
# Clear test results
rm -rf test-results/ playwright-report/

# View test report
npm run test:e2e:report

# Run with verbose output
npm run test:e2e -- --reporter=list

# Debug specific test
npm run test:e2e -- --debug week-selection.spec.ts

# Update snapshots (if using)
npm run test:e2e -- --update-snapshots
```

---

## CI/CD Specific Issues

### GitHub Actions Failures

**Problem:** Tests pass locally but fail in CI

**Solutions:**

1. Check for hardcoded localhost:
   ```bash
   grep -r "localhost:5173" tests/e2e/
   # Should use process.env.BASE_URL instead
   ```

2. Ensure backends are running:
   ```yaml
   # .github/workflows/test.yml
   services:
     postgres:
       image: postgres:15
     backend:
       # Start uvicorn
   ```

3. Install browsers in CI:
   ```bash
   npm ci
   npx playwright install chromium
   ```

---

## Still Stuck?

If troubleshooting steps don't help:

1. Run in headed mode to see what's happening visually
2. Use `page.pause()` to inspect page state
3. Check browser console for JavaScript errors
4. Review recent changes to components/selectors
5. Ask for help with full error output and screenshots
