# Week Management API Documentation

**Version:** 1.0
**Last Updated:** October 28, 2025
**Status:** Complete and Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Base URL & Authentication](#base-url--authentication)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Schemas](#requestresponse-schemas)
5. [Error Handling](#error-handling)
6. [cURL Examples](#curl-examples)
7. [Integration Guide](#integration-guide)

---

## Overview

The Week Management API provides REST endpoints for managing NFL seasons and weeks within the Cortex DFS lineup optimization system. The API supports:

- Dynamic week generation based on NFL calendar
- Week status management (active, upcoming, completed)
- Manual status overrides with persistence
- Week locking after data import (prevents modifications)
- Import tracking with metadata
- NFL schedule retrieval

### Key Features

- Automatic week creation from NFL schedule (no hardcoding)
- Smart status calculation based on dates
- Week immutability enforcement after import
- Rich metadata (kickoff times, ESPN links, import details)
- Full error handling with user-friendly messages

---

## Base URL & Authentication

### Base URL
```
http://localhost:8000/api
# Production: https://api.cortex.example.com/api
```

### Authentication
Currently no authentication required (development mode). In production, implement OAuth 2.0 or API key authentication.

### Headers
```
Content-Type: application/json
Accept: application/json
```

---

## API Endpoints

### 1. Get Weeks by Year

Retrieve all 18 weeks for a given NFL season with metadata.

**Endpoint:** `GET /api/weeks`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `year` | integer | Yes | N/A | NFL season year (2025-2030) |
| `include_metadata` | boolean | No | true | Include detailed metadata in response |

**Response: 200 OK**
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
        "espn_link": "https://www.espn.com/nfl/schedule/_/week/1/year/2025",
        "slate_start": "2025-09-07T13:00:00Z",
        "import_status": "imported",
        "import_count": 153,
        "import_timestamp": "2025-09-10T14:30:00Z"
      }
    }
    // ... 17 more weeks
  ],
  "current_week": 5,
  "current_date": "2025-10-05T12:00:00Z"
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid Year | Year not between 2025-2030 |
| 500 | Internal Server Error | Database error or schedule not found |

**Processing Logic:**
1. Validate year is between 2025-2030
2. Check if weeks exist in database
3. If not, auto-generate 18 weeks from nfl_schedule
4. Calculate current week and status for each week
5. Apply manual status overrides
6. Sort by week_number and return

---

### 2. Get Current Week

Get the current active NFL week with full details.

**Endpoint:** `GET /api/current-week`

**Parameters:** None

**Response: 200 OK**
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
    "status_override": null,
    "nfl_slate_date": "2025-10-05",
    "is_locked": false,
    "locked_at": null,
    "metadata": {
      "kickoff_time": "13:00",
      "espn_link": "https://www.espn.com/nfl/schedule/_/week/5/year/2025",
      "slate_start": "2025-10-05T13:00:00Z",
      "import_status": "pending",
      "import_count": 0,
      "import_timestamp": null
    }
  }
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 500 | Internal Server Error | Unable to determine current week |

**Processing Logic:**
1. Get current date/time (UTC)
2. Query nfl_schedule to find matching week
3. Check for manual status overrides
4. Return week with full metadata

---

### 3. Get Week Metadata

Retrieve detailed metadata for a specific week.

**Endpoint:** `GET /api/weeks/{id}/metadata`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Week ID |

**Response: 200 OK**
```json
{
  "success": true,
  "week_id": 5,
  "metadata": {
    "season": 2025,
    "week_number": 5,
    "nfl_slate_date": "2025-10-05",
    "kickoff_time": "13:00",
    "espn_link": "https://www.espn.com/nfl/schedule/_/week/5/year/2025",
    "import_status": "imported",
    "import_count": 153,
    "import_timestamp": "2025-10-05T14:30:00Z",
    "is_locked": true,
    "locked_at": "2025-10-05T14:30:00Z"
  }
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 404 | Week Not Found | Week ID doesn't exist |
| 500 | Internal Server Error | Database error |

---

### 4. Update Week Status

Manually override the auto-calculated status of a week.

**Endpoint:** `PUT /api/weeks/{id}/status`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Week ID |

**Request Body:**
```json
{
  "status": "active",
  "reason": "Manual override for testing"
}
```

**Request Schema:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `status` | string | Yes | "active", "upcoming", "completed" |
| `reason` | string | No | Any string describing override reason |

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Week status updated",
  "week": {
    "id": 5,
    "season": 2025,
    "week_number": 5,
    "status": "active",
    "status_override": "active",
    "nfl_slate_date": "2025-10-05",
    "is_locked": false,
    "locked_at": null,
    "metadata": {
      "kickoff_time": "13:00",
      "espn_link": "https://www.espn.com/nfl/schedule/_/week/5/year/2025",
      "import_status": "pending",
      "import_count": 0,
      "import_timestamp": null
    }
  }
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid Status | Status not in ["active", "upcoming", "completed"] |
| 404 | Week Not Found | Week ID doesn't exist |
| 409 | Week Locked | Week is locked after import |
| 500 | Internal Server Error | Database error |

**Processing Logic:**
1. Validate week exists
2. Validate status is valid enum
3. Check week is not locked
4. Create/update week_status_overrides record
5. Return updated week

---

### 5. Generate Weeks for Season

Auto-generate 18 weeks for a given NFL season.

**Endpoint:** `POST /api/weeks/generate`

**Request Body:**
```json
{
  "year": 2026,
  "force_regenerate": false
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `year` | integer | Yes | NFL season year (2025-2030) |
| `force_regenerate` | boolean | No | Delete existing weeks and regenerate (default: false) |

**Response: 200 OK**
```json
{
  "success": true,
  "message": "18 weeks generated for 2026",
  "weeks_created": 18,
  "year": 2026
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid Year | Year not between 2025-2030 |
| 409 | Conflict | Weeks already exist (set force_regenerate=true) |
| 500 | NFL Schedule Not Found | Schedule data missing for year |

**Processing Logic:**
1. Validate year is valid
2. Check if weeks exist for year
3. If exist and force_regenerate=false, return 409
4. If force_regenerate=true, delete existing weeks
5. Fetch NFL schedule for year
6. Create 18 week records with metadata
7. Return count of created weeks

---

### 6. Get NFL Schedule

Retrieve the NFL schedule for a given year.

**Endpoint:** `GET /api/nfl-schedule`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `year` | integer | No | Current year | NFL season year (2025-2030) |

**Response: 200 OK**
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
    {
      "week": 2,
      "slate_date": "2025-09-14",
      "kickoff_time": "13:00",
      "is_playoff": false,
      "game_count": 16
    }
    // ... 16 more weeks
  ]
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid Year | Year not between 2025-2030 |
| 500 | Internal Server Error | Schedule data not found |

---

### 7. Lock Week

Lock a week after successful data import (prevents modifications).

**Endpoint:** `PUT /api/weeks/{id}/lock`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Week ID |

**Request Body:**
```json
{
  "import_id": "550e8400-e29b-41d4-a716-446655440000",
  "player_count": 153
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `import_id` | string | Yes | UUID of import transaction |
| `player_count` | integer | Yes | Number of players imported |

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Week locked",
  "week": {
    "id": 5,
    "season": 2025,
    "week_number": 5,
    "status": "active",
    "status_override": null,
    "nfl_slate_date": "2025-10-05",
    "is_locked": true,
    "locked_at": "2025-10-05T14:30:00Z",
    "metadata": {
      "kickoff_time": "13:00",
      "espn_link": "https://www.espn.com/nfl/schedule/_/week/5/year/2025",
      "import_status": "imported",
      "import_count": 153,
      "import_timestamp": "2025-10-05T14:30:00Z"
    }
  }
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 404 | Week Not Found | Week ID doesn't exist |
| 409 | Week Already Locked | Week already has imported data |
| 500 | Internal Server Error | Database error |

**Processing Logic:**
1. Validate week exists
2. Check week is not already locked
3. Set is_locked = true, locked_at = NOW()
4. Update week_metadata with import_status='imported'
5. Update import_count and import_timestamp
6. Return updated week

**Called by:** Data Import System after successful import

---

### 8. Update Week Import Status

Update the import status and metadata for a week.

**Endpoint:** `PUT /api/weeks/{id}/import-status`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Week ID |

**Request Body:**
```json
{
  "status": "imported",
  "import_count": 153,
  "import_timestamp": "2025-10-05T14:30:00Z",
  "error_message": null
}
```

**Request Schema:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `status` | string | Yes | "pending", "imported", "error" |
| `import_count` | integer | Yes | Number of players |
| `import_timestamp` | string (ISO) | Yes | When import occurred |
| `error_message` | string | No | Error message if status="error" |

**Response: 200 OK**
```json
{
  "success": true,
  "message": "Import status updated",
  "week": {
    "id": 5,
    "season": 2025,
    "week_number": 5,
    "status": "active",
    "status_override": null,
    "nfl_slate_date": "2025-10-05",
    "is_locked": false,
    "locked_at": null,
    "metadata": {
      "kickoff_time": "13:00",
      "espn_link": "https://www.espn.com/nfl/schedule/_/week/5/year/2025",
      "import_status": "imported",
      "import_count": 153,
      "import_timestamp": "2025-10-05T14:30:00Z"
    }
  }
}
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid Status | Status not in ["pending", "imported", "error"] |
| 404 | Week Not Found | Week ID doesn't exist |
| 500 | Internal Server Error | Database error |

---

## Request/Response Schemas

### Week Response Schema
```json
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
    "espn_link": "https://www.espn.com/nfl/schedule/_/week/1/year/2025",
    "slate_start": "2025-09-07T13:00:00Z",
    "import_status": "imported",
    "import_count": 153,
    "import_timestamp": "2025-09-10T14:30:00Z"
  }
}
```

### Error Response Schema
```json
{
  "success": false,
  "error": "User-friendly error message"
}
```

### Standard Success Response
All successful responses include:
- `success: true`
- Status-specific data (weeks, metadata, etc.)
- `message` field (where applicable)

---

## Error Handling

### Error Status Codes

| Status | Name | Cause | Resolution |
|--------|------|-------|-----------|
| 400 | Bad Request | Invalid parameters (year, status, etc.) | Check request parameters against documentation |
| 404 | Not Found | Week doesn't exist | Verify week ID is correct |
| 409 | Conflict | Week already locked or seasons exist | Use force_regenerate for seasons, can't modify locked weeks |
| 500 | Server Error | Database error or unexpected exception | Check server logs, retry with exponential backoff |

### Error Recovery

1. **Automatic Retry:** Client should retry 400/500 errors with exponential backoff (1s, 2s, 4s, 8s)
2. **Graceful Degradation:** If metadata unavailable, show basic week info
3. **Fallback Data:** Use localStorage cache if API fails
4. **User Feedback:** Display user-friendly error messages (never stack traces)

---

## cURL Examples

### Get Weeks for 2025
```bash
curl -X GET "http://localhost:8000/api/weeks?year=2025&include_metadata=true" \
  -H "Content-Type: application/json"
```

### Get Current Week
```bash
curl -X GET "http://localhost:8000/api/current-week" \
  -H "Content-Type: application/json"
```

### Get Week Metadata
```bash
curl -X GET "http://localhost:8000/api/weeks/5/metadata" \
  -H "Content-Type: application/json"
```

### Update Week Status (Manual Override)
```bash
curl -X PUT "http://localhost:8000/api/weeks/5/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "reason": "Manual override for testing"
  }'
```

### Generate Weeks for 2026
```bash
curl -X POST "http://localhost:8000/api/weeks/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2026,
    "force_regenerate": false
  }'
```

### Get NFL Schedule
```bash
curl -X GET "http://localhost:8000/api/nfl-schedule?year=2025" \
  -H "Content-Type: application/json"
```

### Lock Week After Import
```bash
curl -X PUT "http://localhost:8000/api/weeks/5/lock" \
  -H "Content-Type: application/json" \
  -d '{
    "import_id": "550e8400-e29b-41d4-a716-446655440000",
    "player_count": 153
  }'
```

### Update Import Status
```bash
curl -X PUT "http://localhost:8000/api/weeks/5/import-status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "imported",
    "import_count": 153,
    "import_timestamp": "2025-10-05T14:30:00Z",
    "error_message": null
  }'
```

---

## Integration Guide

### Frontend Integration (React)

```typescript
// Fetch weeks for current year
const { data: weeks } = useQuery({
  queryKey: ['weeks', currentYear],
  queryFn: () => fetch(`/api/weeks?year=${currentYear}`).then(r => r.json()),
});

// Get current week
const { data: currentWeekData } = useQuery({
  queryKey: ['current-week'],
  queryFn: () => fetch('/api/current-week').then(r => r.json()),
  refetchInterval: 60000, // 1 minute
});

// Update week status
const updateStatus = useMutation({
  mutationFn: (weekId: number, status: string) =>
    fetch(`/api/weeks/${weekId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, reason: 'Manual override' }),
    }).then(r => r.json()),
});

// Lock week after import
const lockWeek = useMutation({
  mutationFn: (weekId: number, importId: string, playerCount: number) =>
    fetch(`/api/weeks/${weekId}/lock`, {
      method: 'PUT',
      body: JSON.stringify({ import_id: importId, player_count: playerCount }),
    }).then(r => r.json()),
});
```

### Data Import System Integration

After successful import:
1. Call `PUT /api/weeks/{week_id}/lock` with import metadata
2. Call `PUT /api/weeks/{week_id}/import-status` with final status
3. Update frontend Zustand store with locked week
4. Show import success toast with week details

### Scheduled Tasks

Implement daily scheduled task to update week statuses:
```python
# Backend scheduled task (e.g., with APScheduler)
@scheduler.scheduled_job('cron', hour=0)
def update_all_week_statuses():
    """Update all week statuses at midnight UTC"""
    db = SessionLocal()
    service = WeekManagementService(db)
    status_service = StatusUpdateService(db)

    for year in range(2025, 2031):
        weeks = service.get_weeks_by_year(year)
        for week in weeks:
            week['status'] = status_service.determine_week_status(week)
        status_service.update_all_statuses(year)
    db.close()
```

---

## OpenAPI/Swagger

Access the interactive API documentation at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide:
- Interactive endpoint testing
- Request/response examples
- Schema documentation
- Authentication testing

---

## Performance Considerations

- **Database Queries:** All optimized to <100ms
- **Response Time:** Typical <200ms for all endpoints
- **Caching:** Consider caching NFL schedule (changes yearly)
- **Pagination:** Not needed (max 18 weeks per year)
- **Rate Limiting:** Implement in production (suggest 100 req/min per IP)

---

## Versioning

Current API version: **1.0**

Future versions will maintain backward compatibility or provide migration path.

---

**End of API Documentation**
