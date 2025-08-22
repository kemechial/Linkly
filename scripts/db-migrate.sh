#!/bin/bash
# Database migration script for Linkly project

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Database Migration - Linkly${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_dependencies() {
    print_info "Checking migration dependencies..."
    
    if ! command -v alembic &> /dev/null; then
        print_error "alembic not found. Installing..."
        pip install alembic
    fi
    
    print_success "Migration tools ready"
}

wait_for_database() {
    print_info "Waiting for database to be ready..."
    
    # Extract database connection details from DATABASE_URL
    DB_HOST=${DATABASE_URL#*@}
    DB_HOST=${DB_HOST%/*}
    DB_HOST=${DB_HOST%:*}
    
    DB_USER=${DATABASE_URL#*://}
    DB_USER=${DB_USER%:*}
    
    # Wait for PostgreSQL to be ready
    until pg_isready -h "${DB_HOST:-db}" -U "${DB_USER:-postgres}" -q; do
        print_info "Database is unavailable - sleeping"
        sleep 2
    done
    
    print_success "Database is ready"
}

init_alembic() {
    print_info "Initializing Alembic (if not already done)..."
    
    if [ ! -f "alembic.ini" ]; then
        alembic init migrations
        print_success "Alembic initialized"
    else
        print_info "Alembic already initialized"
    fi
}

create_migration() {
    local message="$1"
    if [ -z "$message" ]; then
        message="Auto-generated migration"
    fi
    
    print_info "Creating new migration: $message"
    alembic revision --autogenerate -m "$message"
    print_success "Migration created"
}

upgrade_database() {
    print_info "Upgrading database to latest version..."
    alembic upgrade head
    print_success "Database upgraded"
}

downgrade_database() {
    local target="${1:--1}"
    print_warning "Downgrading database to: $target"
    alembic downgrade "$target"
    print_success "Database downgraded"
}

show_current_revision() {
    print_info "Current database revision:"
    alembic current
}

show_migration_history() {
    print_info "Migration history:"
    alembic history --verbose
}

reset_database() {
    print_error "DESTRUCTIVE OPERATION: Resetting database"
    print_warning "This will drop all tables and recreate them"
    
    # Drop all tables
    python -c "
from app.database import engine, Base
from app.models import *
print('Dropping all tables...')
Base.metadata.drop_all(bind=engine)
print('Creating all tables...')
Base.metadata.create_all(bind=engine)
print('Database reset complete!')
"
    
    # Reset alembic version table
    alembic stamp head
    
    print_success "Database reset completed"
}

show_usage() {
    cat << EOF
Usage: $0 [command] [options]

Commands:
  init              Initialize Alembic migrations
  create [message]  Create a new migration
  upgrade           Upgrade to latest version
  downgrade [rev]   Downgrade to revision (default: -1)
  current           Show current revision
  history           Show migration history
  reset             Reset database (DESTRUCTIVE)
  
Examples:
  $0 init
  $0 create "Add user table"
  $0 upgrade
  $0 downgrade -1
  $0 current
  $0 history
  $0 reset
EOF
}

main() {
    print_header
    
    local command="$1"
    shift || true
    
    case "$command" in
        init)
            check_dependencies
            wait_for_database
            init_alembic
            ;;
        create)
            check_dependencies
            wait_for_database
            create_migration "$1"
            ;;
        upgrade)
            check_dependencies
            wait_for_database
            upgrade_database
            ;;
        downgrade)
            check_dependencies
            wait_for_database
            downgrade_database "$1"
            ;;
        current)
            check_dependencies
            wait_for_database
            show_current_revision
            ;;
        history)
            check_dependencies
            wait_for_database
            show_migration_history
            ;;
        reset)
            check_dependencies
            wait_for_database
            reset_database
            ;;
        *)
            echo "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
    
    print_success "Migration operation completed!"
}

main "$@"