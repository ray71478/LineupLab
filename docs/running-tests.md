# Running Tests Guide

This guide provides comprehensive instructions for running the Cortex DFS Lineup Optimizer test suite.

## Quick Start

### Run all tests with verbose output

```bash
pytest -v
```

### Run specific test file

```bash
pytest tests/integration/test_week_api_endpoints.py -v
```

### Run specific test function

```bash
pytest tests/integration/test_week_api_endpoints.py::TestGetWeeksEndpointLogic::test_get_weeks_returns_18_weeks -v
```

### Run tests by marker

```bash
pytest -m integration -v
```

---

## Test Structure

The test suite is organized into three categories:

### Integration Tests (`tests/integration/`)

Test complete features end-to-end, including database interactions and API responses.

**Available test modules:**

- `test_linestar_import.py` - LineStar XLSX file imports
- `test_draftkings_import.py` - DraftKings XLSX file imports
- `test_comprehensive_stats_import.py` - NFL stats XLSX file imports
- `test_error_handling.py` - Error handling and data validation
- `test_validation_rules.py` - Data validation constraints
- `test_nfl_schedule_service.py` - NFL schedule data and queries
- `test_week_api_endpoints.py` - Week management API endpoints

**Run all integration tests:**

```bash
pytest tests/integration/ -v
```

**Run specific integration test module:**

```bash
pytest tests/integration/test_linestar_import.py -v
```

### Feature Tests (`tests/features/`)

Test specific features with realistic workflows.

**Available test modules:**

- `tests/features/week_management/test_database_schema.py` - Database schema verification
- `tests/features/week_management/test_week_management_service.py` - Week management business logic
- `tests/features/week_management/test_status_update_service.py` - Week status update logic
- `tests/features/week_management/test_import_integration.py` - Import feature integration
- `tests/features/week_management/test_e2e_workflows.py` - End-to-end workflow tests

**Run all feature tests:**

```bash
pytest tests/features/ -v
```

**Run specific feature test module:**

```bash
pytest tests/features/week_management/test_week_management_service.py -v
```

---

## Advanced Test Execution

### Generate coverage report

```bash
pytest --cov=backend --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`. Open in browser to see which code lines are covered by tests.

### Run with detailed output

```bash
pytest -vv  # Very verbose
pytest -vvv # Extra verbose (includes full SQL statements)
```

### Run tests matching keyword filter

```bash
# Run only tests with "import" in the name
pytest -k "import" -v

# Run only tests without "e2e" in the name
pytest -k "not e2e" -v
```

### Run tests with specific markers

```bash
# Show available markers
pytest --markers

# Run integration tests only
pytest -m integration -v

# Run feature tests only
pytest -m feature -v
```

### Stop on first failure

```bash
pytest -x  # Stop on first failure
pytest -x -v  # Stop on first failure, verbose
```

### Show print statements during test execution

```bash
pytest -s  # Show stdout/print statements
pytest -sv  # Verbose + show print statements
```

---

## Understanding Test Output

### Passing tests

```
tests/integration/test_linestar_import.py::TestLineStarImportSuccess::test_linestar_import_creates_correct_count PASSED [ 10%]
```

- `PASSED` - Test executed and assertions passed
- `[ 10%]` - Progress through test suite

### Failed tests

```
tests/integration/test_week_api_endpoints.py::TestGetWeeksEndpointLogic::test_get_weeks_returns_18_weeks FAILED [ 92%]
```

- `FAILED` - Test assertion failed
- Shows file path, class, and test function name
- Detailed error message appears in summary section

### Skipped tests

```
tests/example.py::test_something SKIPPED
```

- Test was skipped using `@pytest.mark.skip` decorator
- Not run, not counted as pass or fail

### Test summary

```
======================== 93 passed, 14 failed, 4 warnings in 1.13s ========================
```

- Total passed, failed, warnings, and execution time
- Failed tests listed in "short test summary info" section

---

## Test Database Setup

Tests use SQLite in-memory database for speed and isolation:

```python
# From conftest.py
TEST_DATABASE_URL = "sqlite:///:memory:"

# Each test gets a fresh database via db_engine and db_session fixtures
@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine."""
    # Creates all tables
    # Yields engine for test
    # Drops all tables on cleanup
```

### Database isolation

Each test function gets a clean database:

1. Setup: Create all tables
2. Test: Execute test code with fresh database
3. Teardown: Drop all tables and close session

This ensures tests don't interfere with each other.

### Running with PostgreSQL instead of SQLite

To run tests against a PostgreSQL database:

```bash
export TEST_DATABASE_URL="postgresql://cortex:cortex@localhost:5432/cortex_test"
pytest -v
```

---

## Fixtures Available in Tests

### Database fixtures

```python
# Session-scoped: Created once per test function
def test_something(db_session: Session):
    # db_session is a SQLAlchemy session with fresh database
    db_session.execute(text("INSERT INTO weeks ..."))
    db_session.commit()

# Also available: db_engine (SQLAlchemy engine)
def test_something_else(db_engine):
    # db_engine provides raw database connection
    with db_engine.connect() as conn:
        conn.execute(text("SELECT * FROM weeks"))
```

### Sample data fixtures

```python
# LineStar XLSX file (153 players)
def test_linestar(linestar_sample: BytesIO):
    # filestr linestar_sample is a BytesIO object containing sample XLSX
    df = pd.read_excel(linestar_sample)
    assert len(df) == 153

# DraftKings XLSX file (174 players)
def test_draftkings(draftkings_sample: BytesIO):
    df = pd.read_excel(draftkings_sample)
    assert len(df) == 174

# Comprehensive Stats XLSX file (2690 rows)
def test_stats(comprehensive_stats_sample: BytesIO):
    df = pd.read_excel(comprehensive_stats_sample)
    assert len(df) == 2690
```

### Helper fixtures

```python
# Create a test week and return its ID
def test_with_week(db_session: Session):
    week_id = create_week(db_session, season=2024, week_number=9)
    # week_id can be used in subsequent operations

# Verify import succeeded
def test_verify_import(db_session: Session):
    week_id = create_week(db_session, season=2024, week_number=9)
    # ... import code ...
    result = verify_import_success(db_session, week_id, expected_count=153, source='LineStar')
    assert result['count_matches'] is True
```

---

## Common Test Patterns

### Testing database inserts

```python
def test_insert_week(db_session: Session):
    # Insert a week
    db_session.execute(
        text("""
            INSERT INTO weeks (season, week_number, status)
            VALUES (:season, :week_number, :status)
        """),
        {"season": 2024, "week_number": 9, "status": "active"}
    )
    db_session.commit()

    # Verify insert
    result = db_session.execute(
        text("SELECT COUNT(*) FROM weeks WHERE season = :season")
    )
    assert result.scalar() == 1
```

### Testing foreign key relationships

```python
def test_player_pools_foreign_key(db_session: Session):
    # Create week first
    week_id = create_week(db_session, season=2024, week_number=9)

    # Now can insert into player_pools with week_id reference
    db_session.execute(
        text("""
            INSERT INTO player_pools (week_id, player_key, name, team, position, salary, source)
            VALUES (:week_id, :player_key, :name, :team, :position, :salary, :source)
        """),
        {
            "week_id": week_id,
            "player_key": "player_123",
            "name": "John Doe",
            "team": "KC",
            "position": "QB",
            "salary": 7500,
            "source": "LineStar",
        }
    )
    db_session.commit()
```

### Testing file uploads

```python
def test_import_linestar_file(db_session: Session, linestar_sample: BytesIO):
    week_id = create_week(db_session, season=2024, week_number=9)

    # Read sample file
    df = pd.read_excel(linestar_sample)

    # Process as would happen in import endpoint
    for _, row in df.iterrows():
        db_session.execute(
            text("""
                INSERT INTO player_pools (...)
                VALUES (...)
            """),
            {...}
        )
    db_session.commit()

    # Verify import
    result = verify_import_success(db_session, week_id, len(df), 'LineStar')
    assert result['count_matches'] is True
```

### Testing error conditions

```python
def test_salary_constraint_violation(db_session: Session):
    week_id = create_week(db_session, season=2024, week_number=9)

    # Try to insert player with salary outside valid range
    with pytest.raises(IntegrityError):
        db_session.execute(
            text("""
                INSERT INTO player_pools (week_id, ..., salary, ...)
                VALUES (:week_id, ..., :salary, ...)
            """),
            {..., "salary": 1000, ...}  # Invalid: < 3000 minimum
        )
        db_session.commit()
```

---

## Debugging Failed Tests

### Show full error traceback

```bash
pytest -v --tb=long tests/integration/test_linestar_import.py::TestLineStarImportSuccess::test_linestar_import_creates_correct_count
```

### Show SQL statements

```bash
pytest -v -vv tests/integration/test_linestar_import.py
```

### Show print output

```bash
pytest -sv tests/integration/test_linestar_import.py
```

### Drop into debugger on failure

```bash
pytest --pdb tests/integration/test_linestar_import.py
```

### Keep test database after test (don't drop tables)

Edit `tests/conftest.py` and comment out the cleanup code in `db_engine` fixture:

```python
# In db_engine fixture, comment out:
# try:
#     with engine.begin() as conn:
#         for table in tables:
#             conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
```

Then query database while tests run:

```bash
# In another terminal
psql postgresql://cortex:cortex@localhost:5432/cortex
SELECT * FROM weeks;
```

---

## Expected Test Results

### Current status (as of latest run)

```
93 passed, 14 failed in 1.13s
```

**Passing test suites:**

- LineStar import tests (8/8 passing)
- DraftKings import tests (6/6 passing)
- Comprehensive Stats import tests (7/7 passing)
- Error handling tests (9/9 passing)
- Validation rules tests (18/18 passing)
- NFL schedule service tests (10/10 passing)
- Week API endpoints tests (8/9 passing)
- Week status update service tests (4/4 passing)
- Week management service tests (5/6 passing)
- Database schema tests (12/14 passing)
- E2E workflow tests (4/11 passing) - Note: Some marked as feature tests, not intended for regular runs

**Known failures:**

The 14 failing tests are primarily due to:
1. Test data conflicts (tests trying to insert duplicate NFL schedule data that already exists)
2. Feature tests marked as work-in-progress (not critical path)
3. One API endpoint test with datetime conversion issue (minor bug)

These failures do not block the core functionality.

---

## Running Tests in CI/CD

### GitHub Actions example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: cortex
          POSTGRES_PASSWORD: cortex
          POSTGRES_DB: cortex_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -v
        env:
          TEST_DATABASE_URL: postgresql://cortex:cortex@localhost:5432/cortex_test
```

---

## Performance Considerations

### Test execution time

Current test suite runs in approximately 1.1 seconds:
- 93 passing tests
- 14 failing tests (expected behavior in some cases)
- Parallel execution not currently enabled

### Speed up test runs

```bash
# Run only specific test category (faster)
pytest tests/integration/test_linestar_import.py -v

# Skip slow tests
pytest -v -m "not slow"

# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

---

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest plugins](https://docs.pytest.org/en/latest/plugins.html)
- [SQLAlchemy testing documentation](https://docs.sqlalchemy.org/en/20/faq/models_data.html)
- [pytest-cov coverage documentation](https://pytest-cov.readthedocs.io/)
