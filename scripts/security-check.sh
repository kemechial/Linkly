#!/bin/bash
# Security check script for Linkly project

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Security Check - Linkly${NC}"
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
    print_info "Checking security tools..."
    
    if ! command -v bandit &> /dev/null; then
        print_error "bandit not found. Installing..."
        pip install bandit
    fi
    
    if ! command -v safety &> /dev/null; then
        print_error "safety not found. Installing..."
        pip install safety
    fi
    
    print_success "Security tools ready"
}

run_bandit_scan() {
    print_info "Running Bandit security scan..."
    
    bandit -r app/ -f json -o security-report.json || true
    bandit -r app/ -ll
    
    print_success "Bandit scan completed"
}

run_safety_check() {
    print_info "Checking for known security vulnerabilities in dependencies..."
    
    safety check --json --output safety-report.json || true
    safety check
    
    print_success "Safety check completed"
}

check_secrets() {
    print_info "Checking for hardcoded secrets..."
    
    # Check for common secret patterns
    if grep -r "password.*=" app/ --include="*.py" | grep -v "hashed_password" | grep -v "get_password_hash"; then
        print_warning "Found potential hardcoded passwords"
    fi
    
    if grep -r "secret.*=" app/ --include="*.py" | grep -v "settings.secret_key"; then
        print_warning "Found potential hardcoded secrets"
    fi
    
    if grep -r "api_key.*=" app/ --include="*.py"; then
        print_warning "Found potential hardcoded API keys"
    fi
    
    print_success "Secret scan completed"
}

check_environment_config() {
    print_info "Checking environment configuration security..."
    
    if [ -f ".env" ]; then
        if grep -q "your-super-secret-key-change-this-in-production" .env; then
            print_error "Default SECRET_KEY found in .env file!"
        fi
        
        if grep -q "DEBUG=true" .env; then
            print_warning "Debug mode enabled - ensure this is disabled in production"
        fi
    fi
    
    print_success "Environment config check completed"
}

generate_security_report() {
    print_info "Generating security report..."
    
    cat > security-summary.md << EOF
# Security Scan Summary

**Date:** $(date)
**Project:** Linkly Backend

## Bandit Results
$(if [ -f "security-report.json" ]; then
    echo "- Security report generated: security-report.json"
else
    echo "- No security issues found by Bandit"
fi)

## Safety Results
$(if [ -f "safety-report.json" ]; then
    echo "- Vulnerability report generated: safety-report.json"
else
    echo "- No known vulnerabilities found in dependencies"
fi)

## Recommendations
- Ensure SECRET_KEY is changed in production
- Keep dependencies updated
- Review any warnings above
- Use HTTPS in production
- Implement rate limiting
- Enable proper logging and monitoring
EOF

    print_success "Security report generated: security-summary.md"
}

main() {
    print_header
    
    check_dependencies
    run_bandit_scan
    run_safety_check
    check_secrets
    check_environment_config
    generate_security_report
    
    print_success "Security check completed!"
}

main "$@"