# Backend API Endpoint Verification Guide

This guide provides step-by-step instructions for manually verifying all backend API endpoints using Swagger UI and curl commands.

## Prerequisites

- Backend server running on `http://localhost:8000`
- PostgreSQL database running with migrations applied
- Sample data seeded (optional)

## Starting the Backend Server

### Step 1: Ensure database is running

```bash
# Start PostgreSQL container if using Docker
docker-compose up -d

# Wait 10 seconds for database to be healthy
sleep 10
```

### Step 2: Apply migrations

```bash
alembic upgrade head
```

### Step 3: Optional - Seed development data

```bash
python backend/scripts/seed_development_data.py
```

### Step 4: Start FastAPI backend server

```bash
# In terminal 1
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete
```

### Step 5: Access Swagger UI

Open browser to: **http://localhost:8000/docs**

You should see interactive API documentation with all endpoints listed.

---

## API Endpoint Verification Checklist

### Endpoint: GET /api/weeks

**Purpose:** List all weeks for a given season

**Swagger UI Steps:**

1. Click on "GET /api/weeks" to expand
2. Click "Try it out"
3. Enter query parameters:
   - `season`: 2024
   - `year`: 2024 (optional, alternative parameter name)
4. Click "Execute"

**Expected Response (200 OK):**

```json
{
  "weeks": [
    {
      "id": 1,
      "season": 2024,
      "week_number": 1,
      "status": "upcoming",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    },
    {
      "id": 2,
      "season": 2024,
      "week_number": 2,
      "status": "upcoming",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
    // ... more weeks (18 total)
  ],
  "total": 18,
  "season": 2024
}
```

**curl command:**

```bash
curl -X GET "http://localhost:8000/api/weeks?season=2024" \
  -H "Accept: application/json"
```

**Verification:**

- [ ] Response status is 200
- [ ] Response contains array of weeks
- [ ] Each week has required fields (id, season, week_number, status)
- [ ] Total weeks equals 18
- [ ] Season matches request parameter

---

### Endpoint: GET /api/weeks/{week_id}

**Purpose:** Get specific week details

**Swagger UI Steps:**

1. Click on "GET /api/weeks/{week_id}" to expand
2. Click "Try it out"
3. Enter path parameter:
   - `week_id`: 1
4. Click "Execute"

**Expected Response (200 OK):**

```json
{
  "id": 1,
  "season": 2024,
  "week_number": 1,
  "status": "upcoming",
  "nfl_slate_date": "2024-09-05",
  "is_locked": false,
  "metadata": {},
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**curl command:**

```bash
curl -X GET "http://localhost:8000/api/weeks/1" \
  -H "Accept: application/json"
```

**Verification:**

- [ ] Response status is 200
- [ ] Response contains week details
- [ ] week_id matches request parameter
- [ ] All expected fields present
- [ ] Timestamps are valid ISO format

---

### Endpoint: POST /api/weeks

**Purpose:** Create a new week

**Swagger UI Steps:**

1. Click on "POST /api/weeks" to expand
2. Click "Try it out"
3. Enter request body:

```json
{
  "season": 2024,
  "week_number": 10,
  "status": "upcoming"
}
```

4. Click "Execute"

**Expected Response (201 Created):**

```json
{
  "id": 19,
  "season": 2024,
  "week_number": 10,
  "status": "upcoming",
  "created_at": "2025-10-29T12:00:00",
  "updated_at": "2025-10-29T12:00:00"
}
```

**curl command:**

```bash
curl -X POST "http://localhost:8000/api/weeks" \
  -H "Content-Type: application/json" \
  -d '{
    "season": 2024,
    "week_number": 10,
    "status": "upcoming"
  }'
```

**Verification:**

- [ ] Response status is 201 (Created)
- [ ] Response contains new week with id assigned
- [ ] Season and week_number match request
- [ ] Created_at timestamp is recent

**Verify in database:**

```sql
SELECT * FROM weeks WHERE season = 2024 AND week_number = 10;
```

Expected output:

```
 id | season | week_number | status | created_at
────┼────────┼─────────────┼────────┼────────────────────
 19 |   2024 |          10 | upcoming | 2025-10-29 12:00:00
```

---

### Endpoint: PATCH /api/weeks/{week_id}

**Purpose:** Update week status

**Swagger UI Steps:**

1. Click on "PATCH /api/weeks/{week_id}" to expand
2. Click "Try it out"
3. Enter path parameter:
   - `week_id`: 1
4. Enter request body:

```json
{
  "status": "active"
}
```

5. Click "Execute"

**Expected Response (200 OK):**

```json
{
  "id": 1,
  "season": 2024,
  "week_number": 1,
  "status": "active",
  "updated_at": "2025-10-29T12:01:00"
}
```

**curl command:**

```bash
curl -X PATCH "http://localhost:8000/api/weeks/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active"
  }'
```

**Verification:**

- [ ] Response status is 200
- [ ] Status field updated to new value
- [ ] Updated_at timestamp is recent

**Verify in database:**

```sql
SELECT status, updated_at FROM weeks WHERE id = 1;
```

---

### Endpoint: POST /api/import/linestar

**Purpose:** Upload LineStar XLSX player file

**Prerequisites:**

1. Create or prepare a LineStar XLSX file with columns:
   - Name, Position, Team, Salary, Projected, Ceiling, Floor, ProjOwn

2. Or use the test fixture file generated by conftest.py

**Swagger UI Steps:**

1. Click on "POST /api/import/linestar" to expand
2. Click "Try it out"
3. Enter query parameter:
   - `week_id`: 1
4. Select file:
   - Click "Select File" button
   - Choose LineStar XLSX file
5. Click "Execute"

**Expected Response (200 OK):**

```json
{
  "success": true,
  "message": "Import successful",
  "import_id": "import_uuid_12345",
  "player_count": 153,
  "unmatched_count": 0,
  "week_id": 1,
  "source": "LineStar",
  "timestamp": "2025-10-29T12:02:00"
}
```

**curl command:**

```bash
curl -X POST "http://localhost:8000/api/import/linestar?week_id=1" \
  -F "file=@linestar_data.xlsx"
```

**Verification:**

- [ ] Response status is 200
- [ ] Success is true
- [ ] Player count matches expected (typically 153 for LineStar)
- [ ] Unmatched count is 0 or documented

**Verify in database:**

```sql
-- Check players inserted
SELECT COUNT(*) FROM player_pools WHERE week_id = 1 AND source = 'LineStar';

-- Expected result: 153 (or actual count from file)

-- Check import history
SELECT * FROM import_history WHERE week_id = 1 AND source = 'LineStar' ORDER BY created_at DESC LIMIT 1;

-- Expected: Record with player_count = 153, source = 'LineStar'
```

---

### Endpoint: POST /api/import/draftkings

**Purpose:** Upload DraftKings XLSX player file

**Expected Response (200 OK):**

```json
{
  "success": true,
  "message": "Import successful",
  "import_id": "import_uuid_12346",
  "player_count": 174,
  "unmatched_count": 0,
  "week_id": 1,
  "source": "DraftKings",
  "timestamp": "2025-10-29T12:03:00"
}
```

**curl command:**

```bash
curl -X POST "http://localhost:8000/api/import/draftkings?week_id=1" \
  -F "file=@draftkings_data.xlsx"
```

**Verification:**

- [ ] Response status is 200
- [ ] Player count matches expected (typically 174 for DraftKings)
- [ ] Source field is "DraftKings"

**Verify in database:**

```sql
SELECT COUNT(*) FROM player_pools WHERE week_id = 1 AND source = 'DraftKings';
```

---

### Endpoint: POST /api/import/comprehensive-stats

**Purpose:** Upload NFL stats XLSX file

**Expected Response (200 OK):**

```json
{
  "success": true,
  "message": "Import successful",
  "import_id": "import_uuid_12347",
  "stats_count": 2690,
  "week_id": 1,
  "source": "Stats",
  "timestamp": "2025-10-29T12:04:00"
}
```

**curl command:**

```bash
curl -X POST "http://localhost:8000/api/import/comprehensive-stats?week_id=1" \
  -F "file=@nfl_stats.xlsx"
```

**Verification:**

- [ ] Response status is 200
- [ ] Stats count matches expected (typically 2690 total rows)

**Verify in database:**

```sql
SELECT COUNT(*) FROM historical_stats WHERE week_id = 1;
```

---

### Endpoint: GET /api/import/history

**Purpose:** View import history

**Swagger UI Steps:**

1. Click on "GET /api/import/history" to expand
2. Click "Try it out"
3. Optional query parameters:
   - `limit`: 10
   - `offset`: 0
4. Click "Execute"

**Expected Response (200 OK):**

```json
{
  "imports": [
    {
      "id": "import_uuid_12347",
      "week_id": 1,
      "source": "Stats",
      "player_count": 2690,
      "unmatched_count": 0,
      "created_at": "2025-10-29T12:04:00",
      "metadata": {}
    },
    {
      "id": "import_uuid_12346",
      "week_id": 1,
      "source": "DraftKings",
      "player_count": 174,
      "unmatched_count": 0,
      "created_at": "2025-10-29T12:03:00",
      "metadata": {}
    },
    {
      "id": "import_uuid_12345",
      "week_id": 1,
      "source": "LineStar",
      "player_count": 153,
      "unmatched_count": 0,
      "created_at": "2025-10-29T12:02:00",
      "metadata": {}
    }
  ],
  "total": 3
}
```

**curl command:**

```bash
curl -X GET "http://localhost:8000/api/import/history?limit=10" \
  -H "Accept: application/json"
```

**Verification:**

- [ ] Response status is 200
- [ ] Import records listed in reverse chronological order (newest first)
- [ ] Each import has required fields

**Verify in database:**

```sql
SELECT id, week_id, source, player_count, created_at
FROM import_history
ORDER BY created_at DESC LIMIT 10;
```

---

## Error Response Testing

### Test 404 Error (Week not found)

**Request:**

```bash
curl -X GET "http://localhost:8000/api/weeks/99999"
```

**Expected Response (404 Not Found):**

```json
{
  "success": false,
  "error": "Week not found",
  "detail": "No week found with ID 99999"
}
```

**Verification:**

- [ ] Response status is 404
- [ ] Error message is clear and helpful

### Test 400 Error (Invalid input)

**Request:**

```bash
curl -X POST "http://localhost:8000/api/weeks" \
  -H "Content-Type: application/json" \
  -d '{
    "season": 2024,
    "week_number": 99,
    "status": "upcoming"
  }'
```

**Expected Response (400 Bad Request):**

```json
{
  "success": false,
  "error": "Validation error",
  "detail": "week_number must be between 1 and 18"
}
```

**Verification:**

- [ ] Response status is 400
- [ ] Error explains what's wrong with input
- [ ] Helpful hint for valid values

### Test 409 Error (Duplicate)

**Request (create same week twice):**

```bash
# First request - succeeds
curl -X POST "http://localhost:8000/api/weeks" \
  -H "Content-Type: application/json" \
  -d '{
    "season": 2024,
    "week_number": 15,
    "status": "upcoming"
  }'

# Second request - fails
curl -X POST "http://localhost:8000/api/weeks" \
  -H "Content-Type: application/json" \
  -d '{
    "season": 2024,
    "week_number": 15,
    "status": "upcoming"
  }'
```

**Expected Response (409 Conflict):**

```json
{
  "success": false,
  "error": "Duplicate entry",
  "detail": "Week 15 of season 2024 already exists"
}
```

**Verification:**

- [ ] First request returns 201
- [ ] Second request returns 409
- [ ] Error message explains conflict

---

## Database Verification After API Calls

### After importing players:

```sql
-- Verify players inserted
SELECT COUNT(*) as linestar_count FROM player_pools WHERE source = 'LineStar';
SELECT COUNT(*) as draftkings_count FROM player_pools WHERE source = 'DraftKings';

-- Verify import history
SELECT source, player_count, created_at FROM import_history ORDER BY created_at DESC;

-- Verify player data integrity
SELECT MIN(salary), MAX(salary) FROM player_pools;
-- Should be 3000 (min) to 10000 (max)

-- Verify foreign keys
SELECT COUNT(*) as orphaned FROM player_pools WHERE week_id NOT IN (SELECT id FROM weeks);
-- Should be 0
```

---

## Load Testing (Optional)

Test API performance with multiple requests:

```bash
# Test 10 requests to GET /api/weeks endpoint
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/weeks?season=2024" \
    -H "Accept: application/json" > /dev/null
  echo "Request $i completed"
done

# Using Apache Bench (if installed)
ab -n 100 -c 10 "http://localhost:8000/api/weeks?season=2024"

# Using wrk (if installed)
wrk -t4 -c100 -d30s "http://localhost:8000/api/weeks?season=2024"
```

---

## Common Issues and Troubleshooting

### Issue: Connection refused (localhost:8000)

**Solution:**
```bash
# Verify server is running
ps aux | grep uvicorn

# Or check port is listening
lsof -i :8000
```

### Issue: Database connection error

**Solution:**
```bash
# Verify PostgreSQL is running
docker-compose logs postgres

# Check environment variables
echo $DATABASE_URL

# Verify migrations
alembic current
```

### Issue: 422 Unprocessable Entity (validation error)

**Solution:**
```bash
# Check request format matches Swagger schema
# Common issues:
# - Missing required fields
# - Wrong data type (string instead of number)
# - Invalid enum values (status must be 'upcoming', 'active', or 'completed')
```

### Issue: 413 Payload Too Large

**Solution:**
```bash
# File upload too large
# Reduce file size or increase server limits in main.py
```

---

## API Documentation

Full interactive API documentation available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Swagger/OpenAPI Documentation](https://swagger.io/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [curl Documentation](https://curl.se/docs/)
