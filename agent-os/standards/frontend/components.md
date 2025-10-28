## UI component best practices

### General Principles
- **Single Responsibility**: Each component should have one clear purpose and do it well
- **Reusability**: Design components to be reused across different contexts with configurable props
- **Composability**: Build complex UIs by combining smaller, simpler components rather than monolithic structures
- **Clear Interface**: Define explicit, well-documented props with sensible defaults using TypeScript
- **Encapsulation**: Keep internal implementation details private and expose only necessary APIs
- **Consistent Naming**: Use PascalCase for components (e.g., `PlayerCard`, `SmartScoreSlider`)
- **State Management**: Keep state as local as possible; lift to Zustand store only when needed globally
- **Minimal Props**: Keep the number of props manageable; if a component needs many props, consider composition
- **TypeScript**: Use TypeScript for all components with explicit prop types

### Cortex Component Structure

**File Organization:**
```
src/
├── components/
│   ├── common/           # Shared components (Button, Card, etc.)
│   ├── players/          # Player-related components
│   │   ├── PlayerCard.tsx
│   │   ├── PlayerTable.tsx
│   │   └── PlayerRow.tsx
│   ├── lineups/          # Lineup-related components
│   │   ├── LineupCard.tsx
│   │   ├── LineupGrid.tsx
│   │   └── LineupExport.tsx
│   ├── smart-score/      # Smart Score components
│   │   ├── WeightSlider.tsx
│   │   ├── ProfileSelector.tsx
│   │   └── ScoreDisplay.tsx
│   └── layout/           # Layout components
│       ├── Sidebar.tsx
│       ├── Header.tsx
│       └── BottomNav.tsx
├── pages/                # Page-level components
│   ├── Dashboard.tsx
│   ├── Players.tsx
│   ├── SmartScore.tsx
│   └── Lineups.tsx
├── hooks/                # Custom React hooks
│   ├── usePlayerPool.ts
│   ├── useSmartScore.ts
│   └── useLineups.ts
└── stores/               # Zustand stores
    ├── weekStore.ts
    ├── playerStore.ts
    └── smartScoreStore.ts
```

### Component Patterns

#### Basic Component Template
```typescript
import { FC } from 'react';
import { Box, Typography } from '@mui/material';

interface PlayerCardProps {
  player: {
    name: string;
    team: string;
    position: string;
    salary: number;
    smartScore: number;
  };
  onClick?: () => void;
}

export const PlayerCard: FC<PlayerCardProps> = ({ player, onClick }) => {
  return (
    <Box
      onClick={onClick}
      sx={{
        p: 2,
        bgcolor: 'background.paper',
        borderRadius: 2,
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? { boxShadow: 3 } : {},
      }}
    >
      <Typography variant="h6">{player.name}</Typography>
      <Typography variant="body2" color="text.secondary">
        {player.team} • {player.position}
      </Typography>
      <Typography variant="body1" color="primary">
        ${player.salary.toLocaleString()}
      </Typography>
    </Box>
  );
};
```

#### Component with State
```typescript
import { FC, useState } from 'react';
import { Box, Slider, Typography } from '@mui/material';

interface WeightSliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

export const WeightSlider: FC<WeightSliderProps> = ({
  label,
  value,
  onChange,
  min = 0,
  max = 2,
  step = 0.1,
}) => {
  const [localValue, setLocalValue] = useState(value);

  const handleChange = (_: Event, newValue: number | number[]) => {
    const val = Array.isArray(newValue) ? newValue[0] : newValue;
    setLocalValue(val);
  };

  const handleChangeCommitted = (_: Event, newValue: number | number[]) => {
    const val = Array.isArray(newValue) ? newValue[0] : newValue;
    onChange(val);
  };

  return (
    <Box>
      <Typography variant="body2" gutterBottom>
        {label}: {localValue.toFixed(1)}
      </Typography>
      <Slider
        value={localValue}
        onChange={handleChange}
        onChangeCommitted={handleChangeCommitted}
        min={min}
        max={max}
        step={step}
        marks
        valueLabelDisplay="auto"
      />
    </Box>
  );
};
```

#### Component with Custom Hook
```typescript
// hooks/usePlayerPool.ts
import { useQuery } from '@tanstack/react-query';
import { fetchPlayerPool } from '../api/players';

export const usePlayerPool = (weekId: number) => {
  return useQuery({
    queryKey: ['playerPool', weekId],
    queryFn: () => fetchPlayerPool(weekId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// components/players/PlayerTable.tsx
import { FC } from 'react';
import { usePlayerPool } from '../../hooks/usePlayerPool';
import { CircularProgress, Alert } from '@mui/material';

interface PlayerTableProps {
  weekId: number;
}

export const PlayerTable: FC<PlayerTableProps> = ({ weekId }) => {
  const { data: players, isLoading, error } = usePlayerPool(weekId);

  if (isLoading) return <CircularProgress />;
  if (error) return <Alert severity="error">Failed to load players</Alert>;
  if (!players) return null;

  return (
    <Table>
      {/* Render players */}
    </Table>
  );
};
```

#### Component with Zustand Store
```typescript
// stores/weekStore.ts
import { create } from 'zustand';

interface WeekState {
  currentWeek: number;
  setCurrentWeek: (week: number) => void;
}

export const useWeekStore = create<WeekState>((set) => ({
  currentWeek: 9,
  setCurrentWeek: (week) => set({ currentWeek: week }),
}));

// components/layout/WeekSelector.tsx
import { FC } from 'react';
import { Select, MenuItem } from '@mui/material';
import { useWeekStore } from '../../stores/weekStore';

export const WeekSelector: FC = () => {
  const { currentWeek, setCurrentWeek } = useWeekStore();

  return (
    <Select
      value={currentWeek}
      onChange={(e) => setCurrentWeek(e.target.value as number)}
    >
      {Array.from({ length: 18 }, (_, i) => i + 1).map((week) => (
        <MenuItem key={week} value={week}>
          Week {week}
        </MenuItem>
      ))}
    </Select>
  );
};
```

### Composition Patterns

#### Container/Presenter Pattern
```typescript
// Container: Handles data fetching and state
export const PlayerPoolContainer: FC = () => {
  const { currentWeek } = useWeekStore();
  const { data: players, isLoading } = usePlayerPool(currentWeek);

  return <PlayerPoolPresenter players={players} isLoading={isLoading} />;
};

// Presenter: Pure UI component
interface PlayerPoolPresenterProps {
  players?: Player[];
  isLoading: boolean;
}

export const PlayerPoolPresenter: FC<PlayerPoolPresenterProps> = ({
  players,
  isLoading,
}) => {
  if (isLoading) return <LoadingState />;
  if (!players) return <EmptyState />;

  return (
    <Box>
      {players.map((player) => (
        <PlayerCard key={player.player_key} player={player} />
      ))}
    </Box>
  );
};
```

#### Compound Components
```typescript
// Parent component with context
interface LineupCardContextValue {
  lineup: Lineup;
  isExpanded: boolean;
  toggleExpanded: () => void;
}

const LineupCardContext = createContext<LineupCardContextValue | null>(null);

export const LineupCard: FC<{ lineup: Lineup }> & {
  Header: FC;
  Body: FC;
  Footer: FC;
} = ({ lineup, children }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <LineupCardContext.Provider
      value={{ lineup, isExpanded, toggleExpanded: () => setIsExpanded(!isExpanded) }}
    >
      <Box sx={{ bgcolor: 'background.paper', borderRadius: 2 }}>
        {children}
      </Box>
    </LineupCardContext.Provider>
  );
};

// Child components
LineupCard.Header = () => {
  const { lineup, toggleExpanded } = useContext(LineupCardContext)!;
  return (
    <Box onClick={toggleExpanded} sx={{ p: 2, cursor: 'pointer' }}>
      <Typography variant="h6">Lineup {lineup.number}</Typography>
    </Box>
  );
};

// Usage
<LineupCard lineup={lineup}>
  <LineupCard.Header />
  <LineupCard.Body />
  <LineupCard.Footer />
</LineupCard>
```

### Performance Optimization

#### Memoization
```typescript
import { memo, useMemo, useCallback } from 'react';

// Memoize expensive components
export const PlayerRow = memo<PlayerRowProps>(({ player }) => {
  return <TableRow>{/* ... */}</TableRow>;
});

// Memoize expensive calculations
const sortedPlayers = useMemo(() => {
  return players.sort((a, b) => b.smartScore - a.smartScore);
}, [players]);

// Memoize callbacks
const handlePlayerClick = useCallback((playerId: string) => {
  console.log('Clicked player:', playerId);
}, []);
```

#### Code Splitting
```typescript
import { lazy, Suspense } from 'react';
import { CircularProgress } from '@mui/material';

// Lazy load heavy components
const AdvancedAnalytics = lazy(() => import('./AdvancedAnalytics'));

export const Dashboard: FC = () => {
  return (
    <Box>
      <Suspense fallback={<CircularProgress />}>
        <AdvancedAnalytics />
      </Suspense>
    </Box>
  );
};
```

### Cortex-Specific Components

**Required Components (MVP):**
- `WeekSelector` - Dropdown to select week 1-18
- `DataImportButton` - Upload XLSX files (LineStar, DraftKings, NFL Stats)
- `PlayerTable` - Sortable, filterable table of players
- `WeightSlider` - Slider for Smart Score weights (W1-W8)
- `ProfileSelector` - Dropdown to load/save weight profiles
- `LineupGenerator` - Form to configure lineup generation settings
- `LineupGrid` - Display 10 generated lineups
- `LineupCard` - Individual lineup display (9 players + totals)
- `ExportButton` - Download lineups as DraftKings CSV

**Component Naming Conventions:**
- Use PascalCase: `PlayerCard`, `SmartScoreSlider`
- Be specific: `LineupExportButton` not `ExportButton`
- Avoid generic names: `PlayerTable` not `Table`

### Testing Components
```typescript
import { render, screen } from '@testing-library/react';
import { PlayerCard } from './PlayerCard';

describe('PlayerCard', () => {
  it('renders player name and salary', () => {
    const player = {
      name: 'Christian McCaffrey',
      team: 'SF',
      position: 'RB',
      salary: 9500,
      smartScore: 12.5,
    };

    render(<PlayerCard player={player} />);

    expect(screen.getByText('Christian McCaffrey')).toBeInTheDocument();
    expect(screen.getByText('$9,500')).toBeInTheDocument();
  });
});
```
