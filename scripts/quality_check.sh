#!/bin/bash
# Development Quality Check Scripts
# Run code quality tools on the codebase

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Running Code Quality Checks"
echo "=========================================="

# 1. Black - Code Formatting
echo -e "\n${YELLOW}[1/5] Running Black (Code Formatter)...${NC}"
if python -m black backend/ --check; then
    echo -e "${GREEN}✓ Black: All files properly formatted${NC}"
else
    echo -e "${RED}✗ Black: Formatting issues found. Run 'python -m black backend/' to fix${NC}"
fi

# 2. isort - Import Sorting
echo -e "\n${YELLOW}[2/5] Running isort (Import Sorter)...${NC}"
if python -m isort backend/ --check-only; then
    echo -e "${GREEN}✓ isort: All imports properly sorted${NC}"
else
    echo -e "${RED}✗ isort: Import sorting issues found. Run 'python -m isort backend/' to fix${NC}"
fi

# 3. flake8 - Style Guide Enforcement
echo -e "\n${YELLOW}[3/5] Running flake8 (Style Checker)...${NC}"
if python -m flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503; then
    echo -e "${GREEN}✓ flake8: No style issues found${NC}"
else
    echo -e "${RED}✗ flake8: Style issues found${NC}"
fi

# 4. mypy - Type Checking
echo -e "\n${YELLOW}[4/5] Running mypy (Type Checker)...${NC}"
if python -m mypy backend/ --ignore-missing-imports; then
    echo -e "${GREEN}✓ mypy: No type issues found${NC}"
else
    echo -e "${RED}✗ mypy: Type issues found${NC}"
fi

# 5. pylint - Code Analysis
echo -e "\n${YELLOW}[5/5] Running pylint (Code Analyzer)...${NC}"
if python -m pylint backend/ --max-line-length=100 --score=yes; then
    echo -e "${GREEN}✓ pylint: Code quality looks good${NC}"
else
    echo -e "${RED}✗ pylint: Code quality issues found${NC}"
fi

echo -e "\n=========================================="
echo -e "${GREEN}Quality checks complete!${NC}"
echo "=========================================="
