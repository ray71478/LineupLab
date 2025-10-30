# Week Management Feature - Technical Specification

**Feature:** Week Management System
**Version:** 1.0
**Date:** October 27, 2025
**Status:** Ready for Implementation
**Estimated Effort:** 8-10 hours
**Dependencies:** Data Import System (completed)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Specifications](#api-specifications)
5. [Frontend Components](#frontend-components)
6. [UI/UX Design](#uiux-design)
7. [State Management](#state-management)
8. [Data Flow](#data-flow)
9. [Mobile Considerations](#mobile-considerations)
10. [Validation Rules](#validation-rules)
11. [Error Handling](#error-handling)
12. [Integration Points](#integration-points)
13. [Implementation Plan](#implementation-plan)
14. [Test Cases](#test-cases)
15. [Acceptance Criteria](#acceptance-criteria)

---

## Overview

### Purpose

Enable users to create, manage, and navigate between NFL seasons and weeks (1-18) with automatic week status management, modern Material Design UI, and seamless integration with the Data Import System. Weeks are dynamically generated based on NFL calendar and support flexible year selection for current and future seasons.

### Key Objectives

1. **Dynamic Week Generation** - Auto-generate weeks based on NFL calendar (not hardcoded)
2. **Smart Status Management** - Automatic status updates (Active/Upcoming/Completed) with manual override capability
3. **Modern Navigation** - Sleek Material Design dropdown selector as primary UI element
4. **Professional Visual Design** - Dark mode optimized, Material Design icons, glow effects
5. **Seamless Data Integration** - Link data imports to selected week; prevent editing once data imported
6. **Mobile-Optimized UX** - Swipeable carousel or modal-based navigation for mobile
7. **Rich Metadata Display** - NFL slate dates, kickoff times, ESPN links, import status indicators
8. **Immutable Data** - Weeks locked once player pool data is imported

### Success Metrics

- Automatic week status updates within 1 second of navigation
- Current week visually distinguished with smooth auto-scroll
- Zero friction in week selection across all device sizes
- 100% data integrity (no imported weeks can be edited/deleted)
- <200ms dropdown open animation
- All Material Design standards followed with NO emojis

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Week Management System                         │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────┐      │   │
│  │  │  Desktop UI: Dropdown Selector      │      │   │
│  │  │  - Year selector (2025, 2026, etc)│      │   │
│  │  │  - Week 1-18 with status badges   │      │   │
│  │  │  - Current week highlighted       │      │   │
│  │  │  - Glow effect on current week    │      │   │
│  │  │  - Auto-scroll to current week    │      │   │
│  │  └─────────────────────────────────────┘      │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────┐      │   │
│  │  │  Mobile UI: Swipeable Carousel      │      │   │
│  │  │  - Swipe left/right between weeks  │      │   │
│  │  │  - Week number display (large)     │      │   │
│  │  │  - Status badge below week         │      │   │
│  │  │  - Metadata display in modal       │      │   │
│  │  └─────────────────────────────────────┘      │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────┐      │   │
│  │  │  Week Metadata Panel                │      │   │
│  │  │  - NFL slate date & kickoff time  │      │   │
│  │  │  - ESPN schedule link             │      │   │
│  │  │  - Data import status             │      │   │
│  │  │  - Import count & timestamp       │      │   │
│  │  │  - Tooltip with details           │      │   │
│  │  └─────────────────────────────────────┘      │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────┐      │   │
│  │  │  Status Badge Component             │      │   │
│  │  │  - Green checkmark (completed)     │      │   │
│  │  │  - Gray dash (pending/upcoming)    │      │   │
│  │  │  - Orange warning (import error)   │      │   │
│  │  └─────────────────────────────────────┘      │   │
│  │                                                 │   │
│  │  State Management (Zustand):                    │   │
│  │  - currentYear                                  │   │
│  │  - currentWeek                                  │   │
│  │  - weeks[] (with metadata)                      │   │
│  │  - selectedWeek (for data import)               │   │
│  │  - weekStatuses                                 │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Week Management Endpoints                      │   │
│  │  - GET /api/weeks?year=2025                    │   │
│  │  - GET /api/weeks/{id}                         │   │
│  │  - GET /api/weeks/{id}/metadata                │   │
│  │  - POST /api/weeks (auto-generate)             │   │
│  │  - PUT /api/weeks/{id}/status                  │   │
│  │  - GET /api/current-week                       │   │
│  │  - GET /api/nfl-schedule                       │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │  Services                                       │   │
│  │                                                 │   │
│  │  WeekManagementService                          │   │
│  │  - create_weeks_for_season()                   │   │
│  │  - get_weeks_by_year()                         │   │
│  │  - update_week_status()                        │   │
│  │  - get_current_week()                          │   │
│  │  - validate_week_immutability()                │   │
│  │                                                 │   │
│  │  NFLScheduleService                             │   │
│  │  - get_nfl_schedule()                          │   │
│  │  - parse_schedule()                            │   │
│  │  - get_week_metadata()                         │   │
│  │  - generate_espn_link()                        │   │
│  │                                                 │   │
│  │  StatusUpdateService                            │   │
│  │  - update_all_statuses()                       │   │
│  │  - determine_week_status()                     │   │
│  │  - apply_manual_overrides()                    │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓ SQLAlchemy ORM
┌─────────────────────────────────────────────────────────┐
│              DATABASE (PostgreSQL)                       │
│                                                          │
│  Tables:                                                │
│  - weeks (extend existing)                              │
│  - week_metadata (new)                                  │
│  - nfl_schedule (new)                                   │
│  - week_status_overrides (new)                          │
│  - player_pools (from Data Import System)               │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (ORM)
- Alembic (migrations)
- python-dateutil (date calculations)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- Material-UI (MUI) v5
- Zustand (state management - reusing existing pattern)
- TanStack Query (data fetching)
- React Swipeable (mobile carousel)

**Database:**
- PostgreSQL 15

---

## Database Schema

### Table: `weeks` (EXTEND EXISTING)

The `weeks` table already exists from the Data Import System. We need to add two new columns:

```sql
ALTER TABLE weeks ADD COLUMN IF NOT EXISTS (
    nfl_slate_date DATE,  -- e.g., 2025-01-05 (Sunday of NFL week)
    status_override VARCHAR(20),  -- Manual override: 'active', 'upcoming', 'completed', or NULL for auto
    metadata JSONB,  -- Store: {kickoff_time, espn_link, slate_start, slate_end}
    is_locked BOOLEAN DEFAULT false,  -- TRUE once player pool data imported
    locked_at TIMESTAMP,  -- When data was imported
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_weeks_nfl_slate_date ON weeks(nfl_slate_date);
CREATE INDEX idx_weeks_is_locked ON weeks(is_locked);
CREATE INDEX idx_weeks_status_override ON weeks(status_override);
```

### Table: `week_metadata` (NEW)

Store rich metadata about each week, including kickoff times and ESPN links:

```sql
CREATE TABLE IF NOT EXISTS week_metadata (
    id SERIAL PRIMARY KEY,
    week_id INTEGER NOT NULL UNIQUE REFERENCES weeks(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK (week_number BETWEEN 1 AND 18),
    nfl_slate_date DATE NOT NULL,  -- Sunday of NFL week
    kickoff_time TIME NOT NULL,  -- e.g., 13:00 (1:00 PM ET)
    slate_start_time TIMESTAMP,  -- When slate games begin
    slate_end_time TIMESTAMP,  -- When last game starts
    espn_schedule_url TEXT,  -- e.g., "https://www.espn.com/nfl/schedule/_/week/9"
    import_status VARCHAR(20) DEFAULT 'pending' CHECK (import_status IN ('pending', 'imported', 'error')),
    import_count INTEGER DEFAULT 0,
    import_timestamp TIMESTAMP,
    import_error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_season_week_metadata UNIQUE (season, week_number)
);

CREATE INDEX idx_week_metadata_week_id ON week_metadata(week_id);
CREATE INDEX idx_week_metadata_nfl_slate_date ON week_metadata(nfl_slate_date);
CREATE INDEX idx_week_metadata_import_status ON week_metadata(import_status);
```

### Table: `nfl_schedule` (NEW)

Store NFL schedule data for dynamic week generation and metadata:

```sql
CREATE TABLE IF NOT EXISTS nfl_schedule (
    id SERIAL PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 18),
    slate_date DATE NOT NULL,
    kickoff_time TIME NOT NULL,
    game_count INTEGER,
    is_playoff BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_season_week_schedule UNIQUE (season, week)
);

CREATE INDEX idx_nfl_schedule_season ON nfl_schedule(season);
CREATE INDEX idx_nfl_schedule_slate_date ON nfl_schedule(slate_date);
```

### Table: `week_status_overrides` (NEW)

Track manual status overrides for weeks (allows overriding auto-status):

```sql
CREATE TABLE IF NOT EXISTS week_status_overrides (
    id SERIAL PRIMARY KEY,
    week_id INTEGER NOT NULL UNIQUE REFERENCES weeks(id) ON DELETE CASCADE,
    override_status VARCHAR(20) NOT NULL CHECK (override_status IN ('active', 'upcoming', 'completed')),
    reason TEXT,
    overridden_by TEXT,  -- User ID or system
    overridden_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_week_status_overrides_week_id ON week_status_overrides(week_id);
```

---

## API Specifications

### 1. Get Weeks by Year

**Endpoint:** `GET /api/weeks`

**Query Parameters:**
- `year` (required): Integer (e.g., 2025, 2026)
- `include_metadata` (optional): Boolean (default: true)

**Response (Success):**
```json
{
  "success": true,
  "year": 2025,
  "weeks": [
    {
      "id": 1,
      "season": 2025,
      "week_number": 1,
      "status": "completed",
      "status_override": null,
      "nfl_slate_date": "2025-09-07",
      "is_locked": true,
      "locked_at": "2025-09-10T14:30:00Z",
      "metadata": {
        "kickoff_time": "13:00",
        "espn_link": "https://www.espn.com/nfl/schedule/_/week/1",
        "slate_start": "2025-09-07T13:00:00Z",
        "import_status": "imported",
        "import_count": 153,
        "import_timestamp": "2025-09-10T14:30:00Z"
      }
    },
    {
      "id": 2,
      "season": 2025,
      "week_number": 2,
      "status": "completed",
      "status_override": null,
      "nfl_slate_date": "2025-09-14",
      "is_locked": false,
      "locked_at": null,
      "metadata": {
        "kickoff_time": "13:00",
        "espn_link": "https://www.espn.com/nfl/schedule/_/week/2",
        "import_status": "pending",
        "import_count": 0,
        "import_timestamp": null
      }
    }
    // ... weeks 3-18
  ],
  "current_week": 5,
  "current_date": "2025-10-05T12:00:00Z"
}
```

**Response (Invalid Year):**
```json
{
  "success": false,
  "error": "Year must be between 2025 and 2030"
}
```

**Processing Logic:**
1. Validate year is current or future year (2025-2030)
2. Check if weeks exist for year in database
3. If not, auto-generate 18 weeks using NFL schedule service
4. Get current date/week and calculate status for each week
5. Apply any manual status overrides
6. Return weeks sorted by week_number with metadata

---

### 2. Get Current Week

**Endpoint:** `GET /api/current-week`

**Response:**
```json
{
  "success": true,
  "current_week": 5,
  "current_date": "2025-10-05T12:00:00Z",
  "week_details": {
    "id": 5,
    "season": 2025,
    "week_number": 5,
    "status": "active",
    "nfl_slate_date": "2025-10-05",
    "metadata": {
      "kickoff_time": "13:00",
      "espn_link": "https://www.espn.com/nfl/schedule/_/week/5",
      "import_status": "imported",
      "import_count": 153
    }
  }
}
```

**Processing Logic:**
1. Get current date/time
2. Query nfl_schedule to determine current week
3. Return week with full metadata
4. Always check for manual status overrides

---

### 3. Get Week Metadata

**Endpoint:** `GET /api/weeks/{id}/metadata`

**Response:**
```json
{
  "success": true,
  "week_id": 5,
  "metadata": {
    "season": 2025,
    "week_number": 5,
    "nfl_slate_date": "2025-10-05",
    "kickoff_time": "13:00",
    "espn_link": "https://www.espn.com/nfl/schedule/_/week/5",
    "import_status": "imported",
    "import_count": 153,
    "import_timestamp": "2025-10-05T14:30:00Z",
    "is_locked": true,
    "locked_at": "2025-10-05T14:30:00Z"
  }
}
```

---

### 4. Update Week Status

**Endpoint:** `PUT /api/weeks/{id}/status`

**Request:**
```json
{
  "status": "active",  // 'active', 'upcoming', 'completed'
  "reason": "Manual override for Week 5"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Week status updated",
  "week": {
    "id": 5,
    "week_number": 5,
    "status": "active",
    "status_override": "active",
    "updated_at": "2025-10-05T15:00:00Z"
  }
}
```

**Processing Logic:**
1. Validate week exists
2. Validate status is valid enum value
3. Create/update week_status_overrides record
4. Return updated week with override info

---

### 5. Auto-Generate Weeks for Season

**Endpoint:** `POST /api/weeks/generate`

**Request:**
```json
{
  "year": 2026,
  "force_regenerate": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "18 weeks generated for 2026",
  "weeks_created": 18,
  "year": 2026
}
```

**Processing Logic:**
1. Validate year is valid
2. Check if weeks already exist for year (skip if exists, unless force_regenerate=true)
3. Fetch NFL schedule for year from nfl_schedule table
4. Generate 18 week records with metadata
5. Return count of created weeks

---

### 6. Get NFL Schedule

**Endpoint:** `GET /api/nfl-schedule`

**Query Parameters:**
- `year` (optional): Integer (default: current year)

**Response:**
```json
{
  "success": true,
  "year": 2025,
  "schedule": [
    {
      "week": 1,
      "slate_date": "2025-09-07",
      "kickoff_time": "13:00",
      "is_playoff": false,
      "game_count": 16
    },
    // ... weeks 2-18
  ]
}
```

**Processing Logic:**
1. Check nfl_schedule table for year
2. If not found, fetch from external NFL API or seed from static data
3. Return all weeks with dates/times

---

### 7. Lock Week (on successful data import)

**Endpoint:** `PUT /api/weeks/{id}/lock`

**Request:**
```json
{
  "import_id": "uuid-string",
  "player_count": 153
}
```

**Response:**
```json
{
  "success": true,
  "message": "Week locked",
  "week": {
    "id": 5,
    "is_locked": true,
    "locked_at": "2025-10-05T14:30:00Z",
    "metadata": {
      "import_status": "imported",
      "import_count": 153,
      "import_timestamp": "2025-10-05T14:30:00Z"
    }
  }
}
```

**Processing Logic:**
1. Validate week_id exists
2. Check no other weeks are locked for this season + week combo
3. Set is_locked = true, locked_at = NOW()
4. Update week_metadata import status and count
5. Return updated week

**Called by:** Data Import System (after successful player pool import)

---

### 8. Update Week Import Status

**Endpoint:** `PUT /api/weeks/{id}/import-status`

**Request:**
```json
{
  "status": "imported",  // 'pending', 'imported', 'error'
  "import_count": 153,
  "import_timestamp": "2025-10-05T14:30:00Z",
  "error_message": null
}
```

**Response:**
```json
{
  "success": true,
  "message": "Import status updated",
  "week": {
    "id": 5,
    "metadata": {
      "import_status": "imported",
      "import_count": 153,
      "import_timestamp": "2025-10-05T14:30:00Z"
    }
  }
}
```

---

## Frontend Components

### 1. WeekSelector Component (ENHANCED)

**Location:** Header (always visible)

**File:** `/frontend/src/components/layout/WeekSelector.tsx`

**Props:**
```typescript
interface WeekSelectorProps {
  onWeekChange?: (week: number) => void;
  showMetadata?: boolean;  // Display metadata in tooltip
}
```

**State (Zustand - existing):**
```typescript
interface WeekState {
  currentWeek: number;
  currentYear: number;
  weeks: Week[];
  setCurrentWeek: (week: number) => void;
  setCurrentYear: (year: number) => void;
  setWeeks: (weeks: Week[]) => void;
  isLoading: boolean;
  error: string | null;
}
```

**Week Data Structure:**
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
  metadata: {
    kickoff_time: string;
    espn_link: string;
    slate_start: string;
    import_status: string;
    import_count: number;
    import_timestamp: string | null;
  };
}
```

**UI Features:**
- Year dropdown selector (2025, 2026, etc.)
- Week 1-18 with Material Design status badges
- Current week highlighted with glow effect
- Auto-scroll to current week when dropdown opens
- Smooth 200ms animation for opening/closing
- Tooltip on hover showing: kickoff time, import count, last import time
- Disabled state for locked weeks (visual feedback, not disabled interaction)

**Responsive Design:**
- Desktop (>960px): Dropdown selector with inline metadata
- Tablet (600-960px): Dropdown selector, metadata in tooltip
- Mobile (<600px): Hidden from header, use carousel instead

---

### 2. WeekCarousel Component (MOBILE)

**Location:** Main content area (mobile only)

**File:** `/frontend/src/components/mobile/WeekCarousel.tsx`

**Props:**
```typescript
interface WeekCarouselProps {
  weeks: Week[];
  currentWeek: number;
  onWeekChange: (week: number) => void;
  showMetadata?: boolean;
}
```

**UI Features:**
- Swipeable horizontal carousel
- Large week number display (font-size: 48px)
- Status badge below week number
- Week metadata in modal on tap
- Smooth swipe animations
- Snap to center on release
- Week range indicator (e.g., "Week 5 of 18")

**Mobile Breakpoint:**
- Activate below 600px viewport width
- Replace WeekSelector in header

---

### 3. WeekMetadataPanel Component

**Location:** Below week selector or in modal (mobile)

**File:** `/frontend/src/components/weeks/WeekMetadataPanel.tsx`

**Props:**
```typescript
interface WeekMetadataPanelProps {
  week: Week;
  isLoading?: boolean;
  compact?: boolean;  // Tooltip vs full panel
}
```

**UI Features:**
- NFL slate date (e.g., "Sunday, Sept 7")
- Kickoff time (e.g., "1:00 PM ET")
- ESPN schedule link (clickable)
- Import status badge (Imported / Pending / Error)
- Import details tooltip:
  - Player count
  - Import timestamp
  - Data source (LineStar, DraftKings)
  - Error message (if error)

**Styling:**
- Dark mode optimized
- Professional sans-serif font
- No colors, Material Design icon colors only
- Subtle hover effects on links

---

### 4. WeekStatusBadge Component

**Location:** Used in selector, carousel, metadata panel

**File:** `/frontend/src/components/weeks/WeekStatusBadge.tsx`

**Props:**
```typescript
interface WeekStatusBadgeProps {
  status: 'active' | 'upcoming' | 'completed';
  importStatus?: 'pending' | 'imported' | 'error';
  isCurrentWeek?: boolean;
  compact?: boolean;
}
```

**UI Features:**
- **Completed:** Green checkmark icon (material-ui CheckCircleIcon)
- **Pending:** Gray dash icon (material-ui RemoveCircleIcon)
- **Error:** Orange warning icon (material-ui WarningIcon)
- **Active week:** Glow effect, brighter appearance
- Material Design styling
- No emojis (strictly icon-based)

---

### 5. YearSelector Component

**Location:** Header, next to week selector

**File:** `/frontend/src/components/layout/YearSelector.tsx`

**Props:**
```typescript
interface YearSelectorProps {
  currentYear: number;
  onYearChange: (year: number) => void;
  availableYears?: number[];  // e.g., [2025, 2026, 2027]
}
```

**UI Features:**
- Dropdown selector with 2025-2030
- Current year highlighted
- Loads weeks when year changes
- Shows loading state while fetching
- Smooth transition animation

---

## UI/UX Design

### Design Principles

1. **Modern & Sleek**: Flat design, subtle shadows, smooth animations
2. **Dark Mode Optimized**: Primary usage is dark theme
3. **Professional**: Clean typography, proper spacing, no decorative elements
4. **Material Design**: Strict adherence to Material Design v5
5. **No Emojis**: Professional appearance, icon-based status indicators
6. **Accessibility**: WCAG 2.1 AA compliance, proper color contrast

### Color Palette

```
Primary: #1976d2 (Material Blue)
Secondary: #dc004e (Material Pink)
Background Dark: #121212
Surface Dark: #1e1e1e
Success: #4caf50 (Material Green)
Warning: #ff9800 (Material Orange)
Error: #f44336 (Material Red)
Text Primary: #ffffff
Text Secondary: #b0bec5
Divider: #424242
```

### Typography

```
Display Large: 57px, 64px line-height, -0.25px tracking
Display Medium: 45px, 52px line-height, 0px tracking
Display Small: 36px, 44px line-height, 0px tracking
Headline Large: 32px, 40px line-height, 0px tracking
Headline Medium: 28px, 36px line-height, 0px tracking
Headline Small: 24px, 32px line-height, 0px tracking
Title Large: 22px, 28px line-height, 0px tracking
Title Medium: 16px, 24px line-height, 0.15px tracking
Title Small: 14px, 20px line-height, 0.1px tracking
Body Large: 16px, 24px line-height, 0.5px tracking
Body Medium: 14px, 20px line-height, 0.25px tracking
Body Small: 12px, 16px line-height, 0.4px tracking
```

### Spacing

```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
xxl: 48px
```

### Animations

```
Dropdown open/close: 200ms ease-out
Status badge fade: 150ms ease-in-out
Glow effect: 2s ease-in-out (continuous for active week)
Carousel swipe: 300ms cubic-bezier(0.33, 0.66, 0.66, 1)
```

### Dark Mode Specifics

- Background: Very dark (#121212)
- Surface elevation: Use subtle shadows instead of color
- Text: High contrast white on dark
- Accent colors: Slightly muted to prevent eye strain
- Borders: Subtle divider color (#424242)

### Responsive Breakpoints

```
xs: 0px - 360px (small mobile)
sm: 361px - 600px (mobile)
md: 601px - 960px (tablet)
lg: 961px - 1280px (desktop)
xl: 1281px+ (large desktop)
```

**Component Visibility by Breakpoint:**
```
WeekSelector (dropdown): md and up
WeekCarousel (swipeable): xs, sm only
YearSelector: md and up (inline with WeekSelector)
WeekMetadataPanel: md and up (inline or tooltip)
WeekMetadataModal: xs, sm only (full-screen on tap)
```

---

## State Management

### Zustand Store Structure

**File:** `/frontend/src/store/weekStore.ts`

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

interface WeekMetadata {
  kickoff_time: string;
  espn_link: string;
  slate_start: string;
  import_status: 'pending' | 'imported' | 'error';
  import_count: number;
  import_timestamp: string | null;
  error_message?: string;
}

interface WeekState {
  // Current selections
  currentYear: number;
  currentWeek: number;

  // Data
  weeks: Week[];
  availableYears: number[];

  // UI state
  isLoading: boolean;
  error: string | null;
  selectedWeekForImport: number | null;

  // Actions
  setCurrentYear: (year: number) => void;
  setCurrentWeek: (week: number) => void;
  setWeeks: (weeks: Week[]) => void;
  setAvailableYears: (years: number[]) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSelectedWeekForImport: (week: number | null) => void;

  // Computed
  getCurrentWeekData: () => Week | null;
  getWeekById: (id: number) => Week | null;
  getWeekByNumber: (number: number) => Week | null;
  getWeeksByStatus: (status: string) => Week[];
}
```

### TanStack Query Hooks

**File:** `/frontend/src/hooks/useWeeks.ts`

```typescript
// Fetch weeks for selected year
const useWeeks = (year: number) => {
  return useQuery({
    queryKey: ['weeks', year],
    queryFn: () => api.get(`/api/weeks?year=${year}&include_metadata=true`),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    cacheTime: 10 * 60 * 1000,  // 10 minutes
  });
};

// Get current week
const useCurrentWeek = () => {
  return useQuery({
    queryKey: ['current-week'],
    queryFn: () => api.get('/api/current-week'),
    refetchInterval: 60 * 1000,  // Refresh every minute
  });
};

// Get week metadata (detailed)
const useWeekMetadata = (weekId: number) => {
  return useQuery({
    queryKey: ['week-metadata', weekId],
    queryFn: () => api.get(`/api/weeks/${weekId}/metadata`),
    enabled: !!weekId,
  });
};
```

### Integration with Data Import System

When data is imported successfully:
1. Backend calls `PUT /api/weeks/{week_id}/lock`
2. Frontend receives updated week with `is_locked=true`
3. Zustand store updates week in weeks array
4. UI reflects locked state (visual feedback)
5. Week selector prevents selection change (optional UX decision)

---

## Data Flow

### Week Selection Flow

```
User selects year in YearSelector
  ↓
Zustand action: setCurrentYear(year)
  ↓
useWeeks hook triggered with new year
  ↓
GET /api/weeks?year={year}
  ↓
Backend queries weeks table, enriches with metadata
  ↓
Response includes all 18 weeks + current week calculation
  ↓
Zustand updates weeks array
  ↓
Components re-render with new week data
  ↓
Desktop: WeekSelector shows all weeks
Mobile: WeekCarousel shows weeks
```

### Week Change Flow

```
User clicks/swipes to different week
  ↓
Zustand action: setCurrentWeek(week_number)
  ↓
localStorage updated (persist middleware)
  ↓
Zustand selector updates: selectedWeekForImport
  ↓
Components re-render:
  - Header shows new week
  - Metadata panel updates
  - Player pool context updates (if using React Context)
  ↓
Data Import System uses selectedWeekForImport for imports
```

### Import Status Update Flow

```
User imports data via ImportDataButton
  ↓
POST /api/import/{type} with week_id
  ↓
Backend processes import
  ↓
On success: PUT /api/weeks/{week_id}/lock
  ↓
Backend updates week: is_locked=true, metadata.import_status='imported'
  ↓
Response includes updated week object
  ↓
Frontend receives success response with week data
  ↓
Zustand update: setWeeks() with updated week
  ↓
WeekStatusBadge re-renders with new import_status
  ↓
User sees green checkmark in week selector
  ↓
Optional: Toast notification "Week 5 data imported"
```

### Current Week Auto-Detection Flow

```
Page loads / Every 60 seconds
  ↓
useCurrentWeek hook executes
  ↓
GET /api/current-week
  ↓
Backend:
  1. Get current date/time
  2. Query nfl_schedule for week
  3. Check for status overrides
  4. Return current week + details
  ↓
Frontend:
  1. Compare returned current_week to Zustand currentWeek
  2. If different: setCurrentWeek(current_week)
  3. Highlight current week in selector/carousel
  4. Apply glow effect
  ↓
Components re-render with current week highlighting
```

---

## Mobile Considerations

### Mobile UX Patterns

**Option 1: Swipeable Carousel (RECOMMENDED)**
- Full-screen carousel on mobile
- Week number large and centered
- Status badge directly below
- Metadata in full-screen modal on tap
- Swipe left/right to move between weeks
- Tap to open detailed metadata modal

**Option 2: Bottom Sheet Modal**
- Fixed bottom bar showing current week
- Tap to open bottom sheet with all weeks
- Scrollable week list
- Select week to close sheet and navigate

**Recommended:** Option 1 (swipeable carousel) - most modern, intuitive UX

### Touch Interactions

```
Swipe left: Next week
Swipe right: Previous week
Swipe velocity: Fast swipe = multiple weeks
Tap on week: Open metadata modal
Tap on ESPN link: Open in new tab
Long press: Copy week metadata (optional)
Double tap: Return to current week (optional)
```

### Performance Optimizations

- Lazy load week metadata only when needed
- Virtualize carousel for smooth 60fps
- Preload 2 adjacent weeks images/data
- Use React.memo for week cards
- Debounce swipe handlers (100ms)

### Responsive Images/Icons

- Use SVG icons (scale without quality loss)
- Material-UI icons are SVG-based (perfect)
- No raster images for week status
- Responsive font sizes using MUI `sx` prop

### Touch-Friendly Sizing

- Minimum tap target: 44x44px
- Padding around interactive elements: 8px
- Spacing between weeks in carousel: 16px

---

## Validation Rules

### Week Validation

```python
def validate_week(week: int) -> None:
    """Validate week number."""
    if not isinstance(week, int):
        raise ValueError("Week must be an integer")
    if not (1 <= week <= 18):
        raise ValueError("Week must be between 1 and 18")

def validate_year(year: int) -> None:
    """Validate season year."""
    if not isinstance(year, int):
        raise ValueError("Year must be an integer")
    current_year = datetime.now().year
    if not (current_year <= year <= current_year + 5):
        raise ValueError(f"Year must be between {current_year} and {current_year + 5}")

def validate_status(status: str) -> None:
    """Validate week status."""
    valid_statuses = ['active', 'upcoming', 'completed']
    if status not in valid_statuses:
        raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

def validate_week_immutability(week: Week) -> None:
    """Prevent editing locked weeks."""
    if week.is_locked:
        raise ValidationError(
            f"Week {week.week_number} is locked. Cannot modify weeks with imported data."
        )
```

### Frontend Validation

```typescript
// Week selector validation
const isValidWeek = (week: number): boolean => {
  return Number.isInteger(week) && week >= 1 && week <= 18;
};

// Year selector validation
const isValidYear = (year: number): boolean => {
  const currentYear = new Date().getFullYear();
  return year >= currentYear && year <= currentYear + 5;
};

// Status badge can only show valid statuses
const VALID_STATUSES = ['active', 'upcoming', 'completed'] as const;
type WeekStatus = typeof VALID_STATUSES[number];
```

---

## Error Handling

### Backend Error Cases

```python
class WeekNotFoundError(CortexException):
    """Raised when week doesn't exist."""
    def __init__(self, week_id: int):
        super().__init__(
            f"Week {week_id} not found",
            status_code=404
        )

class WeekLockedError(CortexException):
    """Raised when trying to edit locked week."""
    def __init__(self, week_number: int):
        super().__init__(
            f"Week {week_number} is locked due to imported data. "
            f"Cannot modify weeks with imported player pools.",
            status_code=409
        )

class InvalidYearError(CortexException):
    """Raised when year is invalid."""
    def __init__(self, year: int):
        super().__init__(
            f"Year {year} is invalid. Must be between 2025 and 2030.",
            status_code=400
        )

class NFLScheduleError(CortexException):
    """Raised when NFL schedule cannot be loaded."""
    def __init__(self):
        super().__init__(
            "Failed to load NFL schedule. Please try again.",
            status_code=500
        )
```

### Frontend Error Handling

```typescript
// Generic error handler for week queries
const handleWeekError = (error: any) => {
  if (error.status === 404) {
    return "Week not found";
  } else if (error.status === 409) {
    return "This week is locked and cannot be modified";
  } else if (error.status === 400) {
    return "Invalid year selection";
  } else {
    return "Failed to load weeks. Please refresh and try again.";
  }
};

// Show error toast to user
const { enqueueSnackbar } = useSnackbar();
queryClient.setQueryData(['weeks', year], undefined);
enqueueSnackbar(handleWeekError(error), { variant: 'error' });
```

### Error Recovery

1. **Automatic retry** on network errors (3 attempts with exponential backoff)
2. **Graceful degradation** if week metadata unavailable (show basic info)
3. **Fallback data** from localStorage if API fails
4. **User-friendly messages** always (never show stack traces)

---

## Integration Points

### Data Import System Integration

**When user initiates import:**
1. Data Import System reads selected week from Zustand: `useWeekStore().currentWeek`
2. User uploads file matching selected week
3. Week mismatch detected → show WeekMismatchDialog
4. User confirms import → backend processes data

**When import completes successfully:**
1. Backend calls `PUT /api/weeks/{week_id}/lock`
2. Zustand store updates week with `is_locked=true`
3. WeekSelector shows locked state (visual feedback)
4. Week becomes immutable

**When import fails:**
1. Backend updates `week_metadata.import_status='error'`
2. Backend stores error message in `import_error_message`
3. Zustand updates week with error status
4. WeekStatusBadge shows orange warning icon
5. Tooltip shows error message

### Player Pool Context

Week selection should update global player pool context:

```typescript
// Example: usePlayerPool hook
const usePlayerPool = () => {
  const { currentWeek } = useWeekStore();

  const { data: playerPool } = useQuery({
    queryKey: ['player-pool', currentWeek],
    queryFn: () => api.get(`/api/player-pools?week_id=${currentWeek}`),
    enabled: !!currentWeek && playerPoolExists(currentWeek),
  });

  return { playerPool };
};
```

### Lineup History Integration (Phase 2)

In Phase 2, when replay weeks feature added:
- Locked weeks allow viewing historical lineups
- Button: "View History" appears on locked weeks
- Clicking loads historical lineup data
- Cannot edit, only view

---

## Implementation Plan

### Phase 1: Database & Backend Setup (3 hours)

**Tasks:**
1. Create Alembic migration for new tables:
   - week_metadata
   - nfl_schedule
   - week_status_overrides
2. Extend weeks table with new columns
3. Seed nfl_schedule data for 2025-2030
4. Run migrations locally
5. Verify schema with psql

**Deliverables:**
- `alembic/versions/002_extend_weeks_system.py`
- All new tables created in PostgreSQL
- nfl_schedule populated with correct dates

---

### Phase 2: Backend Services (2.5 hours)

**Tasks:**
1. Implement WeekManagementService
   - `create_weeks_for_season()`
   - `get_weeks_by_year()`
   - `update_week_status()`
   - `get_current_week()`
   - `validate_week_immutability()`
   - `lock_week()` (called from import system)

2. Implement StatusUpdateService
   - `determine_week_status()` (auto-calculate based on date)
   - `update_all_statuses()` (periodic task)
   - `apply_manual_overrides()`

3. Implement NFLScheduleService
   - `get_nfl_schedule()`
   - `get_week_metadata()`
   - `generate_espn_link()`

**Deliverables:**
- `services/week_management_service.py`
- `services/status_update_service.py`
- `services/nfl_schedule_service.py`

---

### Phase 3: Backend API Endpoints (2 hours)

**Tasks:**
1. Create week router
2. Implement all 8 API endpoints
3. Add request validation with Pydantic
4. Add response serialization
5. Add error handling

**Deliverables:**
- `routers/week_router.py`
- All endpoints documented with docstrings
- Proper error responses

---

### Phase 4: Frontend State & Hooks (1.5 hours)

**Tasks:**
1. Enhance Zustand weekStore
2. Create useWeeks hook
3. Create useCurrentWeek hook
4. Create useWeekMetadata hook
5. Create useWeekSelection hook

**Deliverables:**
- `store/weekStore.ts` (enhanced)
- `hooks/useWeeks.ts`
- `hooks/useCurrentWeek.ts`
- `hooks/useWeekMetadata.ts`

---

### Phase 5: Frontend Components (2 hours)

**Tasks:**
1. Enhance WeekSelector component
2. Create YearSelector component
3. Create WeekCarousel component (mobile)
4. Create WeekMetadataPanel component
5. Create WeekStatusBadge component
6. Create WeekMetadataModal component

**Deliverables:**
- All components in `/frontend/src/components/`
- Responsive CSS/sx styling
- Dark mode optimized

---

### Phase 6: Integration & Polish (1 hour)

**Tasks:**
1. Integrate week management with import system
2. Test week locking on import
3. Test status badge updates
4. Test mobile carousel
5. Polish animations and transitions

**Deliverables:**
- All systems integrated
- Smooth user experience
- Performance optimized

---

### Phase 7: Testing (1 hour)

**Tasks:**
1. Unit tests for services
2. Integration tests for API endpoints
3. Component tests for React components
4. E2E tests for key workflows
5. Mobile testing on real devices

**Deliverables:**
- Test files created
- All tests passing
- >80% code coverage

---

## Test Cases

### Test Case 1: Load Weeks for Year

**Setup:**
- Backend has weeks in database for 2025

**Steps:**
1. Frontend loads
2. YearSelector defaults to current year (2025)
3. useWeeks hook triggers

**Expected Result:**
- 18 weeks loaded for 2025
- Current week highlighted
- All metadata loaded
- Status badges correct

---

### Test Case 2: Auto-Status Update

**Setup:**
- Week 5 nfl_slate_date = 2025-10-05 (past)
- Week 6 nfl_slate_date = 2025-10-12 (future)
- Current date = 2025-10-08

**Steps:**
1. GET /api/current-week

**Expected Result:**
- Week 5 status = 'completed'
- Week 6 status = 'upcoming'
- Correct current week identified

---

### Test Case 3: Week Selection

**Setup:**
- WeekSelector loaded
- Current week = 1

**Steps:**
1. Click Week 5 in dropdown

**Expected Result:**
- Zustand currentWeek = 5
- localStorage updated
- WeekMetadataPanel shows Week 5 metadata
- Glow effect moves to Week 5

---

### Test Case 4: Mobile Carousel Navigation

**Setup:**
- Mobile viewport (375px)
- WeekCarousel loaded
- Current week = 5

**Steps:**
1. Swipe left
2. Swipe right
3. Tap on week metadata area

**Expected Result:**
- Swipe left shows Week 6
- Swipe right shows Week 4
- Tap opens metadata modal
- Modal shows all details

---

### Test Case 5: Data Import Lock

**Setup:**
- Week 5 not locked
- Data imported for Week 5
- Backend calls `PUT /api/weeks/5/lock`

**Expected Result:**
- Week 5 is_locked = true
- WeekStatusBadge shows green checkmark
- WeekSelector disables editing (optional)
- Tooltip shows import details

---

### Test Case 6: Locked Week Cannot Be Modified

**Setup:**
- Week 5 locked with imported data

**Steps:**
1. Attempt to DELETE /api/weeks/5

**Expected Result:**
- 409 Conflict response
- Error message: "Week 5 is locked..."
- Week remains unchanged

---

### Test Case 7: Manual Status Override

**Setup:**
- Week 5 auto-status = 'upcoming'
- System should mark Week 5 as 'active'

**Steps:**
1. PUT /api/weeks/5/status with {"status": "active"}

**Expected Result:**
- Week 5 status_override = 'active'
- GET /api/weeks returns status = 'active'
- Override persists across page reloads

---

### Test Case 8: Year Selection

**Setup:**
- Current year = 2025
- User wants to plan for 2026

**Steps:**
1. Select 2026 from YearSelector
2. Wait for loading

**Expected Result:**
- useWeeks hook fetches weeks for 2026
- 18 weeks displayed for 2026
- localStorage updated with selected year
- Persists across page reloads

---

## Acceptance Criteria

### Must Have (MVP)

1. **Week Management**
   - Auto-generate 18 weeks for NFL season
   - Support multiple years (2025-2030)
   - Dynamic week creation based on NFL calendar (not hardcoded)
   - Persist selected week in localStorage

2. **Status Management**
   - Auto-status update: Active = current, Upcoming = future, Completed = past
   - Status based on current date vs nfl_slate_date
   - Allow manual override with reason tracking
   - Update on page load and every 60 seconds

3. **Week Selection UI**
   - Desktop: Material Design dropdown selector
   - Mobile: Swipeable carousel with week cards
   - Current week highlighted with glow effect
   - Year selector for future seasons
   - Responsive across all breakpoints

4. **Metadata Display**
   - NFL slate date formatted (e.g., "Sunday, Sept 7")
   - Kickoff time displayed (e.g., "1:00 PM ET")
   - ESPN schedule link clickable
   - Import status badge (green/gray/orange)
   - Tooltip with import details

5. **Status Indicators**
   - Green checkmark for completed weeks
   - Gray dash for pending weeks
   - Orange warning for import errors
   - Material Design icons only
   - Professional appearance, no emojis

6. **Data Immutability**
   - Lock weeks once player pool imported
   - Prevent editing/deleting locked weeks
   - Visual feedback that week is locked
   - Cannot be unlocked by user

7. **Integration**
   - Works with Data Import System
   - Updates on successful import
   - Shows import count in metadata
   - Displays import timestamp
   - Shows error message if import failed

8. **Responsive Design**
   - Desktop (>960px): Dropdown selector
   - Mobile (<600px): Swipeable carousel
   - Dark mode optimized
   - Material Design v5 compliance
   - Touch-friendly targets (44x44px min)

9. **Performance**
   - Dropdown opens <200ms
   - Week data loads <500ms
   - Smooth carousel swipes (60fps)
   - No layout shift on data load

10. **Dark Mode**
    - Tested and optimized for dark theme
    - Proper contrast ratios (WCAG AA)
    - No harsh colors
    - Readable in low light

---

## Out of Scope (Phase 2+)

- Replay weeks / view historical lineups
- Calendar view of season
- Vegas line integration
- Automated week generation from external API
- Week-to-week comparison stats
- Advanced filtering by week status
- Bulk status operations
- Week templates for recurring setups

---

## Appendix

### NFL Schedule Seed Data

```python
NFL_SCHEDULE_2025 = [
    {"week": 1, "slate_date": "2025-09-07", "kickoff_time": "13:00", "game_count": 16},
    {"week": 2, "slate_date": "2025-09-14", "kickoff_time": "13:00", "game_count": 16},
    {"week": 3, "slate_date": "2025-09-21", "kickoff_time": "13:00", "game_count": 16},
    {"week": 4, "slate_date": "2025-09-28", "kickoff_time": "13:00", "game_count": 16},
    {"week": 5, "slate_date": "2025-10-05", "kickoff_time": "13:00", "game_count": 16},
    {"week": 6, "slate_date": "2025-10-12", "kickoff_time": "13:00", "game_count": 16},
    {"week": 7, "slate_date": "2025-10-19", "kickoff_time": "13:00", "game_count": 16},
    {"week": 8, "slate_date": "2025-10-26", "kickoff_time": "13:00", "game_count": 16},
    {"week": 9, "slate_date": "2025-11-02", "kickoff_time": "13:00", "game_count": 16},
    {"week": 10, "slate_date": "2025-11-09", "kickoff_time": "13:00", "game_count": 16},
    {"week": 11, "slate_date": "2025-11-16", "kickoff_time": "13:00", "game_count": 16},
    {"week": 12, "slate_date": "2025-11-23", "kickoff_time": "12:30", "game_count": 16},  # Thanksgiving
    {"week": 13, "slate_date": "2025-11-30", "kickoff_time": "13:00", "game_count": 16},
    {"week": 14, "slate_date": "2025-12-07", "kickoff_time": "13:00", "game_count": 16},
    {"week": 15, "slate_date": "2025-12-14", "kickoff_time": "13:00", "game_count": 16},
    {"week": 16, "slate_date": "2025-12-21", "kickoff_time": "13:00", "game_count": 16},
    {"week": 17, "slate_date": "2025-12-28", "kickoff_time": "13:00", "game_count": 16},
    {"week": 18, "slate_date": "2026-01-04", "kickoff_time": "13:00", "game_count": 16},
]
```

### ESPN Schedule Link Generator

```python
def generate_espn_link(week: int, year: int) -> str:
    """
    Generate ESPN schedule link for week.

    Example: https://www.espn.com/nfl/schedule/_/week/5/year/2025
    """
    return f"https://www.espn.com/nfl/schedule/_/week/{week}/year/{year}"
```

### Date Formatting Utility

```typescript
export const formatNFLDate = (dateStr: string): string => {
  /**
   * Format NFL slate date to readable format.
   * Input: "2025-09-07"
   * Output: "Sunday, September 7"
   */
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
};

export const formatKickoffTime = (timeStr: string): string => {
  /**
   * Format kickoff time to readable format.
   * Input: "13:00"
   * Output: "1:00 PM ET"
   */
  const [hours, minutes] = timeStr.split(':');
  const date = new Date();
  date.setHours(parseInt(hours), parseInt(minutes));
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
    timeZone: 'America/New_York',
  });
};
```

### Keyboard Navigation

Implement keyboard support for accessibility:

```
Arrow Right: Next week
Arrow Left: Previous week
Tab: Focus next focusable element
Shift+Tab: Focus previous element
Enter: Open week metadata modal
Escape: Close dropdown/modal
Home: Jump to week 1
End: Jump to week 18
Number keys (1-9): Jump to week (1=W1, 9=W9, 0=W10-18 cycle)
```

### Mobile Touch Gestures

- **Swipe left:** Next week
- **Swipe right:** Previous week
- **Tap:** Select/open details
- **Long press:** Copy week info (optional)
- **Double tap:** Jump to current week
- **Pinch zoom:** (disable - not needed)

---

**End of Specification**

**Status:** Ready for Implementation
**Next Step:** Run Phase 1 implementation (database setup)
