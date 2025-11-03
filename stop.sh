#!/bin/bash

# ============================================
# LineupLab - Stop Script
# ============================================
# This script stops the LineupLab application.

set -e

echo "🛑 Stopping LineupLab..."
echo ""

# Use docker compose (newer) or docker-compose (older)
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

# Stop services
$COMPOSE_CMD stop

echo ""
echo "✅ LineupLab has been stopped"
echo ""
echo "💡 Your data is safe - it's stored in the ./data directory"
echo ""
echo "🚀 To start again, run: ./start.sh"
echo "🗑️  To remove everything (including data), run: docker-compose down -v"
echo ""

