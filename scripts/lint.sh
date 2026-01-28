#!/bin/bash
# Quick lint check before commits

echo "Running quick lint check..."

# Run flake8 only (fastest checker)
python -m flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503

if [ $? -eq 0 ]; then
    echo "✓ Lint check passed"
    exit 0
else
    echo "✗ Lint check failed"
    exit 1
fi
