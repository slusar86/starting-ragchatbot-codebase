#!/bin/bash
# Auto-format the codebase with Black and isort

set -e

echo "=========================================="
echo "Auto-formatting Codebase"
echo "=========================================="

# Format with Black
echo -e "\n[1/2] Running Black formatter..."
python -m black backend/
echo "✓ Black formatting complete"

# Sort imports with isort
echo -e "\n[2/2] Running isort..."
python -m isort backend/
echo "✓ Import sorting complete"

echo -e "\n=========================================="
echo "Auto-formatting complete!"
echo "=========================================="
