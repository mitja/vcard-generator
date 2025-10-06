#!/bin/bash
# Integration test runner script
# This script runs Docker-based integration tests for the vCard generator

set -e  # Exit on error

echo "=================================="
echo "vCard Generator - Integration Tests"
echo "=================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ Error: pytest is not installed"
    echo "Install with: pip install pytest requests"
    exit 1
fi

echo "✅ pytest is available"
echo ""

# Run the integration tests
echo "Running integration tests..."
echo ""

pytest test_integration.py -v --tb=short

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ All integration tests passed!"
    echo "=================================="
else
    echo ""
    echo "=================================="
    echo "❌ Some integration tests failed"
    echo "=================================="
fi

exit $exit_code
