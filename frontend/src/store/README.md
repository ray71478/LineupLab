# Store Documentation

This directory contains Zustand stores for global state management.

## Available Stores

### 1. weekStore.ts
Manages global week state including:
- Currently selected year and week
- Week metadata and import status
- Available years for season selection

**Usage:**
```typescript
import { useWeekStore } from './store';

const { currentWeek, setCurrentWeek } = useWeekStore();
```

### 2. modeStore.ts
Manages global contest mode state:
- Contest mode ('main' | 'showdown')
- Mode switching between Main Slate and Showdown contests

**Usage:**
```typescript
import { useModeStore } from './store';

const { mode, setMode } = useModeStore();

// Or use the convenience hook:
import { useMode } from '../hooks';

const { mode, setMode } = useMode();
```

## State Persistence

Both stores use Zustand's `persist` middleware to save state to localStorage:
- `weekStore` → `localStorage['week-store']`
- `modeStore` → `localStorage['mode-store']`

State persists across page refreshes and browser sessions.

## Testing

Store tests are located in `__tests__/` subdirectory:
- `weekStore.test.ts` - Tests for week store
- `modeStore.test.ts` - Tests for mode store

Run tests with:
```bash
npm run test
```

## Architecture

All stores follow this pattern:
1. Define state interface with properties and actions
2. Create store with `create<StateInterface>()(persist(...))`
3. Export store hook for component usage
4. Include `reset()` helper for testing

## Adding New Stores

To add a new store:
1. Create `{name}Store.ts` following the pattern above
2. Add tests in `__tests__/{name}Store.test.ts`
3. Export from `index.ts`
4. Optionally create a custom hook in `../hooks/use{Name}.ts`
