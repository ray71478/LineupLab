#!/bin/bash

# ============================================
# LineupLab - Easy Startup Script
# ============================================
# This script starts the entire LineupLab application using Docker.
# Perfect for non-technical users - just run this one script!

set -e

echo "🚀 Starting LineupLab..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: docker-compose is not installed!"
    echo ""
    echo "Please install Docker Desktop which includes docker-compose."
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

echo "✅ Docker is running"
echo ""

# Start services
echo "📦 Starting database, backend, and frontend..."
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
if $COMPOSE_CMD ps | grep -q "lineuplab-postgres.*Up"; then
    echo "✅ Database is running"
else
    echo "⚠️  Database may still be starting..."
fi

if $COMPOSE_CMD ps | grep -q "lineuplab-backend.*Up"; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Backend may still be starting..."
fi

if $COMPOSE_CMD ps | grep -q "lineuplab-frontend.*Up"; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "🎉 LineupLab is starting up!"
echo ""
echo "📍 Access your application:"
echo "   Frontend: http://localhost"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Tip: It may take 30-60 seconds for everything to be fully ready."
echo "   You can check status with: docker-compose ps"
echo ""
echo "🛑 To stop LineupLab, run: ./stop.sh"
echo ""

