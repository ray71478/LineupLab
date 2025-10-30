# Cortex Startup Guide

## Kill All Active Sessions

To stop all running processes:

```bash
killall -9 python node
```

This will kill both the backend (Python) and frontend (Node) processes.

## Fresh Startup Sequence

### Step 1: Initialize Database (First Time Only)

If you haven't initialized the database yet, or need to reset it:

```bash
cd /Users/raybargas/Documents/Cortex
./init_db.sh --seed
```

This will:
- Start PostgreSQL container if needed
- Run Alembic migrations to create tables
- Seed development data (NFL schedule, etc.)

**Note:** You only need to run this once, or if you want to reset the database completely. For subsequent startups, skip to Step 2.

### Step 2: Start the Backend

Open a terminal and run:

```bash
cd /Users/raybargas/Documents/Cortex
python -m backend.main
```

Wait for this message to appear:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Start the Frontend

Open a **new terminal** and run:

```bash
cd /Users/raybargas/Documents/Cortex/frontend
npm run dev
```

Wait for the dev server to start. It will show a URL like:
```
Local:   http://localhost:5173
```

### Step 4: Open in Browser

Open your browser and go to the URL shown in Step 3 (usually `http://localhost:5173`).

The app should now be fully loaded and functional!

## Quick Reference

| Action | Command |
|--------|---------|
| Kill all processes | `killall -9 python node` |
| Start backend | `cd /Users/raybargas/Documents/Cortex && python -m backend.main` |
| Start frontend | `cd /Users/raybargas/Documents/Cortex/frontend && npm run dev` |
| Reset database | `cd /Users/raybargas/Documents/Cortex && ./init_db.sh --reset` |
| Reinitialize database | `cd /Users/raybargas/Documents/Cortex && ./init_db.sh --seed` |

## Troubleshooting

### Backend won't start
- Check that port 8000 is free: `lsof -i :8000`
- Kill any processes on port 8000: `kill -9 <PID>`
- Make sure database is initialized: `./init_db.sh --seed`

### Frontend won't start
- Check that port 5173 is free: `lsof -i :5173`
- Kill any processes on that port: `kill -9 <PID>`
- Clear node_modules and reinstall: `npm install`

### App still spinning/not loading
- Check backend is responding: `curl http://localhost:8000/health`
- Check browser console for errors (DevTools)
- Make sure both backend and frontend are running in separate terminals

### Database issues
- Reset database: `./init_db.sh --reset` (WARNING: deletes all data)
- Verify database status: `./init_db.sh` (without flags, just runs migrations)
