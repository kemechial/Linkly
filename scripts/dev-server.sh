#!/bin/bash
# Development server startup script
# Usage: ./scripts/dev-server.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Linkly Development Server${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_dependencies() {
    print_info "Checking development dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Check if virtual environment is activated
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "No virtual environment detected. Consider using: python -m venv venv && source venv/bin/activate"
    fi
    
    # Check if requirements are installed
    if ! python3 -c "import fastapi" &> /dev/null; then
        print_warning "FastAPI not found. Installing dependencies..."
        pip install -r requirements-dev.txt
    fi
    
    print_success "Dependencies OK"
}

setup_environment() {
    print_info "Setting up development environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        print_info "Creating .env file from template..."
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        print_warning "Please update .env file with your configuration"
    fi
    
    # Set development environment variables
    export DEBUG=true
    export ENVIRONMENT=development
    export DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:postgres@localhost:5432/linkly_dev"}
    export REDIS_HOST=${REDIS_HOST:-"localhost"}
    export REDIS_PORT=${REDIS_PORT:-"6379"}
    
    print_success "Environment configured"
}

start_services() {
    print_info "Starting development services..."
    
    # Check if Docker is available
    if command -v docker-compose &> /dev/null; then
        # Start database and Redis if not running
        if ! docker ps | grep -q postgres; then
            print_info "Starting PostgreSQL..."
            docker-compose up -d db
        fi
        
        if ! docker ps | grep -q redis; then
            print_info "Starting Redis..."
            docker-compose up -d redis
        fi
        
        # Wait for services to be ready
        print_info "Waiting for services to be ready..."
        sleep 5
        
        print_success "Services started"
    else
        print_warning "Docker not available. Make sure PostgreSQL and Redis are running manually."
    fi
}

run_migrations() {
    print_info "Running database migrations..."
    
    # Check if Alembic is set up
    if [ -f "$PROJECT_DIR/alembic.ini" ]; then
        alembic upgrade head
        print_success "Migrations completed"
    else
        print_warning "Alembic not configured. Creating tables directly..."
        python3 -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(engine)"
        print_success "Tables created"
    fi
}

start_server() {
    print_info "Starting FastAPI development server..."
    echo ""
    print_info "Server will be available at: http://localhost:8000"
    print_info "API documentation: http://localhost:8000/docs"
    print_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Start uvicorn with development settings
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir app \
        --log-level debug \
        --access-log
}

show_urls() {
    echo ""
    echo -e "${GREEN}🚀 Development server is running!${NC}"
    echo ""
    echo -e "${BLUE}Available URLs:${NC}"
    echo "  📖 API Documentation: http://localhost:8000/docs"
    echo "  🔍 Alternative Docs:  http://localhost:8000/redoc"
    echo "  ⚡ Health Check:     http://localhost:8000/health"
    echo "  🔗 Test Link:        http://localhost:8000/test"
    echo ""
    echo -e "${YELLOW}Development Tools:${NC}"
    echo "  🐛 Debug Mode:       Enabled"
    echo "  🔄 Auto Reload:      Enabled"
    echo "  📝 Access Logs:      Enabled"
    echo ""
}

cleanup() {
    print_info "Shutting down development server..."
    # Any cleanup tasks here
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_header
    
    check_dependencies
    setup_environment
    start_services
    run_migrations
    
    show_urls
    start_server
}

# Run main function
main "$@"
