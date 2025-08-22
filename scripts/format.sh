#!/bin/bash
# Code formatting script
# Usage: ./scripts/format.sh [--check]

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECK_MODE=false
if [[ "$1" == "--check" ]]; then
    CHECK_MODE=true
fi

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

format_with_black() {
    print_info "Formatting code with Black..."
    
    if [ "$CHECK_MODE" = true ]; then
        black app/ tests/ --check --line-length 88 --target-version py311
        print_success "Black formatting check passed"
    else
        black app/ tests/ --line-length 88 --target-version py311
        print_success "Code formatted with Black"
    fi
}

sort_imports() {
    print_info "Sorting imports with isort..."
    
    if [ "$CHECK_MODE" = true ]; then
        isort app/ tests/ --check-only --profile black
        print_success "Import sorting check passed"
    else
        isort app/ tests/ --profile black
        print_success "Imports sorted with isort"
    fi
}

main() {
    if [ "$CHECK_MODE" = true ]; then
        echo -e "${BLUE}🔍 Checking code formatting...${NC}"
    else
        echo -e "${BLUE}🎨 Formatting code...${NC}"
    fi
    
    format_with_black
    sort_imports
    
    if [ "$CHECK_MODE" = true ]; then
        print_success "All formatting checks passed!"
    else
        print_success "Code formatting completed!"
    fi
}

main "$@"
