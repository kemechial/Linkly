#!/bin/bash
# Production-grade test runner script
# Usage: ./scripts/run-tests.sh [test_type] [options]

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="${PROJECT_DIR}/tests"
COVERAGE_DIR="${PROJECT_DIR}/coverage"
REPORTS_DIR="${PROJECT_DIR}/test-reports"

# Ensure directories exist
mkdir -p "$COVERAGE_DIR" "$REPORTS_DIR"

# Default settings
PYTEST_ARGS=""
COVERAGE_THRESHOLD=80
PARALLEL_WORKERS=auto

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Linkly Test Suite Runner${NC}"
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
    print_info "Checking test dependencies..."
    
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found. Run 'make install' first."
        exit 1
    fi
    
    print_success "Dependencies OK"
}

setup_environment() {
    print_info "Setting up test environment..."
    
    # Set test environment variables if they are not already set
    export TEST_MODE=${TEST_MODE:-true}
    export DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:postgres@db:5432/linkly_test"}
    export REDIS_HOST=${REDIS_HOST:-"redis"}
    export REDIS_PORT=${REDIS_PORT:-"6379"}
    export SECRET_KEY=${SECRET_KEY:-"test-secret-key"}
    
    # Assume all test services are already running in container
    
    print_success "Environment ready"
}

run_unit_tests() {
    print_info "Running unit tests..."

    # Run pytest without redundant args, relying on pytest.ini for most settings
    pytest \
        tests/unit/ \
        $PYTEST_ARGS

    print_success "Unit tests completed"
}

run_integration_tests() {
    print_info "Running integration tests..."

    # Run pytest without redundant args
    pytest \
        tests/integration/ \
        $PYTEST_ARGS

    print_success "Integration tests completed"
}

run_e2e_tests() {
    print_info "Running end-to-end tests..."

    # Run pytest without redundant args
    pytest \
        tests/e2e/ \
        $PYTEST_ARGS

    print_success "E2E tests completed"
}

run_coverage_tests() {
    print_info "Running tests with coverage analysis..."

    # Only pass custom coverage threshold, other settings come from pytest.ini
    pytest \
        tests/ \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        $PYTEST_ARGS

    print_success "Coverage tests completed"
    print_info "Coverage report available at: $COVERAGE_DIR/html/index.html"
}

run_parallel_tests() {
    print_info "Running tests in parallel..."

    # Only override number of workers if specified, other settings from pytest.ini
    if [ "$PARALLEL_WORKERS" != "auto" ]; then
        pytest tests/ -n $PARALLEL_WORKERS $PYTEST_ARGS
    else
        pytest tests/ $PYTEST_ARGS
    fi

    print_success "Parallel tests completed"
}

run_watch_tests() {
    print_info "Running tests in watch mode..."
    print_warning "Press Ctrl+C to stop watching"
    
    pip install pytest-watch
    ptw \
        tests/ \
        --runner "pytest tests/ $PYTEST_ARGS"
}

run_all_tests() {
    print_info "Running complete test suite..."
    
    # Run tests in sequence for comprehensive coverage
    run_unit_tests
    run_integration_tests
    run_e2e_tests
    
    print_success "All tests completed successfully!"
}

generate_test_report() {
    print_info "Generating consolidated test report..."
    
    cat > "$REPORTS_DIR/test-summary.md" << EOF
# Test Execution Summary

**Date:** $(date)
**Project:** Linkly Backend
**Version:** $(cat VERSION 2>/dev/null || echo "unknown")

## Test Results

- **Unit Tests:** $([ -f "$REPORTS_DIR/unit-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Integration Tests:** $([ -f "$REPORTS_DIR/integration-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")
- **E2E Tests:** $([ -f "$REPORTS_DIR/e2e-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")

## Coverage

$(if [ -f "$COVERAGE_DIR/coverage.json" ]; then
    python3 -c "
import json
with open('$COVERAGE_DIR/coverage.json') as f:
    data = json.load(f)
    print(f\"**Overall Coverage:** {data['totals']['percent_covered']:.1f}%\")
"
else
    echo "**Coverage:** Not available"
fi)

## Reports

- [Unit Test Report]($REPORTS_DIR/unit-tests.html)
- [Integration Test Report]($REPORTS_DIR/integration-tests.html)
- [E2E Test Report]($REPORTS_DIR/e2e-tests.html)
- [Coverage Report]($COVERAGE_DIR/html/index.html)
EOF

    print_success "Test report generated: $REPORTS_DIR/test-summary.md"
}

cleanup() {
    print_info "Cleaning up test environment..."
    

    # No orchestration in container; cleanup only local artifacts
    
    print_success "Cleanup completed"
}

show_usage() {
    cat << EOF
Usage: $0 [test_type] [options]

Test Types:
  all           Run all tests (unit, integration, e2e)
  unit          Run unit tests only
  integration   Run integration tests only
  e2e           Run end-to-end tests
  coverage      Run tests with coverage analysis
  parallel      Run tests in parallel
  watch         Run tests in watch mode

Options:
  --verbose     Verbose output
  --debug       Debug mode
  --fast        Skip slow tests
  --workers N   Number of parallel workers (default: auto)
  --threshold N Coverage threshold (default: 80)
  --help        Show this help

Examples:
  $0 all                    # Run all tests
  $0 unit --verbose         # Run unit tests with verbose output
  $0 coverage --threshold 90 # Run with 90% coverage requirement
  $0 parallel --workers 4   # Run with 4 parallel workers
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            PYTEST_ARGS="$PYTEST_ARGS -v"
            shift
            ;;
        --debug)
            PYTEST_ARGS="$PYTEST_ARGS -s --pdb"
            shift
            ;;
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
            shift
            ;;
        --workers)
            PARALLEL_WORKERS="$2"
            shift 2
            ;;
        --threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        all|unit|integration|e2e|coverage|parallel|watch)
            TEST_TYPE="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    check_dependencies
    setup_environment
    
    case "${TEST_TYPE:-all}" in
        all)
            run_all_tests
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        coverage)
            run_coverage_tests
            ;;
        parallel)
            run_parallel_tests
            ;;
        watch)
            run_watch_tests
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            show_usage
            exit 1
            ;;
    esac
    
    generate_test_report
    print_success "Test execution completed successfully!"
}

# Run main function
main "$@"
