# =====================================================================
# Onebox Aggregator - Service Startup Script
# =====================================================================
# This PowerShell script starts all services in the correct order:
# 1. VectorDB Service (port 8001)
# 2. API Server (port 3000) 
# 3. API Gateway (port 3001)
# 4. Node.js Service (port 3000 - if needed separately)
# =====================================================================

param(
    [switch]$SkipDependencyCheck,
    [switch]$StartGatewayOnly,
    [switch]$Verbose
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green" 
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-ServiceHealth {
    param([string]$Url, [string]$ServiceName, [int]$MaxRetries = 30)
    
    Write-ColorOutput "🔍 Checking $ServiceName health at $Url..." $InfoColor
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "$Url/health" -Method Get -TimeoutSec 5
            if ($response) {
                Write-ColorOutput "✅ $ServiceName is healthy!" $SuccessColor
                return $true
            }
        }
        catch {
            if ($Verbose) {
                Write-ColorOutput "   Attempt $i/$MaxRetries failed: $($_.Exception.Message)" $WarningColor
            }
        }
        
        if ($i -lt $MaxRetries) {
            Start-Sleep -Seconds 2
        }
    }
    
    Write-ColorOutput "❌ $ServiceName health check failed after $MaxRetries attempts" $ErrorColor
    return $false
}

function Start-ServiceInBackground {
    param([string]$Command, [string]$ServiceName, [string]$LogFile)
    
    Write-ColorOutput "🚀 Starting $ServiceName..." $InfoColor
    Write-ColorOutput "   Command: $Command" $InfoColor
    Write-ColorOutput "   Logs: $LogFile" $InfoColor
    
    # Start the service in a new PowerShell window
    $processArgs = @{
        FilePath     = "powershell.exe"
        ArgumentList = @("-Command", "& {$Command} *> '$LogFile'")
        WindowStyle  = "Minimized"
        PassThru     = $true
    }
    
    $process = Start-Process @processArgs
    
    if ($process) {
        Write-ColorOutput "✅ $ServiceName started (PID: $($process.Id))" $SuccessColor
        return $process
    }
    else {
        Write-ColorOutput "❌ Failed to start $ServiceName" $ErrorColor
        return $null
    }
}

function Test-PythonEnvironment {
    Write-ColorOutput "🐍 Checking Python environment..." $InfoColor
    
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "   Python: $pythonVersion" $SuccessColor
        
        # Check required packages
        $requiredPackages = @("fastapi", "uvicorn", "httpx", "chromadb")
        foreach ($package in $requiredPackages) {
            try {
                $null = python -c "import $package" 2>&1
                Write-ColorOutput "   ✅ $package is installed" $SuccessColor
            }
            catch {
                Write-ColorOutput "   ❌ $package is missing" $ErrorColor
                return $false
            }
        }
        return $true
    }
    catch {
        Write-ColorOutput "❌ Python is not available or not in PATH" $ErrorColor
        return $false
    }
}

function Test-NodeEnvironment {
    Write-ColorOutput "📦 Checking Node.js environment..." $InfoColor
    
    try {
        $nodeVersion = node --version 2>&1
        Write-ColorOutput "   Node.js: $nodeVersion" $SuccessColor
        
        if (Test-Path "package.json") {
            Write-ColorOutput "   ✅ package.json found" $SuccessColor
            
            if (Test-Path "node_modules") {
                Write-ColorOutput "   ✅ node_modules found" $SuccessColor
            }
            else {
                Write-ColorOutput "   ⚠️  node_modules not found. Run 'npm install'" $WarningColor
                return $false
            }
        }
        else {
            Write-ColorOutput "   ❌ package.json not found" $ErrorColor
            return $false
        }
        return $true
    }
    catch {
        Write-ColorOutput "❌ Node.js is not available or not in PATH" $ErrorColor
        return $false
    }
}

# Main script
Clear-Host
Write-ColorOutput "=" * 70 $InfoColor
Write-ColorOutput "🚀 ONEBOX AGGREGATOR - SERVICE STARTUP" $InfoColor
Write-ColorOutput "=" * 70 $InfoColor

# Create logs directory
$LogsDir = "logs"
if (!(Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
    Write-ColorOutput "📁 Created logs directory: $LogsDir" $InfoColor
}

# Check environment dependencies
if (!$SkipDependencyCheck) {
    Write-ColorOutput "`n🔍 CHECKING DEPENDENCIES..." $InfoColor
    Write-ColorOutput "-" * 50 $InfoColor
    
    $pythonOk = Test-PythonEnvironment
    $nodeOk = Test-NodeEnvironment
    
    if (!$pythonOk -or !$nodeOk) {
        Write-ColorOutput "`n❌ Dependency checks failed. Fix the above issues or use -SkipDependencyCheck to continue anyway." $ErrorColor
        exit 1
    }
    
    Write-ColorOutput "✅ All dependencies are available!" $SuccessColor
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-ColorOutput "⚠️  .env file not found. Copying from .env.example..." $WarningColor
        Copy-Item ".env.example" ".env"
        Write-ColorOutput "📝 Please edit .env file with your actual configuration values." $WarningColor
    }
    else {
        Write-ColorOutput "❌ No .env or .env.example file found!" $ErrorColor
        exit 1
    }
}

Write-ColorOutput "`n🚀 STARTING SERVICES..." $InfoColor
Write-ColorOutput "-" * 50 $InfoColor

$services = @()

if (!$StartGatewayOnly) {
    # Start VectorDB Service first
    $vectordbProcess = Start-ServiceInBackground -Command "python vectordb_service.py" -ServiceName "VectorDB Service" -LogFile "$LogsDir\vectordb_service.log"
    if ($vectordbProcess) {
        $services += @{Name = "VectorDB Service"; Process = $vectordbProcess; Url = "http://localhost:8001"; PID = $vectordbProcess.Id }
    }
    
    # Wait and check VectorDB health
    Start-Sleep -Seconds 5
    $vectordbHealthy = Test-ServiceHealth -Url "http://localhost:8001" -ServiceName "VectorDB Service"
    
    # Start API Server
    $apiProcess = Start-ServiceInBackground -Command "python api_server.py" -ServiceName "API Server" -LogFile "$LogsDir\api_server.log"
    if ($apiProcess) {
        $services += @{Name = "API Server"; Process = $apiProcess; Url = "http://localhost:3000"; PID = $apiProcess.Id }
    }
    
    # Wait and check API Server health
    Start-Sleep -Seconds 5
    $apiHealthy = Test-ServiceHealth -Url "http://localhost:3000" -ServiceName "API Server"
}

# Start API Gateway
$gatewayProcess = Start-ServiceInBackground -Command "python api_gateway_onebox.py" -ServiceName "API Gateway" -LogFile "$LogsDir\api_gateway.log"
if ($gatewayProcess) {
    $services += @{Name = "API Gateway"; Process = $gatewayProcess; Url = "http://localhost:3001"; PID = $gatewayProcess.Id }
}

# Wait and check Gateway health
Start-Sleep -Seconds 5
$gatewayHealthy = Test-ServiceHealth -Url "http://localhost:3001" -ServiceName "API Gateway"

Write-ColorOutput "`n📊 SERVICE STATUS SUMMARY" $InfoColor
Write-ColorOutput "-" * 50 $InfoColor

foreach ($service in $services) {
    $status = if (Test-ServiceHealth -Url $service.Url -ServiceName $service.Name -MaxRetries 1) { "✅ HEALTHY" } else { "❌ UNHEALTHY" }
    Write-ColorOutput "   $($service.Name): $status (PID: $($service.PID))" $(if ($status.StartsWith("✅")) { $SuccessColor } else { $ErrorColor })
    Write-ColorOutput "   URL: $($service.Url)" $InfoColor
}

Write-ColorOutput "`n🌐 API ENDPOINTS" $InfoColor
Write-ColorOutput "-" * 50 $InfoColor
Write-ColorOutput "   Gateway:     http://localhost:3001" $InfoColor
Write-ColorOutput "   API Docs:    http://localhost:3001/docs" $InfoColor
Write-ColorOutput "   Health:      http://localhost:3001/health" $InfoColor
Write-ColorOutput "   Search:      http://localhost:3001/api/search?q=test" $InfoColor
Write-ColorOutput "   Vector:      http://localhost:3001/api/vector-search?q=test" $InfoColor

Write-ColorOutput "`n📝 LOGS LOCATION" $InfoColor
Write-ColorOutput "-" * 50 $InfoColor
Get-ChildItem $LogsDir -Filter "*.log" | ForEach-Object {
    Write-ColorOutput "   $($_.Name): $($_.FullName)" $InfoColor
}

Write-ColorOutput "`n⚠️  IMPORTANT NOTES" $WarningColor
Write-ColorOutput "-" * 50 $WarningColor
Write-ColorOutput "   • Services are running in background windows" $WarningColor
Write-ColorOutput "   • Check logs in the '$LogsDir' directory for detailed output" $WarningColor
Write-ColorOutput "   • Use Task Manager to stop services if needed" $WarningColor
Write-ColorOutput "   • Press Ctrl+C in service windows to stop individual services" $WarningColor

Write-ColorOutput "`n🧪 QUICK TESTS" $InfoColor
Write-ColorOutput "-" * 50 $InfoColor
Write-ColorOutput "Run these commands to test the services:" $InfoColor
Write-ColorOutput "   curl http://localhost:3001/health" $InfoColor
Write-ColorOutput "   curl `"http://localhost:3001/api/search?q=test`"" $InfoColor

Write-ColorOutput "`n✅ STARTUP COMPLETE!" $SuccessColor
Write-ColorOutput "=" * 70 $SuccessColor