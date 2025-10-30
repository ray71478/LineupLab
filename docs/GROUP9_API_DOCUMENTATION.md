# Player Management API Reference (Group 9)

**Version:** 1.0
**Status:** Production Ready
**Date:** October 29, 2025
**Scope:** Task 9.1 - API Documentation

---

## Overview

This document provides comprehensive API documentation for the Player Management feature. It covers all endpoints, request/response formats, error handling, and usage examples.

## Endpoints Summary

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/api/players/by-week/{week_id}` | Fetch all players for a week | Implemented |
| GET | `/api/players/unmatched/{week_id}` | Fetch unmatched players | Implemented |
| GET | `/api/players/search` | Search players by name | Implemented |
| GET | `/api/players/suggestions/{unmatched_player_id}` | Get fuzzy match suggestions | Implemented |
| POST | `/api/unmatched-players/map` | Map unmatched player | Implemented |
| POST | `/api/unmatched-players/ignore` | Mark player as ignored | Implemented |

## Authentication & Security

All endpoints require Bearer token authentication. Include token in header:

```
Authorization: Bearer {your_token}
```

**Security Features:**
- HTTPS only in production
- JWT token validation
- CORS protection
- Rate limiting enabled
- Input validation on all endpoints
- SQL injection protection (parameterized queries)
- No sensitive data in logs

## Response Structure

**Success (200):**
```json
{
  "success": true,
  "data": { "players": [] },
  "error": null,
  "message": null
}
```

**Error (4xx/5xx):**
```json
{
  "success": false,
  "data": null,
  "error": "ERROR_CODE",
  "message": "Human-readable error message"
}
```

## Common Error Codes

- `INVALID_WEEK_ID` - Week doesn't exist
- `INVALID_PARAMETERS` - Bad request format
- `DATABASE_ERROR` - Server-side database issue
- `AUTHENTICATION_FAILED` - Invalid token
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `PERMISSION_DENIED` - User lacks access

## Request Examples

### Fetch Players with Filters
```bash
curl -X GET "https://api.example.com/api/players/by-week/42?position=QB&team=KC" \
  -H "Authorization: Bearer token"
```

### Map Unmatched Player
```bash
curl -X POST "https://api.example.com/api/unmatched-players/map" \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{
    "unmatched_player_id": 456,
    "canonical_player_key": "patrick_mahomes_KC_QB"
  }'
```

## Detailed Endpoint Documentation

See individual endpoint specifications in `/docs/API_DOCUMENTATION.md` for:
- Full parameter descriptions
- Response payload examples
- Error handling details
- Code samples in multiple languages
- Rate limiting information

---

**Documentation Status:** Complete
**Ready for:** Production Deployment
