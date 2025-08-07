#!/bin/bash

# Run tests for the Tizzl AI Stylist Retailer Integration

echo "Running Tizzl Retailer Integration Tests..."
echo "=========================================="

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run all tests
echo "Running all tests..."
pytest tests/ -v

# Run specific test suites with coverage
echo ""
echo "Running retailer integration tests with coverage..."
pytest tests/test_retailer_integration.py tests/test_retailer_endpoints.py -v --cov=tizzl.services.retailer_integration --cov=tizzl.api.retailer_endpoints --cov-report=term-missing

# Run only unit tests
echo ""
echo "Running unit tests..."
pytest tests/ -m unit -v

# Run only API tests
echo ""
echo "Running API endpoint tests..."
pytest tests/ -m api -v

echo ""
echo "Tests completed!"