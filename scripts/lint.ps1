# Quick lint check before commits

Write-Host "Running quick lint check..." -ForegroundColor Yellow

# Run flake8 only (fastest checker)
python -m flake8 backend/ --max-line-length=100 --extend-ignore=E203,W503

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lint check passed" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Lint check failed" -ForegroundColor Red
    exit 1
}
