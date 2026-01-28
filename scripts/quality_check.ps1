# Development Quality Check Scripts
# Run code quality tools on the codebase

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running Code Quality Checks" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$ErrorCount = 0

# 1. Black - Code Formatting
Write-Host "`n[1/5] Running Black (Code Formatter)..." -ForegroundColor Yellow
try {
    python -m black backend/ --check
    Write-Host "✓ Black: All files properly formatted" -ForegroundColor Green
}
catch {
    Write-Host "✗ Black: Formatting issues found. Run 'python -m black backend/' to fix" -ForegroundColor Red
    $ErrorCount++
}

# 2. isort - Import Sorting
Write-Host "`n[2/5] Running isort (Import Sorter)..." -ForegroundColor Yellow
try {
    python -m isort backend/ --check-only
    Write-Host "✓ isort: All imports properly sorted" -ForegroundColor Green
}
catch {
    Write-Host "✗ isort: Import sorting issues found. Run 'python -m isort backend/' to fix" -ForegroundColor Red
    $ErrorCount++
}

# 3. flake8 - Style Guide Enforcement
Write-Host "`n[3/5] Running flake8 (Style Checker)..." -ForegroundColor Yellow
try {
    python -m flake8 backend/ --max-line-length=100 --extend-ignore=E203, W503
    Write-Host "✓ flake8: No style issues found" -ForegroundColor Green
}
catch {
    Write-Host "✗ flake8: Style issues found" -ForegroundColor Red
    $ErrorCount++
}

# 4. mypy - Type Checking
Write-Host "`n[4/5] Running mypy (Type Checker)..." -ForegroundColor Yellow
try {
    python -m mypy backend/ --ignore-missing-imports
    Write-Host "✓ mypy: No type issues found" -ForegroundColor Green
}
catch {
    Write-Host "✗ mypy: Type issues found" -ForegroundColor Red
    $ErrorCount++
}

# 5. pylint - Code Analysis
Write-Host "`n[5/5] Running pylint (Code Analyzer)..." -ForegroundColor Yellow
try {
    python -m pylint backend/ --max-line-length=100 --score=yes
    Write-Host "✓ pylint: Code quality looks good" -ForegroundColor Green
}
catch {
    Write-Host "✗ pylint: Code quality issues found" -ForegroundColor Red
    $ErrorCount++
}

Write-Host "`n==========================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "Quality checks complete! All passed ✓" -ForegroundColor Green
}
else {
    Write-Host "Quality checks complete with $ErrorCount issues" -ForegroundColor Yellow
}
Write-Host "==========================================" -ForegroundColor Cyan

exit $ErrorCount
