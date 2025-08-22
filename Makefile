# Linkly - Production Makefile
# Usage: make [target]

.PHONY: help install test lint format clean build deploy docs

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
APP_NAME := linkly
VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.0")

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

define HELP_TEXT
Available targets:

Development:
  install        Install development dependencies
  install-prod   Install production dependencies
  dev            Start development server
  dev-bg         Start development services in background

Testing:
  test           Run all tests
  test-unit      Run unit tests only
  test-integration Run integration tests only
  test-e2e       Run end-to-end tests
  test-coverage  Run tests with coverage report
  test-watch     Run tests in watch mode
  test-performance Run performance tests

Code Quality:
  lint           Run all linters (flake8, mypy, bandit)
  format         Format code (black, isort)
  format-check   Check code formatting
  security       Run security checks
  type-check     Run type checking

Database:
  db-upgrade     Run database migrations
  db-downgrade   Rollback last migration
  db-reset       Reset database (DESTRUCTIVE)
  db-seed        Seed database with test data

Docker:
  build          Build Docker images
  up             Start all services
  down           Stop all services
  logs           Show service logs
  clean-docker   Clean Docker resources

Production:
  deploy-staging Deploy to staging
  deploy-prod    Deploy to production
  backup         Create database backup
  restore        Restore database backup

Utilities:
  clean          Clean temporary files
  docs           Generate documentation
  check-deps     Check for outdated dependencies
  help           Show this help message
endef

help: ## Show this help message
	@echo "$(BLUE)Linkly Backend - Production Makefile$(NC)"
	@echo "$(YELLOW)Version: $(VERSION)$(NC)"
	@echo ""
	@echo "$$HELP_TEXT"

# Development

install: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app pip install -r requirements-dev.txt
	@echo "$(GREEN)Development dependencies installed in container!$(NC)"


install-prod: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app pip install -r requirements-prod.txt
	@echo "$(GREEN)Production dependencies installed in container!$(NC)"


dev: ## Start development server in Docker
	@echo "$(BLUE)Starting development server in Docker...$(NC)"
	$(DOCKER_COMPOSE) up --build app

dev-bg: ## Start development services in background
	@echo "$(BLUE)Starting development services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started in background!$(NC)"

# Testing


test: ## Run all tests in dedicated test container
	@echo "$(BLUE)Running all tests in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml build test
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test pytest



test-unit: ## Run unit tests only in dedicated test container
	@echo "$(BLUE)Running unit tests in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test pytest tests/unit/



test-integration: ## Run integration tests only in dedicated test container
	@echo "$(BLUE)Running integration tests in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test ./scripts/run-tests.sh integration



test-e2e: ## Run end-to-end tests in dedicated test container
	@echo "$(BLUE)Running E2E tests in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test ./scripts/run-tests.sh e2e



test-coverage: ## Run tests with coverage report in dedicated test container
	@echo "$(BLUE)Running tests with coverage in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test ./scripts/run-tests.sh coverage



test-watch: ## Run tests in watch mode in dedicated test container
	@echo "$(BLUE)Running tests in watch mode in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test ./scripts/run-tests.sh watch



test-performance: ## Run performance tests in dedicated test container
	@echo "$(BLUE)Running performance tests in dedicated test container...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.test.yaml run --rm test ./scripts/run-performance-tests.sh

# Code Quality

lint: ## Run all linters in Docker
	@echo "$(BLUE)Running linters in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app ./scripts/lint.sh


format: ## Format code in Docker
	@echo "$(BLUE)Formatting code in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app ./scripts/format.sh


format-check: ## Check code formatting in Docker
	@echo "$(BLUE)Checking code formatting in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app ./scripts/format.sh --check


security: ## Run security checks in Docker
	@echo "$(BLUE)Running security checks in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app ./scripts/security-check.sh


type-check: ## Run type checking in Docker
	@echo "$(BLUE)Running type checks in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app mypy app/ --config-file=mypy.ini

# Database

db-upgrade: ## Run database migrations in Docker
	@echo "$(BLUE)Running database migrations in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app ./scripts/db-migrate.sh upgrade


db-downgrade: ## Rollback last migration in Docker
	@echo "$(YELLOW)Rolling back last migration in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app ./scripts/db-migrate.sh downgrade


db-reset: ## Reset database (DESTRUCTIVE, in Docker)
	@echo "$(RED)Resetting database (DESTRUCTIVE, in Docker)...$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	$(DOCKER_COMPOSE) run --rm app ./scripts/db-migrate.sh reset


db-seed: ## Seed database with test data in Docker
	@echo "$(BLUE)Seeding database in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app python scripts/seed_db.py

# Docker
build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build

up: ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Services started!$(NC)"

down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down

logs: ## Show service logs
	@echo "$(BLUE)Showing service logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f

clean-docker: ## Clean Docker resources
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	docker system prune -f
	docker volume prune -f

# Production
deploy-staging: ## Deploy to staging
	@echo "$(BLUE)Deploying to staging...$(NC)"
	./scripts/deploy.sh staging

deploy-prod: ## Deploy to production
	@echo "$(RED)Deploying to production...$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	./scripts/deploy.sh production

backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	./scripts/backup.sh

restore: ## Restore database backup
	@echo "$(YELLOW)Restoring database backup...$(NC)"
	./scripts/backup.sh restore

# Utilities

clean: ## Clean temporary files in Docker
	@echo "$(BLUE)Cleaning temporary files in Docker...$(NC)"
	$(DOCKER_COMPOSE) run --rm app bash -c "find . -type f -name '*.pyc' -delete && find . -type d -name '__pycache__' -delete && find . -type d -name '*.egg-info' -exec rm -rf {} + && find . -type f -name '.coverage' -delete && find . -type d -name '.pytest_cache' -exec rm -rf {} + && find . -type d -name '.mypy_cache' -exec rm -rf {} +"
	@echo "$(GREEN)Cleanup complete!$(NC)"

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	./scripts/generate-docs.sh

check-deps: ## Check for outdated dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	$(PIP) list --outdated

# CI/CD Targets (used by GitHub Actions)
ci-test: install test-coverage lint security ## Run CI test suite
	@echo "$(GREEN)CI test suite completed!$(NC)"

ci-build: build ## Build for CI
	@echo "$(GREEN)CI build completed!$(NC)"

# Health checks
health-check: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	./scripts/health-check.sh

# Version management
version: ## Show current version
	@echo "$(BLUE)Current version: $(VERSION)$(NC)"

bump-patch: ## Bump patch version
	@echo "$(BLUE)Bumping patch version...$(NC)"
	./scripts/bump-version.sh patch

bump-minor: ## Bump minor version
	@echo "$(BLUE)Bumping minor version...$(NC)"
	./scripts/bump-version.sh minor

bump-major: ## Bump major version
	@echo "$(BLUE)Bumping major version...$(NC)"
	./scripts/bump-version.sh major
