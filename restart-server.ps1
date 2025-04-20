# restart-server.ps1
# Script to properly restart the FastAPI server using PowerShell

Write-Host "Stopping any running uvicorn processes..." -ForegroundColor Yellow
try {
    Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✓ Successfully stopped existing uvicorn processes" -ForegroundColor Green
} catch {
    Write-Host "No uvicorn processes were running" -ForegroundColor Gray
}

# Small delay to ensure ports are freed
Start-Sleep -Seconds 1

Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Note: The script will continue running until the server is stopped 