## API endpoint standards and conventions

### General Principles
- **RESTful Design**: Follow REST principles with clear resource-based URLs and appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **Consistent Naming**: Use lowercase, hyphenated naming for endpoints (e.g., `/api/smart-score/calculate`)
- **API Prefix**: All endpoints start with `/api/` for clear separation from frontend routes
- **Versioning**: No versioning in MVP (local-first); implement in Phase 3 if needed (e.g., `/api/v1/`)
- **Plural Nouns**: Use plural nouns for resource endpoints (e.g., `/api/weeks`, `/api/players`, `/api/lineups`)
- **Nested Resources**: Limit nesting to 2 levels maximum (e.g., `/api/weeks/{week_id}/players`)
- **Query Parameters**: Use query parameters for filtering, sorting, pagination (e.g., `/api/players?week_id=9&position=QB`)
- **HTTP Status Codes**: Return appropriate codes:
  - `200 OK` - Successful GET/PATCH
  - `201 Created` - Successful POST
  - `204 No Content` - Successful DELETE
  - `400 Bad Request` - Validation errors
  - `404 Not Found` - Resource not found
  - `422 Unprocessable Entity` - Business logic errors (e.g., salary cap exceeded)
  - `500 Internal Server Error` - Server errors

### Cortex-Specific API Structure

#### Week Management
- `GET /api/weeks` - List all weeks (1-18)
- `POST /api/weeks` - Create new week
- `GET /api/weeks/{week_id}` - Get week details
- `PATCH /api/weeks/{week_id}` - Update week status

#### Data Import
- `POST /api/import/linestar` - Upload LineStar XLSX (multipart/form-data)
- `POST /api/import/draftkings` - Upload DraftKings XLSX (multipart/form-data)
- `POST /api/import/nfl-stats` - Upload NFL Stats XLSX (multipart/form-data)
- `GET /api/import/status/{week_id}` - Check import status and player count

#### Player Management
- `GET /api/players?week_id={week_id}` - List players for week (supports filtering by position, team)
- `GET /api/players/{player_key}` - Get player details
- `POST /api/players/map-alias` - Manually map player alias
- `GET /api/players/aliases` - List all player aliases

#### Smart Score
- `POST /api/smart-score/calculate` - Calculate Smart Scores for week
- `GET /api/smart-score/weights` - Get current weight configuration
- `PATCH /api/smart-score/weights` - Update weights (triggers recalculation)
- `GET /api/smart-score/profiles` - List saved weight profiles
- `POST /api/smart-score/profiles` - Save new weight profile
- `DELETE /api/smart-score/profiles/{profile_id}` - Delete profile

#### Lineup Optimization
- `POST /api/lineups/generate` - Generate optimized lineups
  - Request body: `{ week_id, num_lineups, strategy_mode, exposure_limits, stacking_rules }`
  - Response: Array of 10 lineup objects
- `GET /api/lineups?week_id={week_id}` - List generated lineups for week
- `GET /api/lineups/{lineup_id}` - Get lineup details

#### Export
- `GET /api/export/draftkings?week_id={week_id}` - Export lineups to DraftKings CSV
- `GET /api/export/database` - Export entire database (SQL dump)

### Request/Response Standards
- **Request Body**: Use JSON for POST/PATCH requests (except file uploads)
- **Response Format**: Always return JSON with consistent structure:
  ```json
  {
    "success": true,
    "data": { ... },
    "message": "153 players imported successfully"
  }
  ```
- **Error Format**: Return errors with clear messages:
  ```json
  {
    "success": false,
    "error": "Validation failed",
    "details": [
      { "field": "salary", "message": "Salary exceeds $50,000 cap" }
    ]
  }
  ```
- **File Uploads**: Use `multipart/form-data` for XLSX uploads
- **CSV Downloads**: Return `text/csv` with appropriate `Content-Disposition` header

### Performance Requirements
- **Lineup Generation**: Complete in <10 seconds
- **Smart Score Calculation**: Complete in <1 second for real-time updates
- **Data Import**: Provide progress feedback for large files (200+ players)
- **Query Optimization**: Use database indexes on `week_id`, `player_key`, `lineup_id`

### FastAPI-Specific Conventions
- **Pydantic Models**: Define request/response schemas using Pydantic for automatic validation
- **Async Endpoints**: Use `async def` for I/O-bound operations (database queries, file processing)
- **Dependency Injection**: Use FastAPI dependencies for database sessions, authentication (Phase 3)
- **OpenAPI Docs**: Leverage automatic Swagger UI at `/docs` for API exploration
- **Type Hints**: Use Python type hints for all function parameters and return values
