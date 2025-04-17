# PowerShell script to run the Tavren backend
# Sets PYTHONPATH to include the project root for proper module resolution

# Set PYTHONPATH to current directory
$env:PYTHONPATH = $PWD

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
}

# Run the application with Uvicorn
python -m uvicorn app.main:app --reload --workers 1

# Keep console open if there's an error
if ($LASTEXITCODE -ne 0) {
    Write-Host "Application exited with code $LASTEXITCODE"
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} 