# CodeCompanion Orchestra Makefile
# Simple task automation for development and testing

.PHONY: test test-verbose test-bus test-schema help install clean setup build uninstall run

# Default target
help:
	@echo "CodeCompanion Orchestra - Available Commands:"
	@echo ""
	@echo "  make test         - Run all smoke tests (quiet)"
	@echo "  make test-verbose - Run tests with verbose output"
	@echo "  make test-bus     - Run only bus system tests"
	@echo "  make test-schema  - Run only schema validation tests"
	@echo "  make install      - Install test dependencies"
	@echo "  make clean        - Clean up test artifacts"
	@echo ""
	@echo "Package commands:"
	@echo "  make setup        - Setup package build environment"
	@echo "  make build        - Build package"
	@echo "  make run          - Run codecompanion CLI"
	@echo ""

# Run all tests quietly
test:
	@echo "🧪 Running CodeCompanion Orchestra smoke tests..."
	python -m pytest tests/ -q --tb=short

# Run tests with verbose output
test-verbose:
	@echo "🧪 Running tests with verbose output..."
	python -m pytest tests/ -v --tb=long

# Run only bus tests
test-bus:
	@echo "🚌 Running bus system tests..."
	python -m pytest tests/test_bus.py -v

# Run only schema tests
test-schema:
	@echo "📋 Running schema validation tests..."
	python -m pytest tests/test_artifact_schema.py -v

# Install test dependencies (if needed)
install:
	@echo "📦 Installing test dependencies..."
	pip install pytest pytest-asyncio

# Clean up test artifacts
clean:
	@echo "🧹 Cleaning up test artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf dist build *.egg-info
	@echo "✅ Cleanup complete"

setup:
	python -m pip install -U pip wheel build
	pip install -e .

build:
	python -m build

uninstall:
	pip uninstall -y codecompanion || true

run:
	codecompanion --check

chat:
	codecompanion --chat

auto:
	codecompanion --auto

agent:
	@[ -n "$$AGENT" ] || (echo "Usage: make agent AGENT=Installer"; exit 1)
	codecompanion --run "$$AGENT"