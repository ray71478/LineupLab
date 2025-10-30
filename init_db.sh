#!/bin/bash

# ============================================
# Cortex Database Initialization Script
# ============================================
# This script automates database setup for local development:
# 1. Waits for PostgreSQL health check to pass
# 2. Runs Alembic migrations to create schema
# 3. Optionally seeds development data
#
# Usage:
#   ./init_db.sh              # Initialize database with migrations only
#   ./init_db.sh --seed       # Initialize database and seed development data
#   ./init_db.sh --reset      # Reset database (WARNING: deletes all data)

set -e  # Exit immediately if a command exits with a non-zero status

# ------------------------------------------
# Configuration
# ------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo "No .env file found. Using default DATABASE_URL from docker-compose.yml"
    export DATABASE_URL="postgresql://cortex:cortex@localhost:5432/cortex"
fi

# ------------------------------------------
# Color output for better readability
# ------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ------------------------------------------
# Helper Functions
# ------------------------------------------
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ------------------------------------------
# Check if Docker is running
# ------------------------------------------
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_success "Docker is running"
}

# ------------------------------------------
# Wait for PostgreSQL to be healthy
# ------------------------------------------
wait_for_postgres() {
    print_header "Waiting for PostgreSQL to be ready..."

    # Check if container exists
    if ! docker-compose ps | grep -q cortex-postgres; then
        print_warning "PostgreSQL container not found. Starting it now..."
        docker-compose up -d postgres
    fi

    MAX_ATTEMPTS=30
    ATTEMPT=0

    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        ATTEMPT=$((ATTEMPT + 1))

        # Check health status using docker-compose
        HEALTH_STATUS=$(docker-compose ps postgres | grep "healthy" || echo "")

        if [ -n "$HEALTH_STATUS" ]; then
            print_success "PostgreSQL is healthy and ready!"
            return 0
        fi

        echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: PostgreSQL not ready yet, waiting 2 seconds..."
        sleep 2
    done

    print_error "PostgreSQL failed to become healthy after $MAX_ATTEMPTS attempts"
    print_info "Check logs: docker-compose logs postgres"
    exit 1
}

# ------------------------------------------
# Run Alembic migrations
# ------------------------------------------
run_migrations() {
    print_header "Running Alembic migrations..."

    # Check if alembic is installed
    if ! command -v alembic &> /dev/null; then
        print_error "Alembic is not installed. Run: pip install -r requirements.txt"
        exit 1
    fi

    # Check current migration version
    print_info "Checking current migration version..."
    alembic current

    # Run migrations
    print_info "Upgrading to latest migration..."
    alembic upgrade head

    # Verify migrations completed
    print_info "Current migration version after upgrade:"
    alembic current

    print_success "Migrations completed successfully!"
}

# ------------------------------------------
# Seed development data (optional)
# ------------------------------------------
seed_development_data() {
    print_header "Seeding development data..."

    # Check if seed script exists
    SEED_SCRIPT="backend/scripts/seed_development_data.py"
    if [ ! -f "$SEED_SCRIPT" ]; then
        print_warning "Seed script not found at $SEED_SCRIPT"
        print_warning "Skipping seed data. Database will be empty except for NFL schedule."
        return 0
    fi

    print_info "Running seed script: $SEED_SCRIPT"
    python "$SEED_SCRIPT"

    print_success "Development data seeded successfully!"
}

# ------------------------------------------
# Reset database (WARNING: destructive)
# ------------------------------------------
reset_database() {
    print_header "RESETTING DATABASE"
    print_warning "This will DELETE ALL DATA in the database!"

    # Prompt for confirmation
    read -p "Are you sure? Type 'yes' to confirm: " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        print_info "Database reset cancelled."
        exit 0
    fi

    print_info "Stopping PostgreSQL container..."
    docker-compose down

    print_info "Deleting database volume (all data will be lost)..."
    docker-compose down -v

    print_info "Removing data directory..."
    if [ -d "./data" ]; then
        rm -rf ./data
    fi

    print_info "Starting fresh PostgreSQL container..."
    docker-compose up -d postgres

    print_success "Database reset complete!"
}

# ------------------------------------------
# Verify database setup
# ------------------------------------------
verify_database() {
    print_header "Verifying database setup..."

    # Connect to database and check tables
    print_info "Checking for tables in database..."

    TABLE_COUNT=$(docker-compose exec -T postgres psql -U cortex -d cortex -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)

    if [ "$TABLE_COUNT" -eq 0 ]; then
        print_warning "No tables found in database. Database is empty."
    else
        print_success "Found $TABLE_COUNT tables in database"

        # List tables
        print_info "Tables in database:"
        docker-compose exec -T postgres psql -U cortex -d cortex -c "\dt"
    fi

    # Check week data
    print_info "Checking weeks table..."
    WEEK_COUNT=$(docker-compose exec -T postgres psql -U cortex -d cortex -t -c "SELECT COUNT(*) FROM weeks;" 2>/dev/null | xargs || echo "0")

    if [ "$WEEK_COUNT" -gt 0 ]; then
        print_success "Found $WEEK_COUNT weeks in database"
    else
        print_warning "No weeks found in database. You may need to run: alembic upgrade head"
    fi

    print_success "Database verification complete!"
}

# ------------------------------------------
# Main execution
# ------------------------------------------
main() {
    print_header "Cortex Database Initialization"

    # Parse command line arguments
    RESET=false
    SEED=false

    for arg in "$@"; do
        case $arg in
            --reset)
                RESET=true
                ;;
            --seed)
                SEED=true
                ;;
            --help)
                echo "Usage: ./init_db.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --reset    Reset database (WARNING: deletes all data)"
                echo "  --seed     Seed development data after migrations"
                echo "  --help     Show this help message"
                echo ""
                echo "Examples:"
                echo "  ./init_db.sh              # Run migrations only"
                echo "  ./init_db.sh --seed       # Run migrations and seed data"
                echo "  ./init_db.sh --reset      # Reset database completely"
                exit 0
                ;;
        esac
    done

    # Execute based on flags
    check_docker

    if [ "$RESET" = true ]; then
        reset_database
    fi

    wait_for_postgres
    run_migrations

    if [ "$SEED" = true ]; then
        seed_development_data
    fi

    verify_database

    # Print connection info
    print_header "Database Ready!"
    print_info "Connection details:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: cortex"
    echo "  Username: cortex"
    echo "  Password: cortex"
    echo ""
    print_info "Connection string:"
    echo "  postgresql://cortex:cortex@localhost:5432/cortex"
    echo ""
    print_info "Connect via psql:"
    echo "  docker-compose exec postgres psql -U cortex -d cortex"
    echo ""
    print_info "Connect via pgAdmin or DBeaver:"
    echo "  See docs/database-setup.md for detailed instructions"
    echo ""
    print_success "Database initialization complete!"
}

# Run main function with all arguments
main "$@"
