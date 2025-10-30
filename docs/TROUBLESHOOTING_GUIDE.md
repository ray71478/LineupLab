# Troubleshooting Guide - Week Management Feature

**Version:** 1.0
**Last Updated:** October 28, 2025
**Status:** Complete and Production Ready

---

## Table of Contents

1. [Common Issues & Solutions](#common-issues--solutions)
2. [Debug Logging Setup](#debug-logging-setup)
3. [Performance Troubleshooting](#performance-troubleshooting)
4. [Mobile-Specific Issues](#mobile-specific-issues)
5. [Database Issues](#database-issues)
6. [API Issues](#api-issues)
7. [Frontend Issues](#frontend-issues)
8. [Diagnostic Tools](#diagnostic-tools)

---

## Common Issues & Solutions

### Issue 1: "Week not found" Error (404)

**Symptoms:**
- API returns 404 when trying to get week
- Frontend shows "Week not found" message
- Error: `Week {id} not found`

**Root Causes:**
- Week ID is invalid
- Week wasn't created for year
- Database query error

**Solutions:**

1. **Verify week exists:**
   ```bash
   # Check database
   psql -U cortex -d cortex_prod -c "SELECT * FROM weeks WHERE id = 5;"

   # If empty, create weeks for year
   curl -X POST "http://localhost:8000/api/weeks/generate" \
     -H "Content-Type: application/json" \
     -d '{"year": 2025, "force_regenerate": false}'
   ```

2. **Check week creation:**
   ```bash
   # Get weeks for year
   curl -X GET "http://localhost:8000/api/weeks?year=2025"

   # Verify 18 weeks returned
   ```

3. **Verify NFL schedule seeded:**
   ```bash
   psql -U cortex -d cortex_prod -c "SELECT COUNT(*) FROM nfl_schedule WHERE season = 2025;"

   # Should return 18
   ```

4. **Check for migration errors:**
   ```bash
   alembic history
   alembic current

   # If missing, run: alembic upgrade head
   ```

---

### Issue 2: "Week is locked" Error (409)

**Symptoms:**
- Can't update locked week
- Error: `Week {week_number} is locked...`
- Status code: 409 Conflict

**Root Causes:**
- Week has imported data
- This is by design (data immutability)

**Solutions:**

1. **Verify lock is intentional:**
   ```bash
   # Check if week has imported data
   curl -X GET "http://localhost:8000/api/weeks/5/metadata"

   # Look for: "import_status": "imported"
   ```

2. **If lock was accidental:**
   - Contact database admin
   - Must manually update: `UPDATE weeks SET is_locked = false WHERE id = 5;`
   - Verify no data integrity issues before unlocking

3. **For testing/development:**
   ```bash
   # Use force_regenerate to reset weeks
   curl -X POST "http://localhost:8000/api/weeks/generate" \
     -H "Content-Type: application/json" \
     -d '{"year": 2025, "force_regenerate": true}'
   ```

---

### Issue 3: "Invalid year" Error (400)

**Symptoms:**
- API returns 400 for valid-looking year
- Error: `Year {year} is invalid...`
- Message suggests year must be between 2025-2030

**Root Causes:**
- Year outside allowed range (2025-2030)
- Type mismatch (string instead of number)

**Solutions:**

1. **Verify year format:**
   ```bash
   # Correct - year as number
   curl "http://localhost:8000/api/weeks?year=2025"

   # Wrong - year as string
   curl "http://localhost:8000/api/weeks?year='2025'"
   ```

2. **Check supported years:**
   ```bash
   # Add more years to configuration
   # File: backend/routers/week_router.py
   # Change: if not (2025 <= year <= 2030):
   # To: if not (2025 <= year <= 2035):

   # Then seed NFL schedule for new years
   ```

3. **Verify database has year:**
   ```bash
   psql -U cortex -d cortex_prod -c "SELECT DISTINCT season FROM nfl_schedule ORDER BY season;"
   ```

---

### Issue 4: Dropdown Not Opening (Frontend)

**Symptoms:**
- WeekSelector dropdown doesn't open on click
- "No weeks available" message
- Dropdown appears empty

**Root Causes:**
- Weeks not loaded in Zustand store
- API failed to fetch weeks
- Network error

**Solutions:**

1. **Check browser console:**
   ```javascript
   // Open DevTools (F12)
   // Look for errors like:
   // - "Failed to fetch weeks"
   // - "Cannot read property 'weeks' of undefined"
   // - Network errors
   ```

2. **Verify Zustand store:**
   ```javascript
   // In browser console
   import { useWeekStore } from '@/store/weekStore';

   const state = useWeekStore.getState();
   console.log(state.weeks);      // Should show array of weeks
   console.log(state.currentYear); // Should show current year
   console.log(state.error);       // Check for error message
   ```

3. **Check API connectivity:**
   ```bash
   # From browser, open Network tab (F12)
   # Go to Cortex app
   # Look for GET /api/weeks?year=2025
   # Check response status and body
   ```

4. **Enable debug logging:**
   ```javascript
   // Add to component
   useEffect(() => {
     const { weeks, isLoading, error } = useWeekStore();
     console.log('Weeks:', weeks);
     console.log('Loading:', isLoading);
     console.log('Error:', error);
   }, []);
   ```

---

### Issue 5: Carousel Not Swiping (Mobile)

**Symptoms:**
- Carousel doesn't respond to swipe
- Can't navigate between weeks
- Tap to open modal works, but swipe doesn't

**Root Causes:**
- Touch event handling disabled
- React-swipeable not mounted
- CSS preventing pointer events

**Solutions:**

1. **Verify touch events enabled:**
   ```typescript
   // In WeekCarousel.tsx
   const swipeHandlers = useSwipeable({
     onSwipedLeft: () => handleSwipe(-1),
     onSwipedRight: () => handleSwipe(1),
     preventDefaultTouchMove: false,  // Important!
     trackTouch: true,                // Important!
   });
   ```

2. **Check CSS for pointer-events:**
   ```css
   /* Should NOT be: pointer-events: none; */
   /* Should be: pointer-events: auto; */
   .week-carousel {
     pointer-events: auto;  /* Allow touch */
     touch-action: pan-y;   /* Allow swipe */
   }
   ```

3. **Test on actual mobile device:**
   ```bash
   # Desktop browser might not trigger touch events
   # Use Chrome DevTools mobile emulation:
   # F12 -> Toggle device toolbar -> Select mobile device

   # Or test on real device
   # Note: Localhost won't work, use ngrok:
   ngrok http 5173
   # Access from mobile via: https://random.ngrok.io
   ```

4. **Debug swipe handlers:**
   ```typescript
   const swipeHandlers = useSwipeable({
     onSwiping: (e) => console.log('Swiping...', e),
     onSwipedLeft: () => {
       console.log('Swiped left');
       handleSwipe(-1);
     },
   });
   ```

---

### Issue 6: Status Badge Not Updating (Frontend)

**Symptoms:**
- Status badge shows old status after week changes
- Glow effect not moving to new week
- Import status doesn't update after import

**Root Causes:**
- Component not re-rendering
- Zustand store not updating
- Query cache stale

**Solutions:**

1. **Force re-render:**
   ```typescript
   // Clear query cache after import
   queryClient.invalidateQueries(['weeks', currentYear]);
   queryClient.invalidateQueries(['current-week']);
   ```

2. **Check store updates:**
   ```javascript
   // In browser console
   const unsubscribe = useWeekStore.subscribe(
     (state) => console.log('Store updated:', state)
   );

   // Perform action that should update store
   // Watch console output
   ```

3. **Verify component memoization:**
   ```typescript
   // May need to remove React.memo if causing issues
   // export const WeekStatusBadge = React.memo((props) => ...)

   // Or add custom comparison:
   export const WeekStatusBadge = React.memo(
     (props) => { ... },
     (prev, next) => {
       // Custom comparison logic
       return prev.status === next.status &&
              prev.importStatus === next.importStatus;
     }
   );
   ```

4. **Clear browser cache:**
   ```bash
   # DevTools -> Application -> Clear Site Data
   # Or in code:
   useEffect(() => {
     localStorage.clear();
     sessionStorage.clear();
   }, []);
   ```

---

## Debug Logging Setup

### Backend Debug Logging

**Enable SQL Logging:**

```python
# In backend/main.py
from sqlalchemy import create_engine, event

# Create engine with echo=True to log all SQL
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL queries
    pool_size=10,
)

# OR use event listeners for more control
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    logger.debug(f"SQL: {statement}")
    logger.debug(f"Parameters: {parameters}")
```

**Enable Request Logging:**

```python
# In backend/main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "status_code": response.status_code,
            "duration": f"{duration:.3f}s",
        }
    )
    return response
```

**Environment Variable:**

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or in .env
LOG_LEVEL=DEBUG
```

### Frontend Debug Logging

**Enable Console Logging:**

```typescript
// In main.tsx or App.tsx
// Enable detailed logging
const enableDebugLogging = process.env.NODE_ENV === 'development';

if (enableDebugLogging) {
  // Override console methods
  const originalLog = console.log;
  console.log = function(...args) {
    originalLog(`[${new Date().toISOString()}]`, ...args);
  };
}

// Log all API requests
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();
queryClient.setDefaultOptions({
  queries: {
    retry: 1,
  },
});
```

**React DevTools Profiler:**

```bash
# Install React DevTools extension
# Open DevTools -> Profiler tab
# Record interactions
# Look for slow re-renders
```

**Network Logging:**

```javascript
// Log all fetch requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log('[FETCH]', args[0]);
  return originalFetch.apply(this, args)
    .then(response => {
      console.log('[FETCH RESPONSE]', response.status, args[0]);
      return response;
    })
    .catch(error => {
      console.error('[FETCH ERROR]', args[0], error);
      throw error;
    });
};
```

---

## Performance Troubleshooting

### Issue: Slow API Responses

**Symptoms:**
- API endpoint takes >500ms to respond
- UI feels sluggish
- Users report slow interactions

**Diagnosis:**

```bash
# Test API performance
time curl "http://localhost:8000/api/weeks?year=2025"

# Should be <200ms

# Check database query performance
EXPLAIN ANALYZE SELECT * FROM weeks WHERE season = 2025;

# Look for:
# - Seq Scan (bad) vs Index Scan (good)
# - High Planning Time
# - High Execution Time
```

**Solutions:**

1. **Add database index:**
   ```sql
   CREATE INDEX idx_weeks_season ON weeks(season);
   ANALYZE weeks;
   ```

2. **Optimize queries:**
   ```python
   # Before: Multiple queries
   weeks = db.query(Week).filter_by(season=year).all()
   for week in weeks:
       metadata = db.query(WeekMetadata).filter_by(week_id=week.id).first()

   # After: Single query with join
   weeks = db.query(Week).outerjoin(WeekMetadata).filter_by(season=year).all()
   ```

3. **Enable query caching:**
   ```python
   from cachetools import TTLCache

   week_cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes

   def get_weeks_cached(year):
       if year in week_cache:
           return week_cache[year]
       weeks = get_weeks_from_db(year)
       week_cache[year] = weeks
       return weeks
   ```

4. **Check database connection pool:**
   ```bash
   # Monitor connections
   psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

   # Should be using pool efficiently (not >50 connections)
   ```

### Issue: Slow Frontend Rendering

**Symptoms:**
- Page takes >3s to load
- Dropdown animation is janky
- Mobile carousel stutters

**Diagnosis:**

```javascript
// Measure performance
window.addEventListener('load', () => {
  const perfData = performance.getEntriesByType('navigation')[0];
  console.log('DOM Interactive:', perfData.domInteractive);
  console.log('DOM Complete:', perfData.domComplete);
  console.log('Load Complete:', perfData.loadEventEnd);
});

// Check Lighthouse
// Chrome DevTools -> Lighthouse -> Generate Report
```

**Solutions:**

1. **Code split heavy components:**
   ```typescript
   // Before
   import WeekCarousel from './WeekCarousel';

   // After
   const WeekCarousel = lazy(() => import('./WeekCarousel'));
   ```

2. **Memoize expensive components:**
   ```typescript
   export const WeekSelector = memo(WeekSelectorComponent, (prev, next) => {
     return prev.weeks === next.weeks;
   });
   ```

3. **Optimize bundle size:**
   ```bash
   npm run build -- --analyze

   # Check for:
   # - Duplicate dependencies
   # - Unused imports
   # - Large libraries (use alternatives)
   ```

---

## Mobile-Specific Issues

### Issue: Carousel Position Wrong After Rotate

**Symptoms:**
- User rotates device
- Carousel position resets
- Week selection lost

**Solutions:**

```typescript
// Save position to localStorage
useEffect(() => {
  localStorage.setItem('carouselPosition', currentWeek.toString());
}, [currentWeek]);

// Restore on mount
useEffect(() => {
  const saved = localStorage.getItem('carouselPosition');
  if (saved) {
    setCurrentWeek(parseInt(saved));
  }
}, []);

// Handle orientation change
useEffect(() => {
  const handleOrientationChange = () => {
    // Re-render carousel
    setRenderKey(prev => prev + 1);
  };

  window.addEventListener('orientationchange', handleOrientationChange);
  return () => window.removeEventListener('orientationchange', handleOrientationChange);
}, []);
```

### Issue: Touch Events Blocked

**Symptoms:**
- Tap doesn't work on iOS
- Long press doesn't trigger
- Context menu appears on hold

**Solutions:**

```css
/* Allow touch interactions */
body {
  touch-action: manipulation;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
}

/* Ensure targets are touchable */
.week-card {
  min-width: 44px;   /* Min touch target */
  min-height: 44px;
  -webkit-user-select: none;
  user-select: none;
  cursor: pointer;
}
```

### Issue: Viewport Scale Issues

**Symptoms:**
- Text too large/small
- Can pinch to zoom when shouldn't
- Responsive layout broken

**Solutions:**

```html
<!-- Correct viewport meta tag -->
<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0,
               maximum-scale=1.0,
               user-scalable=no">

<!-- OR allow zoom for accessibility -->
<meta name="viewport"
      content="width=device-width,
               initial-scale=1.0,
               user-scalable=yes">
```

---

## Database Issues

### Issue: Connection Pool Exhausted

**Symptoms:**
- "QueuePool limit exceeded" error
- Database becomes unresponsive
- New requests timeout

**Solutions:**

```python
# Check connections
psql -c "SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;"

# Increase pool size in .env
DATABASE_POOL_SIZE=30
DATABASE_MAX_OVERFLOW=50

# Kill idle connections
psql -c "SELECT pg_terminate_backend(pid)
         FROM pg_stat_activity
         WHERE state = 'idle'
         AND query_start < now() - interval '10 min';"
```

### Issue: Migration Failed

**Symptoms:**
- "Current database revision" doesn't match expected
- Certain endpoints return 500
- Schema mismatch errors

**Solutions:**

```bash
# Check current state
alembic current
alembic history

# Rollback one step
alembic downgrade -1

# Reapply
alembic upgrade +1

# Or rollback to specific
alembic downgrade <revision>

# Verify
alembic current
```

---

## API Issues

### Issue: CORS Error

**Symptoms:**
- Browser console: "No 'Access-Control-Allow-Origin' header"
- API calls fail from frontend
- Works in Postman/cURL

**Solutions:**

```python
# In backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://cortex.example.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: 500 Internal Server Error

**Symptoms:**
- API returns 500 with generic message
- No details on error cause
- Server logs show errors

**Solutions:**

```bash
# Check server logs
tail -f /var/log/cortex/cortex.log

# Look for stack traces
grep -i "error\|exception" /var/log/cortex/cortex.log

# Enable debug mode temporarily
export DEBUG=True

# Check database connection
curl http://localhost:8000/health
```

---

## Frontend Issues

### Issue: White Screen of Death

**Symptoms:**
- App doesn't render
- No error message
- Blank white page

**Solutions:**

```javascript
// Add error boundary at root
class ErrorBoundary extends React.Component {
  componentDidCatch(error, errorInfo) {
    console.error('Render error:', error, errorInfo);
  }

  render() {
    try {
      return this.props.children;
    } catch (error) {
      return <div>Error: {error.message}</div>;
    }
  }
}
```

### Issue: State Lost on Refresh

**Symptoms:**
- Week selection lost after refresh
- Have to select week again
- localStorage not working

**Solutions:**

```typescript
// Verify persist middleware enabled
useWeekStore = create<WeekState>()(
  persist(
    (set, get) => ({ ... }),
    {
      name: 'week-store',  // localStorage key
      version: 1,          // Migration version
    }
  )
);

// Check localStorage
localStorage.getItem('week-store')
// Should return stored state

// Clear and reinitialize if corrupted
localStorage.removeItem('week-store');
location.reload();
```

---

## Diagnostic Tools

### Backend Diagnostics

**Check Service Status:**
```bash
# Systemd service
sudo systemctl status cortex
sudo systemctl restart cortex
sudo journalctl -u cortex -f

# Or if running directly
lsof -i :8000  # See what's using port 8000
```

**Database Diagnostics:**
```bash
# Connect
psql -U cortex -d cortex_prod

# Check connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Check locks
SELECT pid, usename, pg_blocking_pids(pid) FROM pg_stat_activity WHERE pg_blocking_pids(pid)::text != '{}';

# Check indexes
SELECT * FROM pg_stat_user_indexes;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Frontend Diagnostics

**DevTools Checklist:**
- [ ] Console: No red errors
- [ ] Network: All requests 200-399
- [ ] Performance: Lighthouse >90
- [ ] Memory: No leaks on long usage
- [ ] Accessibility: Issues minimal
- [ ] Responsive: Works on mobile/tablet/desktop

**Quick Debug Script:**
```javascript
// Paste in browser console
const diag = {
  store: () => {
    const state = useWeekStore.getState();
    console.table(state);
  },
  api: async () => {
    const res = await fetch('/api/weeks?year=2025');
    console.log(await res.json());
  },
  health: async () => {
    const res = await fetch('/health');
    console.log(await res.json());
  }
};

// Run: diag.store(); diag.api(); diag.health();
```

---

**End of Troubleshooting Guide**
