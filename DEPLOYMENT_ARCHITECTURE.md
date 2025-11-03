# LineupLab Deployment Architecture Guide

## Current Situation

**What We Have:**
- ✅ Frontend (React) - Ready for GitHub Pages
- ✅ Backend (FastAPI) - Runs locally on `localhost:8000`
- ✅ Database (PostgreSQL) - Runs locally via Docker

**The Problem:**
GitHub Pages only hosts **static files** (HTML, CSS, JavaScript). It cannot run:
- ❌ Python backend (FastAPI)
- ❌ PostgreSQL database
- ❌ Any server-side code

**Current Frontend API Calls:**
The frontend makes requests to `/api/...` which means:
- **Local dev**: `http://localhost:5173/api/...` → Vite proxy → `localhost:8000`
- **GitHub Pages**: `https://ray71478.github.io/LineupLab/api/...` → ❌ **404 Error** (no backend)

---

## Deployment Options

### Option 1: Full Stack Cloud Deployment (Recommended for Sharing)

Deploy everything to the cloud so anyone can access it:

**Architecture:**
```
Frontend (GitHub Pages) → Backend API (Railway/Render) → Database (Cloud PostgreSQL)
```

**Components:**
1. **Frontend**: GitHub Pages (already configured)
2. **Backend API**: Railway.app or Render.com (free tier available)
3. **Database**: Railway PostgreSQL or Render PostgreSQL (included)

**User Experience:**
- User visits: `https://ray71478.github.io/LineupLab/`
- Frontend loads from GitHub Pages
- API calls go to: `https://lineuplab-api.railway.app/api/...`
- Database lives in the cloud (Railway/Render)

**Cost:**
- Free tier on Railway/Render (limits apply)
- ~$5-20/month for production use

**Pros:**
- ✅ Anyone can use it (no local setup)
- ✅ Your data is centralized
- ✅ Automatic deployments
- ✅ No user configuration needed

**Cons:**
- ⚠️ Requires cloud deployment setup
- ⚠️ Database costs (if beyond free tier)
- ⚠️ API rate limits on free tier

---

### Option 2: Local Development Only (Current Setup)

Keep everything local - users must set up their own environment.

**Architecture:**
```
User's Machine:
├── Frontend (localhost:5173) → Backend (localhost:8000) → Database (localhost:5432)
```

**User Experience:**
1. User clones repository
2. User installs dependencies (Python, Node.js, Docker)
3. User runs database locally
4. User starts backend and frontend
5. User imports their own data

**Pros:**
- ✅ Free (no cloud costs)
- ✅ Full control over data
- ✅ Privacy (data stays local)
- ✅ No rate limits

**Cons:**
- ❌ Requires technical setup
- ❌ Each user has separate database
- ❌ No sharing of data
- ❌ Not accessible to non-technical users

---

### Option 3: Hybrid (Frontend on GitHub Pages, Backend Self-Hosted)

Frontend on GitHub Pages, but backend runs on your own server.

**Architecture:**
```
Frontend (GitHub Pages) → Backend (Your Server) → Database (Your Server)
```

**User Experience:**
- User visits GitHub Pages
- Frontend connects to your backend API
- Backend and database run on your server

**Pros:**
- ✅ Frontend accessible to anyone
- ✅ Centralized data
- ✅ Full control

**Cons:**
- ❌ Requires your own server (VPS costs ~$5-10/month)
- ❌ You maintain server uptime
- ❌ Security considerations

---

## Recommended: Option 1 (Full Stack Cloud)

For sharing with others, deploy everything to the cloud. Here's how:

### Step 1: Deploy Backend to Railway

1. **Create Railway account**: https://railway.app
2. **New Project** → Deploy from GitHub
3. **Select repository**: `ray71478/LineupLab`
4. **Configure:**
   - Root directory: `/backend`
   - Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Environment variables: Copy from `.env`

5. **Add PostgreSQL:**
   - Railway → New → PostgreSQL
   - Auto-generates `DATABASE_URL`

### Step 2: Update Frontend API URL

Create production environment variable:

**File: `frontend/.env.production`**
```bash
VITE_API_URL=https://your-backend.railway.app
```

**Update frontend code to use environment variable:**
```typescript
// frontend/src/config/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Then use: `${API_BASE_URL}/smart-score/calculate`
```

### Step 3: Deploy Frontend to GitHub Pages

The GitHub Actions workflow will automatically deploy when you push.

**Result:**
- Frontend: `https://ray71478.github.io/LineupLab/`
- Backend: `https://your-backend.railway.app`
- Database: Railway PostgreSQL (managed)

---

## What Users Experience

### Option 1 (Cloud Deployment):
1. User visits: `https://ray71478.github.io/LineupLab/`
2. ✅ App loads immediately
3. ✅ User imports data (stored in cloud database)
4. ✅ User generates lineups
5. ✅ Everything works, no setup needed

### Option 2 (Local Development):
1. User clones repo
2. User runs: `docker-compose up -d` (starts database)
3. User runs: `python -m backend.main` (starts backend)
4. User runs: `npm run dev` (starts frontend)
5. User visits: `http://localhost:5173`
6. ✅ App works, but only on their machine

---

## Quick Decision Guide

**Choose Option 1 if:**
- You want to share with non-technical users
- You want centralized data
- You're okay with cloud costs (~$5-20/month)

**Choose Option 2 if:**
- Users are technical
- You want complete privacy
- You want zero cloud costs
- Each user should have separate data

**Choose Option 3 if:**
- You have a VPS/server already
- You want to maintain your own infrastructure

---

## Next Steps

If you want **Option 1** (recommended for sharing):
1. I can help set up Railway deployment
2. Update frontend to use environment variables for API URL
3. Configure GitHub Pages to point to Railway backend

If you want **Option 2** (local only):
1. Document the setup process in README
2. Create `SETUP.md` with detailed instructions
3. Users clone and run locally

Which option do you prefer?

