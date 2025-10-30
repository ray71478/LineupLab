# Week Management Component Documentation

**Version:** 1.0
**Last Updated:** October 28, 2025
**Status:** Complete and Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Shared Types & Interfaces](#shared-types--interfaces)
3. [Layout Components](#layout-components)
4. [Week Selection Components](#week-selection-components)
5. [Status & Metadata Components](#status--metadata-components)
6. [Mobile Components](#mobile-components)
7. [Utility Components](#utility-components)
8. [Usage Examples](#usage-examples)
9. [Styling & Theming](#styling--theming)

---

## Overview

The week management system provides a comprehensive set of React components for:

- Year and week selection (desktop dropdown & mobile carousel)
- Status badge display (completed, active, upcoming)
- Import status tracking
- Week metadata display
- Responsive layouts
- Dark mode optimization
- Material Design compliance

All components use **Material-UI v5** and are fully responsive across all device sizes.

---

## Shared Types & Interfaces

### Week Interface
```typescript
interface Week {
  id: number;
  season: number;
  week_number: number;
  status: 'active' | 'upcoming' | 'completed';
  status_override: string | null;
  nfl_slate_date: string;
  is_locked: boolean;
  locked_at: string | null;
  metadata: WeekMetadata;
}
```

### WeekMetadata Interface
```typescript
interface WeekMetadata {
  kickoff_time: string;
  espn_link: string;
  slate_start: string;
  import_status: 'pending' | 'imported' | 'error';
  import_count: number;
  import_timestamp: string | null;
  error_message?: string;
}
```

### Status Type
```typescript
type WeekStatus = 'active' | 'upcoming' | 'completed';
type ImportStatus = 'pending' | 'imported' | 'error';
```

---

## Layout Components

### MainLayout

Main application layout with responsive header.

**File:** `/frontend/src/components/layout/MainLayout.tsx`

**Props:**
```typescript
interface MainLayoutProps {
  children: ReactNode;
  headerExtra?: ReactNode;
  showWeekNavigation?: boolean;
}
```

**Features:**
- Dark mode background (#121212)
- Responsive header with AppBar
- WeekNavigation integrated in header
- Proper spacing and alignment
- Material Design elevation

**Usage:**
```tsx
import { MainLayout } from '@/components/layout';

function App() {
  return (
    <MainLayout showWeekNavigation={true}>
      <DashboardContent />
    </MainLayout>
  );
}
```

**Responsive Behavior:**
- Desktop (>960px): WeekSelector in header
- Mobile (<600px): WeekCarousel below header
- Uses MUI `useMediaQuery` for detection

---

### WeekNavigation

Responsive wrapper component that renders appropriate week selector based on screen size.

**File:** `/frontend/src/components/layout/WeekNavigation.tsx`

**Props:**
```typescript
interface WeekNavigationProps {
  onWeekChange?: (week: number) => void;
  onYearChange?: (year: number) => void;
  showMetadata?: boolean;
}
```

**Features:**
- Automatic responsive switching
- No props needed (uses Zustand store)
- Renders WeekSelector on desktop
- Renders WeekCarousel on mobile
- Loading states during fetch

**Usage:**
```tsx
import { WeekNavigation } from '@/components/layout';

function Header() {
  return (
    <Box>
      <Logo />
      <WeekNavigation />
    </Box>
  );
}
```

---

## Week Selection Components

### WeekSelector (Desktop Dropdown)

Material-UI Select dropdown for choosing weeks.

**File:** `/frontend/src/components/layout/WeekSelector.tsx`

**Props:**
```typescript
interface WeekSelectorProps {
  onWeekChange?: (week: number) => void;
  showMetadata?: boolean;  // Default: true
}
```

**Features:**
- Material-UI Select dropdown
- All 18 weeks (1-18) displayed
- Current week highlighted with glow effect
- Auto-scroll to current week on open
- Smooth 200ms open/close animation
- Status badge for each week
- Tooltip on hover showing:
  - Kickoff time
  - Import count
  - Last import time
  - ESPN link icon
- Keyboard navigation:
  - Arrow keys: previous/next week
  - Home/End: jump to first/last week
  - Number keys (1-9): jump to week
  - Escape: close dropdown
- Disabled visual state for locked weeks

**Usage:**
```tsx
import { WeekSelector } from '@/components/layout';

function Header() {
  const handleWeekChange = (weekNumber: number) => {
    console.log(`Week changed to: ${weekNumber}`);
  };

  return (
    <WeekSelector
      onWeekChange={handleWeekChange}
      showMetadata={true}
    />
  );
}
```

**State Management:**
Uses Zustand `useWeekStore` for state:
- Automatically updates `currentWeek`
- Persists to localStorage
- Triggers data fetch when changed

**Styling:**
```typescript
// Dark mode optimized
backgroundColor: 'rgba(255, 255, 255, 0.05)',
color: '#ffffff',
'&:hover': {
  backgroundColor: 'rgba(255, 255, 255, 0.1)',
},
// Glow effect for current week
animation: `${glowAnimation} 2s ease-in-out infinite`,
boxShadow: '0 0 12px rgba(76, 175, 80, 0.6)',
```

---

### YearSelector

Dropdown for selecting NFL season year.

**File:** `/frontend/src/components/layout/YearSelector.tsx`

**Props:**
```typescript
interface YearSelectorProps {
  currentYear: number;
  onYearChange: (year: number) => void;
  availableYears?: number[];  // Default: [2025-2030]
}
```

**Features:**
- Material-UI Select dropdown
- Years: 2025-2030
- Current year highlighted
- Loading state while fetching weeks
- Smooth transition animation
- Triggers `useWeeks` hook on change

**Usage:**
```tsx
import { YearSelector } from '@/components/layout';
import { useWeekStore } from '@/store/weekStore';

function Header() {
  const { currentYear } = useWeekStore();

  const handleYearChange = (year: number) => {
    // Zustand store handles this internally
  };

  return (
    <YearSelector
      currentYear={currentYear}
      onYearChange={handleYearChange}
      availableYears={[2025, 2026, 2027, 2028, 2029, 2030]}
    />
  );
}
```

**Responsive Behavior:**
- Hidden on mobile (<600px)
- Shows inline with WeekSelector on desktop
- Proper spacing between components

---

### WeekCarousel (Mobile Swipeable)

Swipeable carousel for mobile week navigation.

**File:** `/frontend/src/components/mobile/WeekCarousel.tsx`

**Props:**
```typescript
interface WeekCarouselProps {
  weeks: Week[];
  currentWeek: number;
  onWeekChange: (week: number) => void;
  showMetadata?: boolean;  // Default: true
}
```

**Features:**
- Horizontal swipeable carousel
- Uses `react-swipeable` library
- Large week number (48px font)
- Status badge below number
- Week range indicator (e.g., "Week 5 of 18")
- Shows 3 weeks at a time (current + left + right)
- Swipe gestures:
  - Swipe left: next week
  - Swipe right: previous week
  - Fast swipe: multiple weeks
- Smooth snap-to-center animation (300ms)
- Tap to open metadata modal
- Virtualized for performance
- Debounced swipe handlers (100ms)

**Usage:**
```tsx
import { WeekCarousel } from '@/components/mobile';
import { useWeekStore } from '@/store/weekStore';

function MobileWeekNav() {
  const { weeks, currentWeek } = useWeekStore();

  return (
    <WeekCarousel
      weeks={weeks}
      currentWeek={currentWeek}
      onWeekChange={(week) => {
        // Update store
      }}
      showMetadata={true}
    />
  );
}
```

**Swipe Behavior:**
```
Swipe Velocity: 0.1-0.5 = +1 week
                0.5-1.0 = +2 weeks
                1.0+    = +3-5 weeks

Snap Behavior: Release -> snap to nearest center position
               Smooth animation over 300ms
```

**Performance:**
- React.memo optimization on individual cards
- Virtual scrolling for large lists
- Debounced swipe handlers prevent jank
- 60fps animation target

---

### WeekCarouselCard

Individual carousel card for mobile carousel.

**File:** `/frontend/src/components/mobile/WeekCarouselCard.tsx`

**Props:**
```typescript
interface WeekCarouselCardProps {
  week: Week;
  isActive: boolean;
  onClick?: () => void;
}
```

**Features:**
- Large week number display
- Status badge
- Optional metadata preview
- Active week: larger and highlighted
- Inactive weeks: smaller and muted
- Tap to select/open details

**Usage:**
```tsx
<WeekCarouselCard
  week={week}
  isActive={currentWeek === week.week_number}
  onClick={() => handleWeekSelect(week.week_number)}
/>
```

---

## Status & Metadata Components

### WeekStatusBadge

Icon-based status indicator for weeks.

**File:** `/frontend/src/components/weeks/WeekStatusBadge.tsx`

**Props:**
```typescript
interface WeekStatusBadgeProps {
  status: 'active' | 'upcoming' | 'completed';
  importStatus?: 'pending' | 'imported' | 'error';
  isCurrentWeek?: boolean;
  compact?: boolean;  // Default: false
}
```

**Features:**
- Material-UI icons only (no emojis)
  - Completed: CheckCircleIcon (green, #4caf50)
  - Pending: RemoveCircleIcon (gray, #b0bec5)
  - Error: WarningIcon (orange, #ff9800)
- Glow effect for active weeks (2s animation)
- Tooltip with status description
- Compact mode for dense layouts
- Dark mode optimized colors

**Icons:**
```typescript
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import WarningIcon from '@mui/icons-material/Warning';
```

**Usage:**
```tsx
import { WeekStatusBadge } from '@/components/weeks';

function WeekCard({ week }) {
  return (
    <Box>
      <Typography variant="h6">Week {week.week_number}</Typography>
      <WeekStatusBadge
        status={week.status}
        importStatus={week.metadata.import_status}
        isCurrentWeek={true}
        compact={false}
      />
    </Box>
  );
}
```

**Colors:**
```typescript
// Dark mode optimized
completed: '#4caf50' (green)
active: '#1976d2' (blue, with glow)
upcoming: '#b0bec5' (gray)
error: '#ff9800' (orange)
```

---

### WeekImportStatusBadge

Display import status with details.

**File:** `/frontend/src/components/weeks/WeekImportStatusBadge.tsx`

**Props:**
```typescript
interface WeekImportStatusBadgeProps {
  importStatus: 'pending' | 'imported' | 'error';
  importCount: number;
  importTimestamp: string | null;
  errorMessage?: string;
}
```

**Features:**
- Status label: "Imported", "Pending", "Error"
- Show player count if imported
- Show import timestamp if available
- Show error message in tooltip if error
- Material-UI icons for status indication
- Hover reveals full details

**Usage:**
```tsx
import { WeekImportStatusBadge } from '@/components/weeks';

function WeekDetails({ week }) {
  return (
    <WeekImportStatusBadge
      importStatus={week.metadata.import_status}
      importCount={week.metadata.import_count}
      importTimestamp={week.metadata.import_timestamp}
      errorMessage={week.metadata.error_message}
    />
  );
}
```

---

### WeekMetadataPanel

Displays detailed metadata for a week.

**File:** `/frontend/src/components/weeks/WeekMetadataPanel.tsx`

**Props:**
```typescript
interface WeekMetadataPanelProps {
  week: Week;
  isLoading?: boolean;
  compact?: boolean;  // Default: false
}
```

**Features:**
- NFL slate date (formatted: "Sunday, September 7")
- Kickoff time (formatted: "1:00 PM ET")
- ESPN schedule link (clickable, opens in new tab)
- Import status badge
- Import details tooltip:
  - Player count
  - Import timestamp
  - Data source (if available)
  - Error message (if error)
- Responsive layout (full panel for desktop, compact for mobile)
- Loading state with skeleton
- Material-UI Stack and Typography

**Usage:**
```tsx
import { WeekMetadataPanel } from '@/components/weeks';

function WeekDetails({ week, isLoading }) {
  return (
    <WeekMetadataPanel
      week={week}
      isLoading={isLoading}
      compact={false}
    />
  );
}
```

**Formatted Output Examples:**
```
Date: "Sunday, September 7, 2025"
Time: "1:00 PM ET"
ESPN Link: "https://www.espn.com/nfl/schedule/_/week/5/year/2025"
Import: "Imported 153 players on 10/5/2025 at 2:30 PM"
```

---

### WeekMetadataModal

Full-screen modal showing week metadata (mobile).

**File:** `/frontend/src/components/weeks/WeekMetadataModal.tsx`

**Props:**
```typescript
interface WeekMetadataModalProps {
  week: Week;
  open: boolean;
  onClose: () => void;
}
```

**Features:**
- Full-screen modal on mobile
- Display all metadata with larger typography
- Include ESPN link
- Include import details
- Close button
- Swipe to close gesture
- Material-UI Dialog component
- Proper touch targets (44x44px min)

**Usage:**
```tsx
import { WeekMetadataModal } from '@/components/weeks';
import { useState } from 'react';

function MobileWeekView() {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedWeek, setSelectedWeek] = useState<Week | null>(null);

  return (
    <>
      <WeekCarousel
        onTap={(week) => {
          setSelectedWeek(week);
          setModalOpen(true);
        }}
      />
      {selectedWeek && (
        <WeekMetadataModal
          week={selectedWeek}
          open={modalOpen}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}
```

---

## Mobile Components

### WeekCarouselLazy

Lazy-loaded version of WeekCarousel for performance.

**File:** `/frontend/src/components/mobile/WeekCarouselLazy.tsx`

**Features:**
- React.lazy() wrapper
- Suspense boundary with skeleton loader
- Loads only on mobile breakpoint
- Improves initial page load performance

**Usage:**
```tsx
import { WeekCarouselLazy } from '@/components/mobile';

const WeekCarousel = lazy(() => import('./WeekCarouselLazy'));

function App() {
  return (
    <Suspense fallback={<Skeleton />}>
      <WeekCarousel />
    </Suspense>
  );
}
```

---

## Utility Components

### WeekStatusBadgeOptimized

Memoized version of WeekStatusBadge for performance.

**File:** `/frontend/src/components/weeks/WeekStatusBadgeOptimized.tsx`

**Features:**
- React.memo wrapper
- Prevents unnecessary re-renders
- Same props as WeekStatusBadge
- Recommended for use in lists

**Usage:**
```tsx
import { WeekStatusBadgeOptimized } from '@/components/weeks';

function WeekList({ weeks }) {
  return weeks.map(week => (
    <WeekStatusBadgeOptimized
      key={week.id}
      status={week.status}
      isCurrentWeek={week.status === 'active'}
    />
  ));
}
```

---

### WeekMetadataPanelOptimized

Memoized version of WeekMetadataPanel.

**File:** `/frontend/src/components/weeks/WeekMetadataPanelOptimized.tsx`

**Features:**
- React.memo wrapper
- Prevents unnecessary re-renders
- Same props as WeekMetadataPanel
- Use in repeating lists

---

### WeekSelectorSkeleton

Skeleton loader for WeekSelector during loading.

**File:** `/frontend/src/components/weeks/WeekSelectorSkeleton.tsx`

**Features:**
- Material-UI Skeleton components
- Matches WeekSelector dimensions
- Smooth loading state
- Dark mode optimized

**Usage:**
```tsx
import { WeekSelectorSkeleton } from '@/components/weeks';

function Header() {
  const { isLoading, weeks } = useWeekStore();

  return (
    <Box>
      {isLoading ? <WeekSelectorSkeleton /> : <WeekSelector />}
    </Box>
  );
}
```

---

### WeekLoadingState

Loading state component with spinner.

**File:** `/frontend/src/components/weeks/WeekLoadingState.tsx`

**Features:**
- Material-UI Spinner/CircularProgress
- Loading text message
- Centered layout
- Dark mode optimized

---

### WeekManagementErrorBoundary

Error boundary for week management components.

**File:** `/frontend/src/components/layout/WeekManagementErrorBoundary.tsx`

**Features:**
- Catches errors in week management components
- Shows user-friendly error message
- Logs error for debugging
- Recovery button to reset state
- Prevents entire app crash

**Usage:**
```tsx
import { WeekManagementErrorBoundary } from '@/components/layout';

function App() {
  return (
    <WeekManagementErrorBoundary>
      <MainLayout>
        <Dashboard />
      </MainLayout>
    </WeekManagementErrorBoundary>
  );
}
```

---

## Usage Examples

### Complete Week Selection Header
```tsx
import React from 'react';
import { Box, AppBar, Toolbar, Typography } from '@mui/material';
import { MainLayout } from '@/components/layout';
import { WeekNavigation } from '@/components/layout';
import { WeekManagementErrorBoundary } from '@/components/layout';

function App() {
  return (
    <WeekManagementErrorBoundary>
      <MainLayout>
        <AppBar position="static" sx={{ backgroundColor: '#121212' }}>
          <Toolbar>
            <Typography variant="h6" sx={{ flex: 1 }}>
              Cortex DFS
            </Typography>
            <WeekNavigation />
          </Toolbar>
        </AppBar>
        <DashboardContent />
      </MainLayout>
    </WeekManagementErrorBoundary>
  );
}

export default App;
```

### Desktop Week Display
```tsx
import { useWeekStore } from '@/store/weekStore';
import { WeekMetadataPanel } from '@/components/weeks';
import { Box, Card, CardContent } from '@mui/material';

function WeekDisplay() {
  const currentWeek = useWeekStore(state => state.getCurrentWeekData());

  if (!currentWeek) return null;

  return (
    <Card>
      <CardContent>
        <Box sx={{ p: 2 }}>
          <WeekMetadataPanel week={currentWeek} compact={false} />
        </Box>
      </CardContent>
    </Card>
  );
}
```

### Mobile Week Navigation
```tsx
import { useWeekStore } from '@/store/weekStore';
import { WeekCarousel } from '@/components/mobile';
import { Box } from '@mui/material';

function MobileNav() {
  const { weeks, currentWeek } = useWeekStore();

  return (
    <Box sx={{ p: 2 }}>
      <WeekCarousel
        weeks={weeks}
        currentWeek={currentWeek}
        onWeekChange={(week) => {
          useWeekStore.setState({ currentWeek: week });
        }}
      />
    </Box>
  );
}
```

---

## Styling & Theming

### Dark Mode Palette
```typescript
// Theme colors (from Material Design)
const palette = {
  primary: {
    main: '#1976d2', // Material Blue
  },
  secondary: {
    main: '#dc004e', // Material Pink
  },
  background: {
    default: '#121212',
    paper: '#1e1e1e',
  },
  text: {
    primary: '#ffffff',
    secondary: '#b0bec5',
  },
  success: {
    main: '#4caf50', // Green for completed
  },
  warning: {
    main: '#ff9800', // Orange for errors
  },
  divider: '#424242',
};
```

### CSS Animations
```typescript
// Glow effect (2s continuous)
@keyframes glow {
  0% { box-shadow: 0 0 4px rgba(76, 175, 80, 0.3); }
  50% { box-shadow: 0 0 12px rgba(76, 175, 80, 0.6); }
  100% { box-shadow: 0 0 4px rgba(76, 175, 80, 0.3); }
}

// Dropdown open animation (200ms)
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

// Carousel swipe animation (300ms)
@keyframes slideSwipe {
  from { transform: translateX(0); }
  to { transform: translateX(-100%); }
}
```

### Responsive Breakpoints
```typescript
const breakpoints = {
  xs: 0,    // Extra small (mobile)
  sm: 600,  // Small (mobile)
  md: 960,  // Medium (tablet)
  lg: 1280, // Large (desktop)
  xl: 1920, // Extra large (large desktop)
};

// Component visibility by breakpoint:
WeekSelector:      hidden xs-sm, visible md+
WeekCarousel:      visible xs-sm, hidden md+
YearSelector:      hidden xs-sm, visible md+
WeekMetadataPanel: hidden xs-sm, visible md+ (compact on sm)
```

---

## Performance Optimization

### Code Splitting
- WeekCarousel lazy loaded on mobile
- WeekMetadataModal lazy loaded on demand

### Memoization
- WeekStatusBadgeOptimized prevents re-renders
- WeekMetadataPanelOptimized prevents re-renders
- List components use React.memo

### Bundle Size
```
Week Management Feature Bundle:
- Gzipped: ~45KB
- Uncompressed: ~150KB
Target: <100KB gzipped
```

### Animation Performance
- CSS animations for 60fps
- GPU-accelerated transforms
- will-change hints for animated elements

---

**End of Component Documentation**
