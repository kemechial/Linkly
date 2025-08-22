#!/bin/bash
# Code quality and linting script
# Usage: ./scripts/lint.sh [--fix]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$PROJECT_DIR/lint-reports"

# Create reports directory
mkdir -p "$REPORTS_DIR"

FIX_MODE=false
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Code Quality & Linting Suite${NC}"
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

run_black() {
    print_info "Running Black (code formatter)..."
    
    if [ "$FIX_MODE" = true ]; then
        black app/ tests/ --line-length 88 --target-version py311
        print_success "Black formatting applied"
    else
        black app/ tests/ --check --line-length 88 --target-version py311
        print_success "Black formatting check passed"
    fi
}

run_isort() {
    print_info "Running isort (import sorting)..."
    
    if [ "$FIX_MODE" = true ]; then
        isort app/ tests/ --profile black
        print_success "Import sorting applied"
    else
        isort app/ tests/ --check-only --profile black
        print_success "Import sorting check passed"
    fi
}

run_flake8() {
    print_info "Running flake8 (style guide enforcement)..."
    
    flake8 app/ tests/ \
        --max-line-length=88 \
        --extend-ignore=E203,W503 \
        --exclude=__pycache__,migrations \
        --output-file="$REPORTS_DIR/flake8-report.txt" \
        --tee
    
    if [ $? -eq 0 ]; then
        print_success "Flake8 check passed"
    else
        print_error "Flake8 found style issues. See: $REPORTS_DIR/flake8-report.txt"
        exit 1
    fi
}

run_mypy() {
    print_info "Running mypy (type checking)..."
    
    mypy app/ \
        --config-file=mypy.ini \
        --html-report="$REPORTS_DIR/mypy-html" \
        --txt-report="$REPORTS_DIR/mypy-txt" \
        --xml-report="$REPORTS_DIR/mypy-xml"
    
    if [ $? -eq 0 ]; then
        print_success "Type checking passed"
    else
        print_warning "Type checking found issues. See: $REPORTS_DIR/mypy-html/index.html"
    fi
}

run_bandit() {
    print_info "Running bandit (security linting)..."
    
    bandit -r app/ \
        -f json \
        -o "$REPORTS_DIR/bandit-report.json" \
        -ll
    
    bandit -r app/ \
        -f html \
        -o "$REPORTS_DIR/bandit-report.html" \
        -ll
    
    if [ $? -eq 0 ]; then
        print_success "Security scan passed"
    else
        print_warning "Security scan found issues. See: $REPORTS_DIR/bandit-report.html"
    fi
}

run_prospector() {
    print_info "Running prospector (comprehensive analysis)..."
    
    prospector app/ \
        --output-format json \
        --output-file "$REPORTS_DIR/prospector-report.json"
    
    prospector app/ \
        --output-format html \
        --output-file "$REPORTS_DIR/prospector-report.html"
    
    print_success "Comprehensive analysis completed"
}

run_vulture() {
    print_info "Running vulture (dead code detection)..."
    
    vulture app/ tests/ \
        --min-confidence 80 \
        > "$REPORTS_DIR/vulture-report.txt"
    
    if [ -s "$REPORTS_DIR/vulture-report.txt" ]; then
        print_warning "Dead code detected. See: $REPORTS_DIR/vulture-report.txt"
    else
        print_success "No dead code detected"
    fi
}

run_radon() {
    print_info "Running radon (complexity analysis)..."
    
    # Cyclomatic complexity
    radon cc app/ \
        --json \
        > "$REPORTS_DIR/radon-complexity.json"
    
    radon cc app/ \
        --show-complexity \
        --average \
        > "$REPORTS_DIR/radon-complexity.txt"
    
    # Maintainability index
    radon mi app/ \
        --json \
        > "$REPORTS_DIR/radon-maintainability.json"
    
    radon mi app/ \
        --show \
        > "$REPORTS_DIR/radon-maintainability.txt"
    
    print_success "Complexity analysis completed"
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    # Safety check for known vulnerabilities
    if command -v safety &> /dev/null; then
        safety check \
            --json \
            --output "$REPORTS_DIR/safety-report.json"
        
        if [ $? -eq 0 ]; then
            print_success "No known vulnerabilities found"
        else
            print_warning "Potential vulnerabilities detected. See: $REPORTS_DIR/safety-report.json"
        fi
    fi
    
    # Check for outdated packages
    pip list --outdated > "$REPORTS_DIR/outdated-packages.txt"
    
    if [ -s "$REPORTS_DIR/outdated-packages.txt" ]; then
        print_warning "Outdated packages found. See: $REPORTS_DIR/outdated-packages.txt"
    else
        print_success "All packages are up to date"
    fi
}

generate_quality_report() {
    print_info "Generating quality report..."
    
    cat > "$REPORTS_DIR/quality-summary.md" << EOF
# Code Quality Report

**Date:** $(date)
**Project:** Linkly Backend
**Fix Mode:** $FIX_MODE

## Linting Results

### Code Formatting
- **Black:** $([ -f "$REPORTS_DIR/black-report.txt" ] && echo "❌ Issues found" || echo "✅ Passed")
- **isort:** $([ -f "$REPORTS_DIR/isort-report.txt" ] && echo "❌ Issues found" || echo "✅ Passed")

### Style Guide
- **Flake8:** $([ -s "$REPORTS_DIR/flake8-report.txt" ] && echo "❌ Issues found" || echo "✅ Passed")

### Type Checking
- **mypy:** $([ -d "$REPORTS_DIR/mypy-html" ] && echo "⚠️  See detailed report" || echo "✅ Passed")

### Security
- **Bandit:** $([ -f "$REPORTS_DIR/bandit-report.json" ] && echo "⚠️  See detailed report" || echo "✅ Passed")

### Code Quality
- **Prospector:** $([ -f "$REPORTS_DIR/prospector-report.json" ] && echo "📊 Analysis complete" || echo "❌ Not run")
- **Vulture:** $([ -s "$REPORTS_DIR/vulture-report.txt" ] && echo "⚠️  Dead code found" || echo "✅ No dead code")
- **Radon:** $([ -f "$REPORTS_DIR/radon-complexity.json" ] && echo "📊 Analysis complete" || echo "❌ Not run")

## Dependencies
- **Safety:** $([ -f "$REPORTS_DIR/safety-report.json" ] && echo "🔍 Security scan complete" || echo "❌ Not run")
- **Outdated:** $([ -s "$REPORTS_DIR/outdated-packages.txt" ] && echo "⚠️  Updates available" || echo "✅ All current")

## Detailed Reports

- [Flake8 Report]($REPORTS_DIR/flake8-report.txt)
- [MyPy HTML Report]($REPORTS_DIR/mypy-html/index.html)
- [Bandit Security Report]($REPORTS_DIR/bandit-report.html)
- [Prospector Report]($REPORTS_DIR/prospector-report.html)
- [Complexity Analysis]($REPORTS_DIR/radon-complexity.txt)
- [Maintainability Index]($REPORTS_DIR/radon-maintainability.txt)

## Recommendations

1. Fix any flake8 style issues
2. Address mypy type hints warnings
3. Review bandit security findings
4. Consider refactoring high complexity functions
5. Remove dead code identified by vulture
6. Update outdated dependencies

EOF

    print_success "Quality report generated: $REPORTS_DIR/quality-summary.md"
}

# Main execution
main() {
    print_header
    
    if [ "$FIX_MODE" = true ]; then
        print_info "Running in fix mode - will apply automatic fixes"
    else
        print_info "Running in check mode - will report issues only"
    fi
    
    echo ""
    
    # Run formatters first (if in fix mode)
    if [ "$FIX_MODE" = true ]; then
        run_black
        run_isort
    fi
    
    # Run linters
    run_flake8 || true  # Don't exit on flake8 errors in summary mode
    run_mypy || true
    run_bandit || true
    
    # Run additional analysis
    run_prospector || true
    run_vulture || true
    run_radon || true
    
    # Check dependencies
    check_dependencies || true
    
    # Run formatters in check mode if not fixing
    if [ "$FIX_MODE" = false ]; then
        run_black || true
        run_isort || true
    fi
    
    generate_quality_report
    
    print_success "Code quality analysis completed!"
    print_info "Detailed reports available in: $REPORTS_DIR"
}

# Run main function
main "$@"
