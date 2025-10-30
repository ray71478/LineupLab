# Week Management - Code Snippets Reference

This document provides reusable code snippets referenced throughout the specification.

All of these snippets are documented in detail in `spec.md` and are ready to be implemented.

---

## Backend Code Snippets

### 1. Database Models (SQLAlchemy)

**File:** `backend/models/week.py`

```python
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, Boolean, JSONB, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Week(Base):
    __tablename__ = "weeks"
    
    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False, check("week_number BETWEEN 1 AND 18"))
    status = Column(String(20), default='upcoming')
    status_override = Column(String(20), nullable=True)
    nfl_slate_date = Column(Date, nullable=True)
    is_locked = Column(Boolean, default=False)
    locked_at = Column(DateTime, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('season', 'week_number', name='unique_season_week'),
    )

class WeekMetadata(Base):
    __tablename__ = "week_metadata"
    
    id = Column(Integer, primary_key=True)
    week_id = Column(Integer, ForeignKey('weeks.id'), nullable=False, unique=True)
    season = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    nfl_slate_date = Column(Date, nullable=False)
    kickoff_time = Column(Time, nullable=False)
    slate_start_time = Column(DateTime, nullable=True)
    slate_end_time = Column(DateTime, nullable=True)
    espn_schedule_url = Column(Text, nullable=True)
    import_status = Column(String(20), default='pending')
    import_count = Column(Integer, default=0)
    import_timestamp = Column(DateTime, nullable=True)
    import_error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NFLSchedule(Base):
    __tablename__ = "nfl_schedule"
    
    id = Column(Integer, primary_key=True)
    season = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False, check("week BETWEEN 1 AND 18"))
    slate_date = Column(Date, nullable=False)
    kickoff_time = Column(Time, nullable=False)
    game_count = Column(Integer, nullable=True)
    is_playoff = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('season', 'week', name='unique_season_week_schedule'),
    )
```

### 2. Validation Service

**File:** `backend/services/validation_service.py`

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

### 3. Week Management Service

**File:** `backend/services/week_management_service.py`

```python
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session

class WeekManagementService:
    
    @staticmethod
    def get_weeks_by_year(session: Session, year: int) -> List[Week]:
        """Get all weeks for a given year."""
        validate_year(year)
        
        weeks = session.execute(
            select(Week).where(Week.season == year).order_by(Week.week_number)
        ).scalars().all()
        
        if not weeks:
            # Auto-generate weeks if not exist
            WeekManagementService.create_weeks_for_season(session, year)
            weeks = session.execute(
                select(Week).where(Week.season == year).order_by(Week.week_number)
            ).scalars().all()
        
        return weeks
    
    @staticmethod
    def determine_week_status(nfl_slate_date: date, status_override: Optional[str] = None) -> str:
        """Determine week status based on current date."""
        if status_override:
            return status_override
        
        today = date.today()
        
        if nfl_slate_date < today:
            return 'completed'
        elif nfl_slate_date == today:
            return 'active'
        else:
            return 'upcoming'
    
    @staticmethod
    def get_current_week(session: Session) -> Week:
        """Get current week based on today's date."""
        today = date.today()
        
        # Find week where nfl_slate_date matches today
        current_week = session.execute(
            select(Week).where(Week.nfl_slate_date == today)
        ).scalar_one_or_none()
        
        if current_week:
            return current_week
        
        # If no exact match, find week in current season
        current_year = today.year
        weeks = session.execute(
            select(Week)
            .where(Week.season == current_year)
            .order_by(Week.nfl_slate_date)
        ).scalars().all()
        
        for week in weeks:
            if week.nfl_slate_date >= today:
                return week
        
        # Fallback: return last week of current season
        return weeks[-1] if weeks else None
    
    @staticmethod
    def lock_week(session: Session, week_id: int, import_id: str, player_count: int) -> Week:
        """Lock week when data is imported."""
        week = session.get(Week, week_id)
        if not week:
            raise WeekNotFoundError(week_id)
        
        week.is_locked = True
        week.locked_at = datetime.utcnow()
        
        # Update metadata
        metadata = session.execute(
            select(WeekMetadata).where(WeekMetadata.week_id == week_id)
        ).scalar_one_or_none()
        
        if metadata:
            metadata.import_status = 'imported'
            metadata.import_count = player_count
            metadata.import_timestamp = datetime.utcnow()
        
        session.commit()
        return week
```

### 4. NFL Schedule Service

**File:** `backend/services/nfl_schedule_service.py`

```python
class NFLScheduleService:
    
    NFL_SCHEDULE_2025 = [
        {"week": 1, "slate_date": "2025-09-07", "kickoff_time": "13:00"},
        {"week": 2, "slate_date": "2025-09-14", "kickoff_time": "13:00"},
        # ... additional weeks
    ]
    
    @staticmethod
    def generate_espn_link(week: int, year: int) -> str:
        """Generate ESPN schedule link."""
        return f"https://www.espn.com/nfl/schedule/_/week/{week}/year/{year}"
    
    @staticmethod
    def get_nfl_schedule(session: Session, year: int) -> List[dict]:
        """Get NFL schedule for year."""
        schedule = session.execute(
            select(NFLSchedule).where(NFLSchedule.season == year).order_by(NFLSchedule.week)
        ).scalars().all()
        
        if not schedule:
            # Seed schedule if not exists
            NFLScheduleService.seed_schedule(session, year)
            schedule = session.execute(
                select(NFLSchedule).where(NFLSchedule.season == year).order_by(NFLSchedule.week)
            ).scalars().all()
        
        return [
            {
                "week": s.week,
                "slate_date": str(s.slate_date),
                "kickoff_time": str(s.kickoff_time),
                "is_playoff": s.is_playoff
            }
            for s in schedule
        ]
```

---

## Frontend Code Snippets

### 1. Zustand Store (Enhanced)

**File:** `frontend/src/store/weekStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Week {
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
    import_status: string;
    import_count: number;
    import_timestamp: string | null;
  };
}

export interface WeekState {
  // Current selections
  currentYear: number;
  currentWeek: number;
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
}

export const useWeekStore = create<WeekState>()(
  persist(
    (set, get) => ({
      currentYear: new Date().getFullYear(),
      currentWeek: 1,
      weeks: [],
      availableYears: [2025, 2026, 2027, 2028, 2029, 2030],
      isLoading: false,
      error: null,
      selectedWeekForImport: null,
      
      setCurrentYear: (year: number) => set({ currentYear: year }),
      setCurrentWeek: (week: number) => {
        if (week >= 1 && week <= 18) {
          set({ currentWeek: week, selectedWeekForImport: week });
        }
      },
      setWeeks: (weeks: Week[]) => set({ weeks }),
      setAvailableYears: (years: number[]) => set({ availableYears: years }),
      setIsLoading: (loading: boolean) => set({ isLoading: loading }),
      setError: (error: string | null) => set({ error }),
      setSelectedWeekForImport: (week: number | null) => set({ selectedWeekForImport: week }),
      
      getCurrentWeekData: () => {
        const { weeks, currentWeek } = get();
        return weeks.find(w => w.week_number === currentWeek) || null;
      },
      
      getWeekById: (id: number) => {
        const { weeks } = get();
        return weeks.find(w => w.id === id) || null;
      },
    }),
    {
      name: 'week-store',
      version: 1,
    }
  )
);
```

### 2. Date Formatting Utilities

**File:** `frontend/src/utils/dateFormatting.ts`

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

### 3. useWeeks Hook

**File:** `frontend/src/hooks/useWeeks.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { useWeekStore } from '../store/weekStore';

export const useWeeks = (year: number) => {
  const { setWeeks, setIsLoading, setError } = useWeekStore();
  
  return useQuery({
    queryKey: ['weeks', year],
    queryFn: async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/weeks?year=${year}&include_metadata=true`);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to load weeks');
        }
        
        setWeeks(data.weeks);
        setError(null);
        return data;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        setError(message);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useCurrentWeek = () => {
  return useQuery({
    queryKey: ['current-week'],
    queryFn: async () => {
      const response = await fetch('/api/current-week');
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to load current week');
      }
      
      return data;
    },
    refetchInterval: 60 * 1000, // Refresh every minute
  });
};
```

### 4. WeekStatusBadge Component

**File:** `frontend/src/components/weeks/WeekStatusBadge.tsx`

```typescript
import React from 'react';
import {
  Box,
  Chip,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import WarningIcon from '@mui/icons-material/Warning';

interface WeekStatusBadgeProps {
  status: 'active' | 'upcoming' | 'completed';
  importStatus?: 'pending' | 'imported' | 'error';
  isCurrentWeek?: boolean;
  compact?: boolean;
}

export const WeekStatusBadge: React.FC<WeekStatusBadgeProps> = ({
  status,
  importStatus,
  isCurrentWeek,
  compact = false,
}) => {
  const theme = useTheme();
  
  const getIcon = () => {
    if (importStatus === 'imported' || status === 'completed') {
      return <CheckCircleIcon />;
    }
    if (importStatus === 'error') {
      return <WarningIcon />;
    }
    return <RemoveCircleIcon />;
  };
  
  const getColor = () => {
    if (importStatus === 'imported' || status === 'completed') {
      return theme.palette.success.main;
    }
    if (importStatus === 'error') {
      return theme.palette.warning.main;
    }
    return theme.palette.action.disabled;
  };
  
  const sx = isCurrentWeek ? {
    boxShadow: `0 0 8px ${alpha(getColor(), 0.5)}`,
    animation: 'glow 2s ease-in-out infinite',
    '@keyframes glow': {
      '0%, 100%': {
        boxShadow: `0 0 8px ${alpha(getColor(), 0.5)}`,
      },
      '50%': {
        boxShadow: `0 0 16px ${alpha(getColor(), 0.8)}`,
      },
    },
  } : {};
  
  return (
    <Tooltip title={`${status.charAt(0).toUpperCase() + status.slice(1)} week`}>
      <Box sx={sx}>
        {getIcon()}
      </Box>
    </Tooltip>
  );
};
```

---

## API Response Examples

### Get Weeks Response

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
        "import_status": "imported",
        "import_count": 153,
        "import_timestamp": "2025-09-10T14:30:00Z"
      }
    }
  ],
  "current_week": 5,
  "current_date": "2025-10-05T12:00:00Z"
}
```

### Lock Week Request/Response

```
PUT /api/weeks/5/lock

Request:
{
  "import_id": "uuid-string",
  "player_count": 153
}

Response:
{
  "success": true,
  "week": {
    "id": 5,
    "week_number": 5,
    "is_locked": true,
    "locked_at": "2025-10-05T14:30:00Z",
    "metadata": {
      "import_status": "imported",
      "import_count": 153
    }
  }
}
```

---

## Database Migration (Alembic)

**File:** `backend/alembic/versions/002_extend_weeks_system.py`

```python
"""Extend weeks system with metadata and schedule.

Revision ID: 002
Revises: 001
Create Date: 2025-10-27 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to weeks table
    op.add_column('weeks', sa.Column('nfl_slate_date', sa.Date(), nullable=True))
    op.add_column('weeks', sa.Column('status_override', sa.String(20), nullable=True))
    op.add_column('weeks', sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('weeks', sa.Column('locked_at', sa.DateTime(), nullable=True))
    op.add_column('weeks', sa.Column('metadata', postgresql.JSONB(), nullable=True))
    
    # Create week_metadata table
    op.create_table(
        'week_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('week_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('nfl_slate_date', sa.Date(), nullable=False),
        sa.Column('kickoff_time', sa.Time(), nullable=False),
        sa.Column('espn_schedule_url', sa.Text(), nullable=True),
        sa.Column('import_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('import_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('import_timestamp', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['week_id'], ['weeks.id'], name='fk_week_metadata_week'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('week_id', name='uq_week_metadata_week_id'),
        sa.UniqueConstraint('season', 'week_number', name='uq_week_metadata_season_week')
    )
    
    # Create nfl_schedule table
    op.create_table(
        'nfl_schedule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('slate_date', sa.Date(), nullable=False),
        sa.Column('kickoff_time', sa.Time(), nullable=False),
        sa.Column('is_playoff', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('season', 'week', name='uq_nfl_schedule_season_week')
    )
    
    # Create indexes
    op.create_index('idx_weeks_nfl_slate_date', 'weeks', ['nfl_slate_date'])
    op.create_index('idx_weeks_is_locked', 'weeks', ['is_locked'])
    op.create_index('idx_week_metadata_week_id', 'week_metadata', ['week_id'])
    op.create_index('idx_nfl_schedule_season', 'nfl_schedule', ['season'])
    op.create_index('idx_nfl_schedule_slate_date', 'nfl_schedule', ['slate_date'])


def downgrade() -> None:
    op.drop_index('idx_nfl_schedule_slate_date', 'nfl_schedule')
    op.drop_index('idx_nfl_schedule_season', 'nfl_schedule')
    op.drop_index('idx_week_metadata_week_id', 'week_metadata')
    op.drop_index('idx_weeks_is_locked', 'weeks')
    op.drop_index('idx_weeks_nfl_slate_date', 'weeks')
    
    op.drop_table('nfl_schedule')
    op.drop_table('week_metadata')
    
    op.drop_column('weeks', 'metadata')
    op.drop_column('weeks', 'locked_at')
    op.drop_column('weeks', 'is_locked')
    op.drop_column('weeks', 'status_override')
    op.drop_column('weeks', 'nfl_slate_date')
```

---

## All snippets are documented in detail in `spec.md`

For complete implementations, refer to the specific sections in the main specification.

