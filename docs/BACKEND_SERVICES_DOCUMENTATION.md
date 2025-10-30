# Backend Services Documentation

**Version:** 1.0
**Last Updated:** October 28, 2025
**Status:** Complete and Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [WeekManagementService](#weekmanagementservice)
3. [StatusUpdateService](#statusupdateservice)
4. [NFLScheduleService](#nflscheduleservice)
5. [Error Classes](#error-classes)
6. [Database Integration](#database-integration)
7. [Usage Examples](#usage-examples)

---

## Overview

The backend services provide core business logic for week management:

- **WeekManagementService:** Core CRUD operations and week lifecycle management
- **StatusUpdateService:** Automatic and manual status calculation and updates
- **NFLScheduleService:** NFL schedule data retrieval and metadata generation

All services use SQLAlchemy ORM with dependency injection for database sessions.

---

## WeekManagementService

Core service for managing NFL weeks and seasons.

**File:** `/backend/services/week_management_service.py`

### Constructor

```python
def __init__(self, session: Session):
    """
    Initialize WeekManagementService.

    Args:
        session: SQLAlchemy Session for database operations
    """
    self.session = session
```

### Methods

#### create_weeks_for_season(year: int) -> int

Create 18 weeks for a given NFL season from nfl_schedule data.

**Parameters:**
- `year` (int): NFL season year (2025-2030)

**Returns:**
- `int`: Count of created weeks (18 if successful, 0 if already exist)

**Raises:**
- `InvalidYearError`: If year not between 2025-2030
- `CortexException`: If NFL schedule data not found for year

**Example:**
```python
from backend.services.week_management_service import WeekManagementService

week_service = WeekManagementService(db_session)
weeks_created = week_service.create_weeks_for_season(2026)
print(f"Created {weeks_created} weeks for 2026")  # Output: Created 18 weeks for 2026
```

**Processing Logic:**
1. Validate year is between 2025-2030
2. Check if weeks already exist for year (skip if found)
3. Query nfl_schedule table for year
4. For each of 18 weeks:
   - Create Week record with season, week_number, status, nfl_slate_date
   - Create corresponding week_metadata record
5. Commit transaction and return count

**Database Operations:**
```sql
INSERT INTO weeks (season, week_number, status, nfl_slate_date)
VALUES (:season, :week_number, :status, :nfl_slate_date)
RETURNING id

INSERT INTO week_metadata (week_id, season, week_number, nfl_slate_date, ...)
VALUES (...)
```

---

#### get_weeks_by_year(year: int) -> List[Dict[str, Any]]

Retrieve all 18 weeks for a given year with metadata and calculated status.

**Parameters:**
- `year` (int): NFL season year (2025-2030)

**Returns:**
- `List[Dict]`: Array of week objects with metadata

**Raises:**
- `InvalidYearError`: If year not between 2025-2030
- `CortexException`: If weeks don't exist and can't auto-create

**Example:**
```python
week_service = WeekManagementService(db_session)
weeks = week_service.get_weeks_by_year(2025)

for week in weeks:
    print(f"Week {week['week_number']}: {week['status']}")
    print(f"  Date: {week['nfl_slate_date']}")
    print(f"  Import Status: {week['metadata']['import_status']}")
```

**Processing Logic:**
1. Validate year is valid
2. Query all weeks for year from database
3. If not found, auto-create using create_weeks_for_season()
4. For each week:
   - Get week_metadata
   - Calculate status (or use override)
   - Compile metadata dictionary
5. Sort by week_number
6. Return list of week dictionaries

**Return Data Structure:**
```python
[
    {
        'id': 1,
        'season': 2025,
        'week_number': 1,
        'status': 'completed',
        'status_override': None,
        'nfl_slate_date': date(2025, 9, 7),
        'is_locked': True,
        'locked_at': datetime(2025, 9, 10, 14, 30),
        'metadata': {
            'kickoff_time': '13:00',
            'espn_link': 'https://www.espn.com/nfl/schedule/_/week/1/year/2025',
            'slate_start': '2025-09-07T13:00:00Z',
            'import_status': 'imported',
            'import_count': 153,
            'import_timestamp': '2025-09-10T14:30:00Z',
        }
    },
    # ... 17 more weeks
]
```

---

#### get_current_week() -> Dict[str, Any]

Determine and return the current active NFL week.

**Parameters:** None

**Returns:**
- `Dict`: Dictionary with week_number, status, current_date, and week_details

**Raises:**
- `CortexException`: If unable to determine current week

**Example:**
```python
week_service = WeekManagementService(db_session)
current = week_service.get_current_week()

print(f"Current week: {current['week_number']}")
print(f"Status: {current['week_details']['status']}")
print(f"Date: {current['current_date']}")
```

**Processing Logic:**
1. Get current date/time (UTC)
2. Query nfl_schedule for week matching current date
3. Get week details from weeks table
4. Check for status overrides
5. Return week data with current_date

**Return Data Structure:**
```python
{
    'week_number': 5,
    'current_date': '2025-10-05T12:00:00Z',
    'week_details': {
        'id': 5,
        'season': 2025,
        'week_number': 5,
        'status': 'active',
        'status_override': None,
        'nfl_slate_date': date(2025, 10, 5),
        'is_locked': False,
        'locked_at': None,
        'metadata': { ... }
    }
}
```

---

#### lock_week(week_id: int, import_id: str, player_count: int) -> Dict[str, Any]

Lock a week after successful data import (prevents future modifications).

**Parameters:**
- `week_id` (int): ID of the week to lock
- `import_id` (str): UUID of import transaction
- `player_count` (int): Number of players imported

**Returns:**
- `Dict`: Updated week object

**Raises:**
- `WeekNotFoundError`: If week doesn't exist
- `CortexException`: If week already locked

**Example:**
```python
import uuid

week_service = WeekManagementService(db_session)
import_id = str(uuid.uuid4())

updated_week = week_service.lock_week(
    week_id=5,
    import_id=import_id,
    player_count=153
)

print(f"Week {updated_week['week_number']} is now locked")
print(f"Imported: {updated_week['metadata']['import_count']} players")
```

**Processing Logic:**
1. Validate week exists
2. Check week is not already locked
3. Set is_locked = true, locked_at = NOW()
4. Update week_metadata:
   - import_status = 'imported'
   - import_count = player_count
   - import_timestamp = NOW()
5. Commit transaction
6. Return updated week object

**Database Operations:**
```sql
UPDATE weeks
SET is_locked = true, locked_at = CURRENT_TIMESTAMP
WHERE id = :week_id

UPDATE week_metadata
SET import_status = 'imported',
    import_count = :player_count,
    import_timestamp = CURRENT_TIMESTAMP
WHERE week_id = :week_id
```

---

#### validate_week_immutability(week_id: int) -> None

Validate that a week is not locked. Raises error if locked.

**Parameters:**
- `week_id` (int): ID of the week to validate

**Returns:** None

**Raises:**
- `WeekNotFoundError`: If week doesn't exist
- `WeekLockedError`: If week is locked

**Example:**
```python
week_service = WeekManagementService(db_session)

try:
    week_service.validate_week_immutability(week_id=5)
    # Week is not locked, can proceed with modifications
except WeekLockedError as e:
    print(f"Cannot modify: {e.message}")
```

**Use Cases:**
- Before DELETE operation: `validate_week_immutability()` then delete
- Before UPDATE operation: `validate_week_immutability()` then update
- Preventing accidental modifications

---

#### update_week_status(week_id: int, status: str, reason: str = '') -> Dict[str, Any]

Manually override the auto-calculated status of a week.

**Parameters:**
- `week_id` (int): ID of the week
- `status` (str): New status ('active', 'upcoming', 'completed')
- `reason` (str, optional): Reason for override

**Returns:**
- `Dict`: Updated week object

**Raises:**
- `WeekNotFoundError`: If week doesn't exist
- `ValueError`: If status not valid enum
- `WeekLockedError`: If week is locked

**Example:**
```python
week_service = WeekManagementService(db_session)

updated_week = week_service.update_week_status(
    week_id=5,
    status='active',
    reason='Manual override for testing'
)

print(f"Week {updated_week['week_number']} status: {updated_week['status']}")
print(f"Override reason: {updated_week.get('override_reason')}")
```

**Processing Logic:**
1. Validate week exists
2. Validate status is valid enum
3. Check week is not locked
4. Create or update week_status_overrides record:
   - override_status = status
   - reason = reason
   - overridden_at = NOW()
5. Update weeks.status_override column
6. Return updated week

**Database Operations:**
```sql
INSERT INTO week_status_overrides (week_id, override_status, reason, overridden_at)
VALUES (:week_id, :status, :reason, CURRENT_TIMESTAMP)
ON CONFLICT (week_id) DO UPDATE SET
  override_status = :status,
  reason = :reason,
  overridden_at = CURRENT_TIMESTAMP

UPDATE weeks
SET status_override = :status
WHERE id = :week_id
```

---

## StatusUpdateService

Service for calculating and updating week statuses.

**File:** `/backend/services/status_update_service.py`

### Constructor

```python
def __init__(self, session: Session):
    """
    Initialize StatusUpdateService.

    Args:
        session: SQLAlchemy Session for database operations
    """
    self.session = session
```

### Methods

#### determine_week_status(week: Dict, current_date: date = None) -> str

Calculate the status of a week based on date comparison.

**Parameters:**
- `week` (Dict): Week object with nfl_slate_date
- `current_date` (date, optional): Date to compare against (default: today)

**Returns:**
- `str`: Status ('active', 'upcoming', 'completed')

**Example:**
```python
from datetime import date
from backend.services.status_update_service import StatusUpdateService

status_service = StatusUpdateService(db_session)
week = {
    'week_number': 5,
    'nfl_slate_date': date(2025, 10, 5),
}

status = status_service.determine_week_status(
    week=week,
    current_date=date(2025, 10, 5)
)
print(status)  # Output: 'active'
```

**Processing Logic:**
1. Get current_date (default: today)
2. Compare current_date to week's nfl_slate_date:
   - If nfl_slate_date < current_date: return 'completed'
   - If nfl_slate_date == current_date: return 'active'
   - If nfl_slate_date in current week: return 'active'
   - If nfl_slate_date > current_date: return 'upcoming'
3. Account for timezone (ET/Eastern Time)

**Status Rules:**
```
Past (before this week's Sunday): 'completed'
Current week (Sunday to Saturday): 'active'
Future (after this Saturday): 'upcoming'
```

---

#### update_all_statuses(year: int) -> int

Update all week statuses for a given season.

**Parameters:**
- `year` (int): NFL season year

**Returns:**
- `int`: Count of weeks updated

**Raises:**
- `InvalidYearError`: If year not valid

**Example:**
```python
status_service = StatusUpdateService(db_session)
updated_count = status_service.update_all_statuses(2025)
print(f"Updated {updated_count} weeks")
```

**Processing Logic:**
1. Query all weeks for year
2. For each week:
   - Check for status_override first
   - If override exists, use that status
   - Otherwise, determine_week_status()
   - Update week.status in database
3. Commit transaction
4. Return count of updated weeks

**Use Cases:**
- Scheduled daily task at midnight UTC
- Manual update request from admin
- On-demand status refresh

---

#### apply_manual_overrides(week: Dict) -> str

Check for manual status overrides and apply them.

**Parameters:**
- `week` (Dict): Week object

**Returns:**
- `str`: Final status (manual override if exists, else auto-calculated)

**Example:**
```python
status_service = StatusUpdateService(db_session)

final_status = status_service.apply_manual_overrides(week)
print(f"Final status (with overrides): {final_status}")
```

**Processing Logic:**
1. Query week_status_overrides for week_id
2. If override exists:
   - Return override_status
   - Log: "Using override status for week X"
3. Else:
   - Return calculated status
   - Log: "Using auto-calculated status for week X"

---

## NFLScheduleService

Service for managing NFL schedule data and metadata generation.

**File:** `/backend/services/nfl_schedule_service.py`

### Constructor

```python
def __init__(self, session: Session):
    """
    Initialize NFLScheduleService.

    Args:
        session: SQLAlchemy Session for database operations
    """
    self.session = session
```

### Methods

#### get_nfl_schedule(year: int) -> List[Dict[str, Any]]

Retrieve the complete NFL schedule for a given year.

**Parameters:**
- `year` (int): NFL season year (2025-2030)

**Returns:**
- `List[Dict]`: Array of week schedule data (18 weeks)

**Raises:**
- `InvalidYearError`: If year not valid
- `CortexException`: If schedule not found

**Example:**
```python
from backend.services.nfl_schedule_service import NFLScheduleService

nfl_service = NFLScheduleService(db_session)
schedule = nfl_service.get_nfl_schedule(2025)

for week_data in schedule:
    print(f"Week {week_data['week']}: {week_data['slate_date']} at {week_data['kickoff_time']}")
```

**Return Data Structure:**
```python
[
    {
        'week': 1,
        'slate_date': '2025-09-07',
        'kickoff_time': '13:00',
        'is_playoff': False,
        'game_count': 16,
    },
    # ... 17 more weeks
]
```

**Database Query:**
```sql
SELECT season, week, slate_date, kickoff_time, game_count, is_playoff
FROM nfl_schedule
WHERE season = :season
ORDER BY week ASC
```

---

#### get_week_metadata(week_id: int) -> Dict[str, Any]

Retrieve detailed metadata for a specific week.

**Parameters:**
- `week_id` (int): ID of the week

**Returns:**
- `Dict`: Compiled metadata object

**Raises:**
- `WeekNotFoundError`: If week doesn't exist

**Example:**
```python
nfl_service = NFLScheduleService(db_session)
metadata = nfl_service.get_week_metadata(week_id=5)

print(f"Kickoff: {metadata['kickoff_time']}")
print(f"ESPN Link: {metadata['espn_link']}")
print(f"Imported: {metadata['import_count']} players")
```

**Return Data Structure:**
```python
{
    'season': 2025,
    'week_number': 5,
    'nfl_slate_date': '2025-10-05',
    'kickoff_time': '13:00',
    'espn_link': 'https://www.espn.com/nfl/schedule/_/week/5/year/2025',
    'import_status': 'imported',
    'import_count': 153,
    'import_timestamp': '2025-10-05T14:30:00Z',
    'is_locked': True,
    'locked_at': '2025-10-05T14:30:00Z',
    'error_message': None,  # Only if import_status='error'
}
```

**Processing Logic:**
1. Query week_metadata for week_id
2. Query weeks for week details
3. Generate ESPN link
4. Compile all data into single metadata object
5. Return compiled metadata

---

#### generate_espn_link(week_number: int, season: int) -> str

Generate an ESPN NFL schedule link for a specific week.

**Parameters:**
- `week_number` (int): Week number (1-18)
- `season` (int): Season year (2025-2030)

**Returns:**
- `str`: Full ESPN URL

**Example:**
```python
nfl_service = NFLScheduleService(db_session)
espn_link = nfl_service.generate_espn_link(week_number=5, season=2025)
print(espn_link)
# Output: https://www.espn.com/nfl/schedule/_/week/5/year/2025
```

**URL Format:**
```
https://www.espn.com/nfl/schedule/_/week/{week}/year/{season}
```

---

## Error Classes

### WeekLockedError

Raised when trying to modify a locked week.

```python
class WeekLockedError(CortexException):
    def __init__(self, week_number: int):
        super().__init__(
            f"Week {week_number} is locked due to imported data. "
            f"Cannot modify weeks with imported player pools.",
            status_code=409
        )
```

**Usage:**
```python
from backend.services.week_management_service import WeekLockedError

try:
    week_service.validate_week_immutability(week_id=5)
except WeekLockedError as e:
    print(f"Error: {e.message}")  # Output: Week 5 is locked...
    http_status = e.status_code   # 409
```

---

### WeekNotFoundError

Raised when a week doesn't exist.

```python
class WeekNotFoundError(CortexException):
    def __init__(self, week_id: int):
        super().__init__(
            f"Week {week_id} not found",
            status_code=404
        )
```

**Usage:**
```python
from backend.services.week_management_service import WeekNotFoundError

try:
    week = week_service.get_week_metadata(week_id=999)
except WeekNotFoundError as e:
    print(f"Error: {e.message}")  # Output: Week 999 not found
    http_status = e.status_code   # 404
```

---

### InvalidYearError

Raised when year is outside valid range.

```python
class InvalidYearError(CortexException):
    def __init__(self, year: int):
        super().__init__(
            f"Year {year} is invalid. Must be between 2025 and 2030.",
            status_code=400
        )
```

**Usage:**
```python
from backend.services.week_management_service import InvalidYearError

try:
    weeks = week_service.get_weeks_by_year(year=2024)
except InvalidYearError as e:
    print(f"Error: {e.message}")  # Output: Year 2024 is invalid...
    http_status = e.status_code   # 400
```

---

## Database Integration

### Session Management

All services use SQLAlchemy Session for database operations:

```python
from sqlalchemy.orm import Session
from backend.services.week_management_service import WeekManagementService

# In API endpoint
def get_weeks(db: Session = Depends(get_db)):
    service = WeekManagementService(db)
    weeks = service.get_weeks_by_year(2025)
    return weeks
```

### Transactions

Services handle transactions automatically:

```python
# Automatic rollback on exception
try:
    week_service.lock_week(week_id, import_id, player_count)
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

### Query Optimization

All queries are optimized with:

- Database indexes on frequently queried columns
- SQL query caching for schedule data
- Pagination support (if needed)
- Connection pooling (10 connections, max 20 overflow)

**Performance Targets:**
- Database queries: <100ms
- API response time: <200ms typical
- Cached queries: <50ms

---

## Usage Examples

### Complete Week Selection Flow

```python
from sqlalchemy.orm import Session
from backend.services.week_management_service import WeekManagementService
from backend.services.status_update_service import StatusUpdateService
from backend.services.nfl_schedule_service import NFLScheduleService

def process_week_selection(db: Session, year: int, week_id: int):
    """Complete week selection workflow"""

    # 1. Get all weeks for year
    week_service = WeekManagementService(db)
    weeks = week_service.get_weeks_by_year(year)
    print(f"Loaded {len(weeks)} weeks for {year}")

    # 2. Get current week
    current_week = week_service.get_current_week()
    print(f"Current week: {current_week['week_number']}")

    # 3. Find selected week
    selected_week = next(
        (w for w in weeks if w['id'] == week_id),
        None
    )

    if not selected_week:
        raise WeekNotFoundError(week_id)

    # 4. Get detailed metadata
    nfl_service = NFLScheduleService(db)
    metadata = nfl_service.get_week_metadata(week_id)

    # 5. Return complete week data
    return {
        'week': selected_week,
        'metadata': metadata,
        'is_locked': selected_week['is_locked'],
    }
```

### Data Import Workflow

```python
def complete_data_import(db: Session, week_id: int, import_id: str, player_count: int):
    """Lock week after successful data import"""

    week_service = WeekManagementService(db)

    # 1. Lock week to prevent future modifications
    updated_week = week_service.lock_week(
        week_id=week_id,
        import_id=import_id,
        player_count=player_count
    )

    # 2. Verify lock was successful
    assert updated_week['is_locked'], "Week lock failed"
    assert updated_week['metadata']['import_count'] == player_count

    # 3. Return success
    return {
        'success': True,
        'week_id': week_id,
        'locked': True,
        'import_count': player_count,
    }
```

### Scheduled Status Update

```python
from apscheduler.schedulers.background import BackgroundScheduler

def init_scheduled_tasks(db: Session):
    """Initialize scheduled background tasks"""

    scheduler = BackgroundScheduler()

    @scheduler.scheduled_job('cron', hour=0, minute=0)
    def update_week_statuses():
        """Update all week statuses daily at midnight UTC"""
        status_service = StatusUpdateService(db)

        for year in range(2025, 2031):
            try:
                updated = status_service.update_all_statuses(year)
                print(f"Updated {updated} weeks for {year}")
            except Exception as e:
                print(f"Error updating week statuses for {year}: {e}")

    scheduler.start()
    return scheduler
```

---

**End of Backend Services Documentation**
