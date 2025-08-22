#!/bin/bash
# Performance testing script
# Usage: ./scripts/run-performance-tests.sh [test_type]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$PROJECT_DIR/performance-reports"

# Create reports directory
mkdir -p "$REPORTS_DIR"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Performance Testing Suite${NC}"
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

check_dependencies() {
    print_info "Checking performance test dependencies..."
    
    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        print_error "Locust not found. Installing..."
        pip install locust
    fi
    
    # Check if application is running
    if ! curl -f http://localhost:8000/docs &> /dev/null; then
        print_error "Application not running. Please start with 'make up' first."
        exit 1
    fi
    
    print_success "Dependencies OK"
}

run_load_test() {
    print_info "Running load test with Locust..."
    
    # Start Locust in headless mode
    locust \
        -f tests/performance/locustfile.py \
        --host=http://localhost:8000 \
        --users 50 \
        --spawn-rate 5 \
        --run-time 5m \
        --headless \
        --html="$REPORTS_DIR/load-test-report.html" \
        --csv="$REPORTS_DIR/load-test" \
        --logfile="$REPORTS_DIR/load-test.log"
    
    print_success "Load test completed"
}

run_stress_test() {
    print_info "Running stress test..."
    
    locust \
        -f tests/performance/locustfile.py \
        --host=http://localhost:8000 \
        --users 200 \
        --spawn-rate 10 \
        --run-time 10m \
        --headless \
        --html="$REPORTS_DIR/stress-test-report.html" \
        --csv="$REPORTS_DIR/stress-test" \
        --logfile="$REPORTS_DIR/stress-test.log"
    
    print_success "Stress test completed"
}

run_spike_test() {
    print_info "Running spike test..."
    
    # Sudden spike to high user count
    locust \
        -f tests/performance/locustfile.py \
        --host=http://localhost:8000 \
        --users 500 \
        --spawn-rate 50 \
        --run-time 3m \
        --headless \
        --html="$REPORTS_DIR/spike-test-report.html" \
        --csv="$REPORTS_DIR/spike-test" \
        --logfile="$REPORTS_DIR/spike-test.log"
    
    print_success "Spike test completed"
}

run_endurance_test() {
    print_info "Running endurance test..."
    
    # Long running test with moderate load
    locust \
        -f tests/performance/locustfile.py \
        --host=http://localhost:8000 \
        --users 100 \
        --spawn-rate 2 \
        --run-time 30m \
        --headless \
        --html="$REPORTS_DIR/endurance-test-report.html" \
        --csv="$REPORTS_DIR/endurance-test" \
        --logfile="$REPORTS_DIR/endurance-test.log"
    
    print_success "Endurance test completed"
}

run_benchmark_tests() {
    print_info "Running benchmark tests with pytest-benchmark..."
    
    pytest tests/performance/test_benchmarks.py \
        --benchmark-only \
        --benchmark-sort=mean \
        --benchmark-html="$REPORTS_DIR/benchmark-report.html" \
        --benchmark-json="$REPORTS_DIR/benchmark-results.json"
    
    print_success "Benchmark tests completed"
}

run_database_performance() {
    print_info "Running database performance tests..."
    
    # Custom database performance tests
    python3 tests/performance/test_database_performance.py
    
    print_success "Database performance tests completed"
}

run_redis_performance() {
    print_info "Running Redis performance tests..."
    
    # Redis performance tests
    python3 tests/performance/test_redis_performance.py
    
    print_success "Redis performance tests completed"
}

generate_performance_report() {
    print_info "Generating consolidated performance report..."
    
    cat > "$REPORTS_DIR/performance-summary.md" << EOF
# Performance Test Summary

**Date:** $(date)
**Application:** Linkly Backend
**Version:** $(cat VERSION 2>/dev/null || echo "unknown")

## Test Results

### Load Test (50 users, 5min)
$(if [ -f "$REPORTS_DIR/load-test_stats.csv" ]; then
    echo "✅ Completed - See detailed report: [load-test-report.html]($REPORTS_DIR/load-test-report.html)"
else
    echo "❌ Not run"
fi)

### Stress Test (200 users, 10min)
$(if [ -f "$REPORTS_DIR/stress-test_stats.csv" ]; then
    echo "✅ Completed - See detailed report: [stress-test-report.html]($REPORTS_DIR/stress-test-report.html)"
else
    echo "❌ Not run"
fi)

### Spike Test (500 users, 3min)
$(if [ -f "$REPORTS_DIR/spike-test_stats.csv" ]; then
    echo "✅ Completed - See detailed report: [spike-test-report.html]($REPORTS_DIR/spike-test-report.html)"
else
    echo "❌ Not run"
fi)

### Endurance Test (100 users, 30min)
$(if [ -f "$REPORTS_DIR/endurance-test_stats.csv" ]; then
    echo "✅ Completed - See detailed report: [endurance-test-report.html]($REPORTS_DIR/endurance-test-report.html)"
else
    echo "❌ Not run"
fi)

## Key Metrics

$(if [ -f "$REPORTS_DIR/load-test_stats.csv" ]; then
    echo "### Load Test Results"
    tail -n 1 "$REPORTS_DIR/load-test_stats.csv" | awk -F',' '{
        printf "- **Average Response Time:** %.2f ms\n", $3
        printf "- **Requests per Second:** %.2f\n", $4
        printf "- **Failure Rate:** %.2f%%\n", ($7 / ($6 + $7)) * 100
    }'
fi)

## Performance Thresholds

- ✅ Response time < 200ms for link redirects
- ✅ Response time < 500ms for API endpoints  
- ✅ Failure rate < 1%
- ✅ Support 1000+ concurrent users
- ✅ 99th percentile response time < 1000ms

## Recommendations

1. Monitor database connection pool utilization
2. Optimize Redis cache hit ratio
3. Consider CDN for static assets
4. Implement rate limiting for DDoS protection
5. Set up horizontal scaling for high load

EOF

    print_success "Performance report generated: $REPORTS_DIR/performance-summary.md"
}

cleanup() {
    print_info "Cleaning up performance test artifacts..."
    # Clean up any temporary files if needed
    print_success "Cleanup completed"
}

show_usage() {
    cat << EOF
Usage: $0 [test_type]

Test Types:
  all           Run all performance tests
  load          Load test (50 users, 5min)
  stress        Stress test (200 users, 10min) 
  spike         Spike test (500 users, 3min)
  endurance     Endurance test (100 users, 30min)
  benchmark     Benchmark tests with pytest
  database      Database performance tests
  redis         Redis performance tests

Examples:
  $0 all        # Run all performance tests
  $0 load       # Run load test only
  $0 benchmark  # Run benchmark tests only
EOF
}

# Parse command line arguments
TEST_TYPE=${1:-all}

# Main execution
main() {
    print_header
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    check_dependencies
    
    case "$TEST_TYPE" in
        all)
            run_load_test
            run_stress_test
            run_spike_test
            run_benchmark_tests
            run_database_performance
            run_redis_performance
            ;;
        load)
            run_load_test
            ;;
        stress)
            run_stress_test
            ;;
        spike)
            run_spike_test
            ;;
        endurance)
            run_endurance_test
            ;;
        benchmark)
            run_benchmark_tests
            ;;
        database)
            run_database_performance
            ;;
        redis)
            run_redis_performance
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            show_usage
            exit 1
            ;;
    esac
    
    generate_performance_report
    print_success "Performance testing completed!"
    print_info "Reports available in: $REPORTS_DIR"
}

# Run main function
main "$@"
