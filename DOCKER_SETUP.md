# LineupLab - Docker Setup Guide

## For Non-Technical Users

**Perfect for users who want to run LineupLab without installing Python, Node.js, or PostgreSQL!**

---

## Prerequisites

**You only need ONE thing installed:**

✅ **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)

That's it! Docker will handle everything else automatically.

---

## Quick Start (3 Steps)

### Step 1: Install Docker Desktop

1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Install it (just like any other app)
3. Open Docker Desktop and wait for it to start (green icon in system tray)

### Step 2: Get LineupLab

**Option A: Download from GitHub**
1. Go to: https://github.com/ray71478/LineupLab
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to a folder (e.g., `Desktop/LineupLab`)

**Option B: Clone with Git (if you have it)**
```bash
git clone https://github.com/ray71478/LineupLab.git
cd LineupLab
```

### Step 3: Start LineupLab

**On Mac/Linux:**
```bash
cd LineupLab
./start.sh
```

**On Windows:**
1. Open Command Prompt or PowerShell
2. Navigate to the LineupLab folder
3. Run: `start.sh` (or double-click `start.sh`)

**That's it!** 🎉

---

## Access Your Application

Once started, open your web browser and go to:

- **Main Application**: http://localhost
- **API Documentation**: http://localhost:8000/docs

---

## What Happens When You Start

The `start.sh` script automatically:

1. ✅ Checks if Docker is running
2. ✅ Starts the PostgreSQL database
3. ✅ Starts the FastAPI backend server
4. ✅ Starts the React frontend
5. ✅ Sets up all the connections between services

**First time startup takes 2-3 minutes** (Docker downloads images and builds everything)

**After that, it takes ~30 seconds** (just starts containers)

---

## Stopping LineupLab

**On Mac/Linux:**
```bash
./stop.sh
```

**On Windows:**
```bash
stop.sh
```

**Or manually:**
```bash
docker-compose stop
```

**Your data is safe!** It's stored in the `./data` directory and won't be deleted.

---

## Troubleshooting

### "Docker is not running"

**Solution:** Open Docker Desktop and wait for it to fully start (green icon).

### "Port 80 is already in use"

**Solution:** Another app is using port 80. You can change the port in `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "8080:80"  # Change 8080 to any port you want
```
Then access at: http://localhost:8080

### "Port 8000 is already in use"

**Solution:** Change the backend port in `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # Change 8001 to any port you want
```

### Services won't start

**Solution:** Check logs:
```bash
docker-compose logs
```

Or check individual service:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### "Permission denied" on start.sh

**Solution:** Make the script executable:
```bash
chmod +x start.sh stop.sh
```

---

## What Gets Installed?

**Nothing!** Docker runs everything in isolated containers:

- ✅ **No Python installation needed**
- ✅ **No Node.js installation needed**
- ✅ **No PostgreSQL installation needed**
- ✅ **No system configuration needed**

Everything runs inside Docker containers that are completely isolated from your computer.

---

## Your Data

**Where is my data stored?**
- Database: `./data/` folder (in the LineupLab directory)
- This persists even if you stop/restart LineupLab

**To backup your data:**
- Just copy the `./data` folder

**To delete everything (including data):**
```bash
docker-compose down -v
```

---

## Updating LineupLab

When new versions are available:

1. **Pull latest code:**
   ```bash
   git pull
   ```
   (Or download the new ZIP and replace files)

2. **Rebuild and restart:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

---

## Advanced Usage

### View logs
```bash
docker-compose logs -f
```

### Restart a service
```bash
docker-compose restart backend
```

### Check status
```bash
docker-compose ps
```

### Access database directly
```bash
docker-compose exec postgres psql -U lineuplab -d lineuplab
```

---

## System Requirements

- **Windows 10/11** (64-bit) or **macOS 10.15+** or **Linux**
- **4GB RAM minimum** (8GB recommended)
- **5GB free disk space**
- **Docker Desktop** installed and running

---

## Need Help?

If something doesn't work:

1. Check that Docker Desktop is running (green icon)
2. Check the logs: `docker-compose logs`
3. Try restarting: `./stop.sh` then `./start.sh`
4. Check the [Troubleshooting](#troubleshooting) section above

---

**That's it! You're ready to use LineupLab! 🚀**

