# Database Setup & SQL Client Connection Guide

This guide provides detailed instructions for connecting to the Cortex PostgreSQL database using popular SQL clients (pgAdmin, DBeaver, and psql command-line tool).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Starting the Database](#starting-the-database)
- [Connection Information](#connection-information)
- [SQL Client Connection Guides](#sql-client-connection-guides)
  - [pgAdmin Connection](#pgadmin-connection)
  - [DBeaver Connection](#dbeaver-connection)
  - [psql Command-Line Connection](#psql-command-line-connection)
- [Common SQL Queries for Verification](#common-sql-queries-for-verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before connecting to the database, ensure you have:

1. **Docker Desktop installed and running**
   - Download from: https://www.docker.com/products/docker-desktop
   - Verify Docker is running: `docker info`

2. **PostgreSQL database started via Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Database initialized with schema**
   ```bash
   ./init_db.sh
   ```

4. **A SQL client installed** (choose one):
   - **pgAdmin** (recommended for beginners): https://www.pgadmin.org/download/
   - **DBeaver** (recommended for advanced users): https://dbeaver.io/download/
   - **psql** (command-line tool, included with PostgreSQL): Installed automatically if you have PostgreSQL on your system

---

## Starting the Database

### Start PostgreSQL Container

```bash
# Start PostgreSQL in detached mode (runs in background)
docker-compose up -d

# View logs to verify PostgreSQL started successfully
docker-compose logs -f postgres

# Check PostgreSQL health status
docker-compose ps
```

Expected output:
```
NAME                IMAGE           STATUS                    PORTS
cortex-postgres     postgres:15     Up 10 seconds (healthy)   0.0.0.0:5432->5432/tcp
```

### Initialize Database Schema

```bash
# Run migrations to create all tables
./init_db.sh

# Or run migrations with development seed data
./init_db.sh --seed
```

---

## Connection Information

Use these credentials to connect to the PostgreSQL database:

| Parameter | Value |
|-----------|-------|
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `cortex` |
| **Username** | `cortex` |
| **Password** | `cortex` |

**Connection String Format:**
```
postgresql://cortex:cortex@localhost:5432/cortex
```

**Note:** These are development credentials. Production credentials should be stored securely in environment variables and never committed to version control.

---

## SQL Client Connection Guides

### pgAdmin Connection

pgAdmin is a popular open-source graphical administration tool for PostgreSQL.

#### Step 1: Download and Install pgAdmin

- **Download:** https://www.pgadmin.org/download/
- **Install:** Follow installation instructions for your operating system

#### Step 2: Launch pgAdmin

- Open pgAdmin from your Applications folder or Start menu
- Wait for pgAdmin to load (it opens in your web browser)

#### Step 3: Create New Server Connection

1. In the pgAdmin left sidebar, right-click **Servers** → **Register** → **Server...**

2. **General Tab:**
   - **Name:** `Cortex Local` (or any name you prefer)

3. **Connection Tab:**
   - **Host name/address:** `localhost`
   - **Port:** `5432`
   - **Maintenance database:** `cortex`
   - **Username:** `cortex`
   - **Password:** `cortex`
   - ✅ Check **Save password** (optional, for convenience)

4. Click **Save**

#### Step 4: Verify Connection

1. In the left sidebar, expand **Servers** → **Cortex Local**
2. Expand **Databases** → **cortex**
3. Expand **Schemas** → **public** → **Tables**

You should see 7 tables:
- `weeks`
- `player_pools`
- `historical_stats`
- `vegas_lines`
- `generated_lineups`
- `weight_profiles`
- `player_aliases`

#### Step 5: Query Data

1. Right-click on a table (e.g., `weeks`) → **View/Edit Data** → **All Rows**
2. Data will appear in the right panel

To run custom SQL queries:
1. Click **Tools** → **Query Tool**
2. Enter your SQL query (see [Common SQL Queries](#common-sql-queries-for-verification))
3. Click ▶️ **Execute/Refresh** or press `F5`

---

### DBeaver Connection

DBeaver is a universal database tool that supports many database systems.

#### Step 1: Download and Install DBeaver

- **Download:** https://dbeaver.io/download/
- **Install:** Follow installation instructions for your operating system
- **Choose Edition:** Community Edition (free) is sufficient

#### Step 2: Launch DBeaver

- Open DBeaver from your Applications folder or Start menu

#### Step 3: Create New Database Connection

1. Click **Database** → **New Database Connection** (or click the ➕ icon in the toolbar)

2. **Select Database Type:**
   - Select **PostgreSQL**
   - Click **Next**

3. **Connection Settings:**
   - **Host:** `localhost`
   - **Port:** `5432`
   - **Database:** `cortex`
   - **Username:** `cortex`
   - **Password:** `cortex`
   - ✅ Check **Save password** (optional)

4. Click **Test Connection**
   - If successful, you'll see "Connected" message
   - If prompted to download PostgreSQL driver, click **Download**

5. Click **Finish**

#### Step 4: Verify Connection

1. In the left sidebar (Database Navigator), expand **PostgreSQL - cortex** → **Databases** → **cortex**
2. Expand **Schemas** → **public** → **Tables**

You should see 7 tables:
- `weeks`
- `player_pools`
- `historical_stats`
- `vegas_lines`
- `generated_lineups`
- `weight_profiles`
- `player_aliases`

#### Step 5: Query Data

To view table data:
1. Right-click on a table (e.g., `weeks`) → **View Data**
2. Data will appear in the right panel

To run custom SQL queries:
1. Click **SQL Editor** → **New SQL Script** (or press `Ctrl+]` / `Cmd+]`)
2. Enter your SQL query (see [Common SQL Queries](#common-sql-queries-for-verification))
3. Click ▶️ **Execute SQL Statement** or press `Ctrl+Enter` / `Cmd+Enter`

---

### psql Command-Line Connection

`psql` is the PostgreSQL interactive terminal. It's powerful for quick queries and scripting.

#### Option 1: Connect via Docker Compose (Recommended)

This method doesn't require PostgreSQL installed on your local machine:

```bash
# Connect to PostgreSQL inside the Docker container
docker-compose exec postgres psql -U cortex -d cortex
```

You should see the psql prompt:
```
psql (15.x)
Type "help" for help.

cortex=#
```

#### Option 2: Connect via Local psql (Requires PostgreSQL Installed)

If you have PostgreSQL installed locally:

```bash
# Connect using connection string
psql postgresql://cortex:cortex@localhost:5432/cortex

# Or using individual parameters
psql -h localhost -p 5432 -U cortex -d cortex
```

#### Common psql Commands

Once connected, use these commands:

```sql
-- List all tables in current database
\dt

-- Describe a specific table (show columns, types, constraints)
\d weeks

-- List all databases
\l

-- List all schemas
\dn

-- Show current connection info
\conninfo

-- Execute a SQL query
SELECT * FROM weeks;

-- Quit psql
\q
```

---

## Common SQL Queries for Verification

Use these queries to verify your database setup:

### 1. Check All Tables Exist

```sql
-- Should return 7 tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Expected result:
```
 table_name
------------------
 generated_lineups
 historical_stats
 player_aliases
 player_pools
 vegas_lines
 weeks
 weight_profiles
```

### 2. Check Weeks Table

```sql
-- Count total weeks
SELECT COUNT(*) as total_weeks FROM weeks;

-- View all weeks for 2024 season
SELECT id, season, week_number, status, kickoff_time
FROM weeks
WHERE season = 2024
ORDER BY week_number;

-- Check week status distribution
SELECT status, COUNT(*) as count
FROM weeks
GROUP BY status;
```

### 3. Check Player Pools Table

```sql
-- Count players by week and source
SELECT w.season, w.week_number, pp.source, COUNT(*) as player_count
FROM player_pools pp
JOIN weeks w ON pp.week_id = w.id
GROUP BY w.season, w.week_number, pp.source
ORDER BY w.season, w.week_number, pp.source;

-- View sample player data for a specific week
SELECT name, position, team, salary, projection, ownership
FROM player_pools
WHERE week_id = (SELECT id FROM weeks WHERE season = 2024 AND week_number = 9 LIMIT 1)
  AND source = 'LineStar'
ORDER BY salary DESC
LIMIT 10;
```

### 4. Check Import History

```sql
-- View import history (if import_history table exists)
SELECT import_date, source, week_id, total_players, matched_players, status
FROM import_history
ORDER BY import_date DESC
LIMIT 10;
```

### 5. Check Historical Stats

```sql
-- Count historical stats entries
SELECT COUNT(*) as total_records FROM historical_stats;

-- View historical stats for a specific player
SELECT player_name, week_id, fantasy_points, targets, receptions, yards, touchdowns
FROM historical_stats
WHERE player_name ILIKE '%patrick mahomes%'
ORDER BY week_id DESC
LIMIT 10;
```

### 6. Check Database Size and Statistics

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('cortex')) as database_size;

-- Table sizes
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Row counts for all tables
SELECT
    table_name,
    (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
FROM (
    SELECT table_name,
           query_to_xml(format('SELECT COUNT(*) as cnt FROM %I.%I',
                               table_schema, table_name), false, true, '') as xml_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
) t
ORDER BY row_count DESC;
```

### 7. Verify Foreign Key Relationships

```sql
-- Check player_pools foreign key to weeks
SELECT
    pp.id as player_pool_id,
    pp.name,
    pp.week_id,
    w.season,
    w.week_number
FROM player_pools pp
JOIN weeks w ON pp.week_id = w.id
LIMIT 5;

-- Verify no orphaned records (should return 0)
SELECT COUNT(*)
FROM player_pools pp
WHERE NOT EXISTS (SELECT 1 FROM weeks w WHERE w.id = pp.week_id);
```

---

## Troubleshooting

### Issue: Cannot Connect to Database

**Symptoms:**
- Connection timeout
- "Could not connect to server" error
- "Connection refused" error

**Solutions:**

1. **Check if Docker is running:**
   ```bash
   docker info
   ```
   If this fails, start Docker Desktop.

2. **Check if PostgreSQL container is running:**
   ```bash
   docker-compose ps
   ```
   If status is not "Up (healthy)", restart:
   ```bash
   docker-compose restart postgres
   ```

3. **Check PostgreSQL logs for errors:**
   ```bash
   docker-compose logs postgres
   ```

4. **Verify port 5432 is not in use by another PostgreSQL instance:**
   ```bash
   # On macOS/Linux
   lsof -i :5432

   # On Windows
   netstat -ano | findstr :5432
   ```
   If another process is using port 5432, either stop it or change the port in `docker-compose.yml`.

5. **Check if PostgreSQL health check is passing:**
   ```bash
   docker-compose exec postgres pg_isready -U cortex -d cortex
   ```
   Should return: `postgres:5432 - accepting connections`

---

### Issue: Authentication Failed

**Symptoms:**
- "password authentication failed for user cortex"
- "FATAL: password authentication failed"

**Solutions:**

1. **Verify credentials match docker-compose.yml:**
   - Username: `cortex`
   - Password: `cortex`
   - Database: `cortex`

2. **Reset database and container:**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ./init_db.sh
   ```

---

### Issue: Tables Don't Exist

**Symptoms:**
- "relation 'weeks' does not exist"
- No tables visible in SQL client
- Table list is empty

**Solutions:**

1. **Run Alembic migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Or use init_db.sh script:**
   ```bash
   ./init_db.sh
   ```

3. **Verify migrations were applied:**
   ```bash
   alembic current
   ```
   Should show: `003_seed_nfl_schedule (head)`

4. **Check migration history:**
   ```bash
   alembic history
   ```

---

### Issue: No Data in Tables

**Symptoms:**
- Tables exist but are empty
- `SELECT COUNT(*) FROM weeks;` returns 0

**Solutions:**

1. **Check if NFL schedule seed migration ran:**
   ```bash
   alembic current
   ```
   If you see `002_extend_weeks_system` but not `003_seed_nfl_schedule`, run:
   ```bash
   alembic upgrade head
   ```

2. **The weeks table is seeded via migration 003_seed_nfl_schedule.**
   If weeks are missing, downgrade and re-run:
   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

3. **For player data, you must import files via the API:**
   - Use the Import Data button in the frontend
   - Or use the API directly: `POST /api/import/linestar` with XLSX file
   - Player data is not automatically seeded

---

### Issue: Docker Compose Command Not Found

**Symptoms:**
- `docker-compose: command not found`

**Solutions:**

1. **For Docker Desktop (newer versions), use:**
   ```bash
   docker compose up -d
   # Note: no hyphen, uses Docker Compose V2
   ```

2. **Or install Docker Compose V1:**
   ```bash
   # macOS (via Homebrew)
   brew install docker-compose

   # Linux
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

---

### Issue: Database Reset Needed

**Symptoms:**
- Corrupted data
- Migration conflicts
- Need to start fresh

**Solutions:**

1. **Reset database with confirmation prompt:**
   ```bash
   ./init_db.sh --reset
   ```
   This will:
   - Stop PostgreSQL container
   - Delete all data (WARNING: irreversible)
   - Start fresh container
   - Run migrations

2. **Manual reset (alternative):**
   ```bash
   docker-compose down -v
   rm -rf ./data
   docker-compose up -d
   ./init_db.sh
   ```

---

## Additional Resources

- **PostgreSQL Documentation:** https://www.postgresql.org/docs/15/
- **pgAdmin Documentation:** https://www.pgadmin.org/docs/
- **DBeaver Documentation:** https://dbeaver.com/docs/
- **Docker Compose Documentation:** https://docs.docker.com/compose/

---

## Next Steps

After connecting to the database:

1. **Verify schema:** Run the SQL queries in [Common SQL Queries](#common-sql-queries-for-verification)
2. **Test API endpoints:** Start the backend server and test via Swagger UI at http://localhost:8000/docs
3. **Import data:** Use the Import Data button in the frontend to upload player data
4. **Run tests:** Execute `pytest -v` to verify backend functionality

---

**Questions or Issues?**

If you encounter any problems not covered in this guide, check:
- Docker logs: `docker-compose logs postgres`
- Backend logs when running API
- PostgreSQL logs inside container: `docker-compose exec postgres cat /var/lib/postgresql/data/log/postgresql-*.log`
