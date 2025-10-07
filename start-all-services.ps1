# Onebox Aggregator - Multi-Service Startup Script
# This script starts all required services in separate PowerShell windows

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 Starting Onebox Aggregator Services" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to your PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Python found: $($pythonCmd.Source)" -ForegroundColor Green
Write-Host ""

# Function to start a service in a new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$Port,
        [string]$Color
    )
    
    Write-Host "🔹 Starting $Title (Port $Port)..." -ForegroundColor $Color
    
    $scriptBlock = @"
`$Host.UI.RawUI.WindowTitle = '$Title - Port $Port'
cd '$projectDir'
Write-Host '============================================================' -ForegroundColor $Color
Write-Host '$Title' -ForegroundColor $Color
Write-Host 'Port: $Port' -ForegroundColor $Color
Write-Host '============================================================' -ForegroundColor $Color
Write-Host ''
$Command
Write-Host ''
Write-Host 'Press any key to close this window...' -ForegroundColor Yellow
`$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptBlock
    Start-Sleep -Seconds 2
}

# Start VectorDB Service (Port 8001)
Start-ServiceWindow -Title "VectorDB Service" -Command "python vectordb_service.py" -Port "8001" -Color "Cyan"

# Wait for VectorDB to initialize
Write-Host "⏳ Waiting for VectorDB to initialize (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start API Server (Port 3000)
Start-ServiceWindow -Title "API Server" -Command "python api_server.py" -Port "3000" -Color "Green"

# Wait for API Server to initialize
Write-Host "⏳ Waiting for API Server to initialize (3 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start Streamlit UI (Port 8501)
Start-ServiceWindow -Title "Streamlit UI" -Command "python -m streamlit run streamlit_app.py" -Port "8501" -Color "Magenta"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ All Services Started!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Yellow
Write-Host "   🌐 Streamlit UI:  http://localhost:8501" -ForegroundColor White
Write-Host "   🔌 API Server:    http://localhost:3000" -ForegroundColor White
Write-Host "   🔍 VectorDB API:  http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "📚 API Documentation:" -ForegroundColor Yellow
Write-Host "   http://localhost:3000/docs" -ForegroundColor White
Write-Host "   http://localhost:8001/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Each service is running in its own window." -ForegroundColor Cyan
Write-Host "    Close any window to stop that service." -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  To stop all services: Close all PowerShell windows." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
