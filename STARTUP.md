# LineupLab Startup Guide

## 1. Kill All Processes
```bash
killall -9 python node
# Free ports if still in use
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :5173 | xargs kill -9 2>/dev/null
```

## 2. Database Setup (First Time Only)
```bash
cd /Users/raybargas/Documents/Cortex
./init_db.sh --seed
```

## 3. Start Backend
```bash
cd /Users/raybargas/Documents/Cortex
source venv/bin/activate
python -m backend.main
```
Wait for: `INFO: Uvicorn running on http://0.0.0.0:8000`

## 4. Start Frontend (New Terminal)
```bash
cd /Users/raybargas/Documents/Cortex/frontend
npm run dev
```
Open: `http://localhost:5173`

---

## Quick Commands

| Task | Command |
|------|---------|
| Kill all | `killall -9 python node` |
| Reset DB | `cd /Users/raybargas/Documents/Cortex && ./init_db.sh --reset` |
| Reinit DB | `cd /Users/raybargas/Documents/Cortex && ./init_db.sh --seed` |
| Check port 8000 | `lsof -i :8000` |
| Check port 5173 | `lsof -i :5173` |
| Test backend | `curl http://localhost:8000/health` |
