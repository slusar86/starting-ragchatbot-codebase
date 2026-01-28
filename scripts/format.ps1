# Auto-format the codebase with Black and isort

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Auto-formatting Codebase" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Format with Black
Write-Host "`n[1/2] Running Black formatter..." -ForegroundColor Yellow
python -m black backend/
Write-Host "✓ Black formatting complete" -ForegroundColor Green

# Sort imports with isort
Write-Host "`n[2/2] Running isort..." -ForegroundColor Yellow
python -m isort backend/
Write-Host "✓ Import sorting complete" -ForegroundColor Green

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Auto-formatting complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
