# Showdown Mode API Documentation

**Version:** 1.0
**Last Updated:** November 2, 2025
**Feature:** DraftKings Showdown Contest Support

---

## Table of Contents

1. [Overview](#overview)
2. [API Endpoint Changes](#api-endpoint-changes)
3. [Request/Response Schemas](#requestresponse-schemas)
4. [Showdown-Specific Examples](#showdown-specific-examples)
5. [Error Handling](#error-handling)
6. [Migration Guide](#migration-guide)

---

## Overview

This document describes API changes to support DraftKings Showdown mode. All existing Main Slate endpoints continue to work unchanged. Showdown support is additive, not breaking.

### Key Changes

1. **contest_mode Parameter:** Added to endpoints that handle player/lineup data
2. **Backward Compatible:** Default value `'main'` preserves existing behavior
3. **New Fields:** `is_captain` flag in lineup responses
4. **New Settings:** `locked_captain_id` in optimization settings

### Base URL

```
Development: http://localhost:8000/api
Production:  https://api.cortex.example.com/api
```

---

## API Endpoint Changes

### 1. Get Players by Week

Retrieve players for a given week and contest mode.

**Endpoint:** `GET /api/players/{week_id}`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `week_id` | integer | Yes | N/A | NFL week number (1-18) |
| `contest_mode` | string | No | `'main'` | Contest type: `'main'` or `'showdown'` |

**Response: 200 OK**

```json
{
  "success": true,
  "week_id": 9,
  "contest_mode": "showdown",
  "players": [
    {
      "id": 123,
      "week_id": 9,
      "contest_mode": "showdown",
      "player_name": "Patrick Mahomes",
      "team": "KC",
      "position": "QB",
      "salary": 8000,
      "projection": 24.5,
      "ownership": 35.2,
      "ceiling": 32.5,
      "floor": 18.3,
      "smart_score": 245.5,
      "created_at": "2025-11-02T10:00:00Z",
      "updated_at": "2025-11-02T10:00:00Z"
    }
    // ... more players
  ]
}
```

**Example Requests:**

```bash
# Get Main Slate players (default)
curl -X GET "http://localhost:8000/api/players/9"

# Get Showdown players
curl -X GET "http://localhost:8000/api/players/9?contest_mode=showdown"
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid contest_mode | Must be 'main' or 'showdown' |
| 404 | No players found | No data imported for week/mode |
| 500 | Internal Server Error | Database error |

---

### 2. Generate Lineups

Generate optimized lineups for Main Slate or Showdown.

**Endpoint:** `POST /api/lineups/generate`

**Request Body:**

```json
{
  "week_id": 9,
  "contest_mode": "showdown",
  "num_lineups": 10,
  "locked_captain_id": null,
  "max_ownership": 30.0,
  "smart_score_percentile": 50.0
}
```

**Request Schema:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `week_id` | integer | Yes | N/A | NFL week number |
| `contest_mode` | string | No | `'main'` | Contest type: `'main'` or `'showdown'` |
| `num_lineups` | integer | No | 10 | Number of lineups (1-20) |
| `locked_captain_id` | integer | No | null | Player ID to lock as captain (showdown only) |
| `max_ownership` | float | No | null | Max ownership % (0-100) |
| `smart_score_percentile` | float | No | null | Filter players by percentile (0-100) |

**Response: 200 OK (Showdown)**

```json
{
  "success": true,
  "contest_mode": "showdown",
  "lineups": [
    {
      "lineup_number": 1,
      "players": [
        {
          "id": 123,
          "name": "Patrick Mahomes",
          "team": "KC",
          "position": "QB",
          "salary": 12000,
          "projection": 36.75,
          "smart_score": 245.5,
          "ownership": 35.2,
          "is_captain": true
        },
        {
          "id": 456,
          "name": "Travis Kelce",
          "team": "KC",
          "position": "TE",
          "salary": 7200,
          "projection": 18.5,
          "smart_score": 189.3,
          "ownership": 28.5,
          "is_captain": false
        }
        // ... 4 more FLEX players (is_captain: false)
      ],
      "total_salary": 49800,
      "total_projection": 127.5,
      "total_smart_score": 1245.8
    }
    // ... 9 more lineups
  ],
  "generation_time": 18.3,
  "captain_diversity": 4
}
```

**Response: 200 OK (Main Slate)**

```json
{
  "success": true,
  "contest_mode": "main",
  "lineups": [
    {
      "lineup_number": 1,
      "players": [
        {
          "id": 789,
          "name": "Josh Allen",
          "team": "BUF",
          "position": "QB",
          "salary": 8000,
          "projection": 24.5,
          "smart_score": 220.1,
          "ownership": 32.5,
          "is_captain": false
        }
        // ... 8 more players (9 total, all is_captain: false)
      ],
      "total_salary": 49500,
      "total_projection": 145.2,
      "total_smart_score": 1450.5
    }
    // ... 9 more lineups
  ],
  "generation_time": 22.5
}
```

**Example Requests:**

```bash
# Generate Main Slate lineups (default)
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_id": 9,
    "num_lineups": 10,
    "max_ownership": 25.0
  }'

# Generate Showdown lineups with automatic captain
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_id": 9,
    "contest_mode": "showdown",
    "num_lineups": 10,
    "max_ownership": 30.0
  }'

# Generate Showdown lineups with locked captain
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_id": 9,
    "contest_mode": "showdown",
    "num_lineups": 5,
    "locked_captain_id": 123,
    "max_ownership": 30.0
  }'
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid contest_mode | Must be 'main' or 'showdown' |
| 400 | Cannot fit captain | No valid captain under salary cap |
| 400 | Captain lock prevents valid lineups | Locked captain salary too high |
| 400 | Insufficient players | Need 6+ players for showdown, 9+ for main |
| 404 | No players found | No data imported for week/mode |
| 500 | Lineup generation failed | PuLP solver error or optimization failure |

---

### 3. Import LineStar Data

Import LineStar Excel file for Main Slate or Showdown.

**Endpoint:** `POST /api/import/linestar`

**Request:** Multipart Form Data

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | Yes | N/A | Excel file (.xlsx) |
| `week_id` | integer | Yes | N/A | NFL week number |
| `contest_mode` | string | No | auto-detect | Contest type: `'main'`, `'showdown'`, or `'auto'` |

**Response: 200 OK**

```json
{
  "success": true,
  "week_id": 9,
  "contest_mode": "showdown",
  "players_imported": 54,
  "auto_detected": true,
  "message": "Successfully imported 54 showdown players for Week 9"
}
```

**Auto-Detection Logic:**

```python
if player_count < 100:
    contest_mode = 'showdown'
else:
    contest_mode = 'main'
```

**Example Requests:**

```bash
# Import with auto-detection (recommended)
curl -X POST "http://localhost:8000/api/import/linestar" \
  -F "file=@linestar_showdown_sea_was.xlsx" \
  -F "week_id=9"

# Import with explicit contest mode
curl -X POST "http://localhost:8000/api/import/linestar" \
  -F "file=@linestar_showdown_sea_was.xlsx" \
  -F "week_id=9" \
  -F "contest_mode=showdown"
```

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 400 | Invalid file format | Not an Excel file (.xlsx) |
| 400 | Missing required columns | File missing name/team/position/salary |
| 400 | Invalid contest_mode | Must be 'main', 'showdown', or 'auto' |
| 500 | Import failed | File parsing error or database error |

---

### 4. Get Saved Lineups

Retrieve saved lineups for a given week and contest mode.

**Endpoint:** `GET /api/lineups/saved/{week_id}`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `week_id` | integer | Yes | N/A | NFL week number |
| `contest_mode` | string | No | `'main'` | Contest type: `'main'` or `'showdown'` |

**Response: 200 OK**

```json
{
  "success": true,
  "week_id": 9,
  "contest_mode": "showdown",
  "saved_lineups": [
    {
      "id": 1,
      "lineup_number": 1,
      "players": [
        {
          "id": 123,
          "name": "Patrick Mahomes",
          "team": "KC",
          "position": "QB",
          "salary": 12000,
          "projection": 36.75,
          "is_captain": true
        }
        // ... 5 more FLEX players
      ],
      "total_salary": 49800,
      "total_projection": 127.5,
      "total_smart_score": 1245.8,
      "saved_at": "2025-11-02T14:30:00Z"
    }
    // ... more saved lineups
  ]
}
```

**Example Requests:**

```bash
# Get saved Main Slate lineups
curl -X GET "http://localhost:8000/api/lineups/saved/9"

# Get saved Showdown lineups
curl -X GET "http://localhost:8000/api/lineups/saved/9?contest_mode=showdown"
```

---

## Request/Response Schemas

### PlayerStatsResponse

```typescript
interface PlayerStatsResponse {
  id: number;
  week_id: number;
  contest_mode: 'main' | 'showdown';  // NEW
  player_name: string;
  team: string;
  position: string;
  salary: number;
  projection: number;
  ownership: number;
  ceiling: number;
  floor: number;
  smart_score: number;
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
}
```

### OptimizationSettings

```typescript
interface OptimizationSettings {
  week_id: number;
  contest_mode: 'main' | 'showdown';  // NEW (default: 'main')
  num_lineups: number;  // 1-20 (default: 10)
  locked_captain_id?: number;  // NEW: Showdown only
  max_ownership?: number;  // 0-100
  smart_score_percentile?: number;  // 0-100
  // ... other settings (stacking, exposure, etc.)
}
```

### PlayerInLineup

```typescript
interface PlayerInLineup {
  id: number;
  name: string;
  team: string;
  position: string;
  salary: number;  // Base salary for FLEX, 1.5x for captain
  projection: number;  // Base projection for FLEX, 1.5x for captain
  smart_score: number;  // Base score (not multiplied)
  ownership: number;
  is_captain: boolean;  // NEW: true for CPT, false for FLEX/main slate
}
```

### GeneratedLineup

```typescript
interface GeneratedLineup {
  lineup_number: number;
  players: PlayerInLineup[];  // 6 for showdown, 9 for main slate
  total_salary: number;  // ≤ $50,000
  total_projection: number;
  total_smart_score: number;
}
```

---

## Showdown-Specific Examples

### Example 1: Complete Showdown Workflow

```bash
# Step 1: Import showdown data
curl -X POST "http://localhost:8000/api/import/linestar" \
  -F "file=@linestar_showdown_sea_was.xlsx" \
  -F "week_id=9"

# Response:
{
  "success": true,
  "week_id": 9,
  "contest_mode": "showdown",
  "players_imported": 54,
  "auto_detected": true
}

# Step 2: Get players to verify import
curl -X GET "http://localhost:8000/api/players/9?contest_mode=showdown"

# Response:
{
  "success": true,
  "week_id": 9,
  "contest_mode": "showdown",
  "players": [
    { "id": 123, "name": "Patrick Mahomes", "team": "KC", ... },
    { "id": 456, "name": "Travis Kelce", "team": "KC", ... }
    // ... 52 more players
  ]
}

# Step 3: Calculate Smart Scores
curl -X POST "http://localhost:8000/api/smart-scores/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_id": 9,
    "contest_mode": "showdown",
    "weight_profile": "balanced"
  }'

# Response:
{
  "success": true,
  "week_id": 9,
  "contest_mode": "showdown",
  "players_scored": 54
}

# Step 4: Generate lineups
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_id": 9,
    "contest_mode": "showdown",
    "num_lineups": 10,
    "max_ownership": 30.0,
    "smart_score_percentile": 50.0
  }'

# Response:
{
  "success": true,
  "contest_mode": "showdown",
  "lineups": [
    {
      "lineup_number": 1,
      "players": [
        { "id": 123, "name": "Patrick Mahomes", "is_captain": true, ... },
        { "id": 456, "name": "Travis Kelce", "is_captain": false, ... }
        // ... 4 more FLEX
      ],
      "total_salary": 49800,
      "total_projection": 127.5
    }
    // ... 9 more lineups
  ],
  "generation_time": 18.3,
  "captain_diversity": 4
}
```

### Example 2: Locked Captain Showdown

```bash
# Generate lineups with Patrick Mahomes locked as captain
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "week_id": 9,
    "contest_mode": "showdown",
    "num_lineups": 5,
    "locked_captain_id": 123,
    "max_ownership": 30.0
  }'

# Response:
{
  "success": true,
  "contest_mode": "showdown",
  "lineups": [
    {
      "lineup_number": 1,
      "players": [
        { "id": 123, "name": "Patrick Mahomes", "is_captain": true, ... },
        // ... 5 FLEX players (vary across lineups)
      ]
    }
    // All 5 lineups use same captain, different FLEX
  ],
  "captain_diversity": 1
}
```

### Example 3: Multi-Mode Data Management

```bash
# Import Main Slate data for Week 9
curl -X POST "http://localhost:8000/api/import/linestar" \
  -F "file=@linestar_main_slate_week9.xlsx" \
  -F "week_id=9" \
  -F "contest_mode=main"

# Import Showdown data for Week 9 (same week, different mode)
curl -X POST "http://localhost:8000/api/import/linestar" \
  -F "file=@linestar_showdown_mnf_week9.xlsx" \
  -F "week_id=9" \
  -F "contest_mode=showdown"

# Both datasets coexist:
# - GET /api/players/9?contest_mode=main → 153 players (Sunday slate)
# - GET /api/players/9?contest_mode=showdown → 54 players (MNF)
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request: Invalid contest_mode

```json
{
  "success": false,
  "error": "Invalid contest_mode",
  "message": "contest_mode must be 'main' or 'showdown'",
  "status_code": 400
}
```

#### 400 Bad Request: Captain Selection Failed

```json
{
  "success": false,
  "error": "Cannot fit captain",
  "message": "Cannot fit any captain + 5 FLEX under $50k cap. Try widening Smart Score percentile filter.",
  "status_code": 400
}
```

#### 400 Bad Request: Locked Captain Invalid

```json
{
  "success": false,
  "error": "Captain lock prevents valid lineups",
  "message": "Captain salary $15,000 leaves $35,000, but cheapest 5 FLEX cost $38,000",
  "status_code": 400
}
```

#### 404 Not Found: No Players

```json
{
  "success": false,
  "error": "No players found",
  "message": "No showdown players found for Week 9. Import data first.",
  "status_code": 404
}
```

#### 500 Internal Server Error: Generation Failed

```json
{
  "success": false,
  "error": "Lineup generation failed",
  "message": "PuLP solver failed to find solution. Check constraints.",
  "status_code": 500,
  "details": "Solver status: Infeasible"
}
```

### Error Handling Best Practices

**Frontend Error Handling:**

```typescript
try {
  const response = await fetch('/api/lineups/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  });

  if (!response.ok) {
    const error = await response.json();

    if (error.error === 'Cannot fit captain') {
      // Suggest widening percentile filter
      showToast('No valid captain found. Try lowering Smart Score filter.');
    } else if (error.error === 'Captain lock prevents valid lineups') {
      // Suggest unlocking captain
      showToast('Locked captain too expensive. Unlock captain or choose cheaper player.');
    } else {
      // Generic error
      showToast(`Error: ${error.message}`);
    }

    return;
  }

  const lineups = await response.json();
  // Success handling
} catch (error) {
  console.error('Network error:', error);
  showToast('Failed to connect to server. Check internet connection.');
}
```

---

## Migration Guide

### For Existing API Consumers

**No Breaking Changes:**

All existing API calls continue to work without modification. The `contest_mode` parameter defaults to `'main'`, preserving pre-showdown behavior.

**Before (Main Slate Only):**

```bash
curl -X GET "http://localhost:8000/api/players/9"
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{"week_id": 9, "num_lineups": 10}'
```

**After (Main Slate + Showdown):**

```bash
# Same calls work identically (default: contest_mode='main')
curl -X GET "http://localhost:8000/api/players/9"
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{"week_id": 9, "num_lineups": 10}'

# NEW: Add contest_mode for showdown
curl -X GET "http://localhost:8000/api/players/9?contest_mode=showdown"
curl -X POST "http://localhost:8000/api/lineups/generate" \
  -H "Content-Type: application/json" \
  -d '{"week_id": 9, "contest_mode": "showdown", "num_lineups": 10}'
```

### Adding Showdown Support to Existing Client

**Step 1: Update Request Types**

```typescript
// Add contest_mode to request interfaces
interface GenerateLineupsRequest {
  week_id: number;
  contest_mode?: 'main' | 'showdown';  // NEW (optional)
  num_lineups: number;
  locked_captain_id?: number;  // NEW (showdown only)
  // ... other fields
}
```

**Step 2: Update Response Types**

```typescript
// Add is_captain to player interface
interface PlayerInLineup {
  id: number;
  name: string;
  // ... other fields
  is_captain: boolean;  // NEW
}
```

**Step 3: Update API Calls**

```typescript
// Add contest_mode to query params
export const getPlayers = async (weekId: number, contestMode: 'main' | 'showdown' = 'main') => {
  const response = await fetch(
    `/api/players/${weekId}?contest_mode=${contestMode}`
  );
  return response.json();
};

// Add contest_mode to request body
export const generateLineups = async (settings: GenerateLineupsRequest) => {
  const response = await fetch('/api/lineups/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...settings,
      contest_mode: settings.contest_mode || 'main'  // Default to 'main'
    })
  });
  return response.json();
};
```

**Step 4: Handle Captain Flag in UI**

```typescript
// Render lineup with captain badge
{lineup.players.map(player => (
  <div key={player.id}>
    {player.is_captain && <Badge>C</Badge>}
    <span>{player.name}</span>
    <span>{player.position}</span>
    <span>${player.salary.toLocaleString()}</span>
  </div>
))}
```

### Database Migration

**Required for On-Premise Deployments:**

```sql
-- Add contest_mode column to player_stats
ALTER TABLE player_stats
ADD COLUMN contest_mode VARCHAR(20) DEFAULT 'main' NOT NULL;

-- Add index for fast filtering
CREATE INDEX idx_player_stats_week_mode
ON player_stats(week_id, contest_mode);

-- Add contest_mode column to generated_lineups
ALTER TABLE generated_lineups
ADD COLUMN contest_mode VARCHAR(20) DEFAULT 'main' NOT NULL;

-- Add index
CREATE INDEX idx_generated_lineups_week_mode
ON generated_lineups(week_id, contest_mode);
```

**Using Alembic (Python):**

```bash
alembic upgrade head
```

---

## Appendix: API Versioning

**Current Version:** v1

**Future Versioning Strategy:**

If breaking changes required, version via URL path:

```
v1: /api/players/9
v2: /api/v2/players/9
```

Current showdown implementation maintains backward compatibility, so versioning not needed.

---

**API Documentation Complete**
**Last Updated:** November 2, 2025
**Version:** 1.0 (Initial Release)
