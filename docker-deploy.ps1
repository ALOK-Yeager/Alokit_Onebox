# PowerShell Deployment Script for Onebox Aggregator Python Services
param(
    [Parameter(Position = 0)]
    [ValidateSet("build", "run", "start", "stop", "restart", "logs", "health", "clean", "help")]
    [string]$Command,
    
    [Parameter(Position = 1)]
    [ValidateSet("api-server", "vectordb", "api-gateway")]
    [string]$Service,
    
    [switch]$Help
)

# Configuration
$ImageName = "onebox-aggregator"
$Dockerfile = "Dockerfile.python"
$DockerComposeFile = "docker-compose.python.yml"

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Show-Usage {
    Write-Host @"
Onebox Aggregator Python Services Deployment Script

Usage: .\docker-deploy.ps1 [COMMAND] [SERVICE]

Commands:
  build [SERVICE]     Build Docker image(s)
  run [SERVICE]       Run a specific service
  start              Start all services with docker-compose
  stop               Stop all services
  restart            Restart all services
  logs [SERVICE]     Show logs for service(s)
  health             Check health of all services
  clean              Clean up containers and images
  help               Show this help message

Services:
  api-server         API Server (port 3000)
  vectordb           VectorDB Service (port 8001)  
  api-gateway        API Gateway (port 3001)

Examples:
  .\docker-deploy.ps1 build api-server     # Build API server image
  .\docker-deploy.ps1 run vectordb         # Run VectorDB service
  .\docker-deploy.ps1 start                # Start all services
  .\docker-deploy.ps1 logs api-gateway     # Show gateway logs
"@
}

function Test-DockerRunning {
    try {
        $null = docker info 2>$null
        return $true
    }
    catch {
        Write-ColorOutput "❌ Docker is not running. Please start Docker first." $ErrorColor
        return $false
    }
}

function Build-Service {
    param([string]$ServiceName)
    
    $ServiceScripts = @{
        "api-server"  = "api_server.py"
        "vectordb"    = "vectordb_service.py"
        "api-gateway" = "api_gateway_onebox.py"
    }
    
    if (-not $ServiceScripts.ContainsKey($ServiceName)) {
        Write-ColorOutput "❌ Unknown service: $ServiceName" $ErrorColor
        Write-ColorOutput "Available services: $($ServiceScripts.Keys -join ', ')" $InfoColor
        return $false
    }
    
    $Script = $ServiceScripts[$ServiceName]
    $Tag = "${ImageName}:${ServiceName}"
    
    Write-ColorOutput "🔨 Building $ServiceName image ($Tag)..." $InfoColor
    
    try {
        docker build -f $Dockerfile --build-arg SERVICE_SCRIPT=$Script -t $Tag .
        Write-ColorOutput "✅ $ServiceName image built successfully!" $SuccessColor
        return $true
    }
    catch {
        Write-ColorOutput "❌ Failed to build $ServiceName image: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Build-AllServices {
    Write-ColorOutput "🔨 Building all service images..." $InfoColor
    
    $Services = @("vectordb", "api-server", "api-gateway")
    $Success = $true
    
    foreach ($Service in $Services) {
        if (-not (Build-Service $Service)) {
            $Success = $false
        }
    }
    
    if ($Success) {
        Write-ColorOutput "✅ All images built successfully!" $SuccessColor
    }
    else {
        Write-ColorOutput "❌ Some images failed to build" $ErrorColor
    }
    
    return $Success
}

function Start-Service {
    param([string]$ServiceName)
    
    $ServicePorts = @{
        "api-server"  = "3000:3000"
        "vectordb"    = "8001:8001"
        "api-gateway" = "3001:3001"
    }
    
    if (-not $ServicePorts.ContainsKey($ServiceName)) {
        Write-ColorOutput "❌ Unknown service: $ServiceName" $ErrorColor
        Write-ColorOutput "Available services: $($ServicePorts.Keys -join ', ')" $InfoColor
        return $false
    }
    
    $Ports = $ServicePorts[$ServiceName]
    $Tag = "${ImageName}:${ServiceName}"
    $ContainerName = "onebox-$ServiceName"
    
    Write-ColorOutput "🚀 Running $ServiceName container..." $InfoColor
    
    # Stop and remove existing container if it exists
    try {
        docker stop $ContainerName 2>$null
        docker rm $ContainerName 2>$null
    }
    catch {
        # Container doesn't exist, continue
    }
    
    # Run the container
    try {
        if (Test-Path ".env") {
            docker run -d --name $ContainerName -p $Ports --env-file .env $Tag
        }
        else {
            docker run -d --name $ContainerName -p $Ports $Tag
        }
        
        $Port = ($Ports -split ':')[0]
        Write-ColorOutput "✅ $ServiceName is running on port $Port!" $SuccessColor
        Write-ColorOutput "📋 Container logs: docker logs $ContainerName" $InfoColor
        return $true
    }
    catch {
        Write-ColorOutput "❌ Failed to start $ServiceName: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Start-AllServices {
    Write-ColorOutput "🚀 Starting all services with docker-compose..." $InfoColor
    
    if (-not (Test-Path $DockerComposeFile)) {
        Write-ColorOutput "❌ Docker compose file not found: $DockerComposeFile" $ErrorColor
        return $false
    }
    
    try {
        docker-compose -f $DockerComposeFile up -d
        Write-ColorOutput "✅ All services started!" $SuccessColor
        Write-ColorOutput "📋 Services are starting up. Use 'health' command to check status." $InfoColor
        return $true
    }
    catch {
        Write-ColorOutput "❌ Failed to start services: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Stop-AllServices {
    Write-ColorOutput "🛑 Stopping all services..." $InfoColor
    
    try {
        if (Test-Path $DockerComposeFile) {
            docker-compose -f $DockerComposeFile down
        }
        
        # Also stop any individually started containers
        @("onebox-api-server", "onebox-vectordb", "onebox-api-gateway") | ForEach-Object {
            try { docker stop $_ 2>$null } catch { }
        }
        
        Write-ColorOutput "✅ All services stopped!" $SuccessColor
        return $true
    }
    catch {
        Write-ColorOutput "❌ Failed to stop services: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Restart-AllServices {
    Write-ColorOutput "🔄 Restarting all services..." $InfoColor
    Stop-AllServices
    Start-AllServices
}

function Show-Logs {
    param([string]$ServiceName = "")
    
    try {
        if ([string]::IsNullOrEmpty($ServiceName)) {
            Write-ColorOutput "📋 Showing logs for all services..." $InfoColor
            docker-compose -f $DockerComposeFile logs -f
        }
        else {
            Write-ColorOutput "📋 Showing logs for $ServiceName..." $InfoColor
            docker-compose -f $DockerComposeFile logs -f $ServiceName
        }
    }
    catch {
        Write-ColorOutput "❌ Failed to show logs: $($_.Exception.Message)" $ErrorColor
    }
}

function Test-ServiceHealth {
    Write-ColorOutput "🏥 Checking service health..." $InfoColor
    
    $Services = @(
        @{Name = "api-server"; Port = 3000 },
        @{Name = "vectordb"; Port = 8001 },
        @{Name = "api-gateway"; Port = 3001 }
    )
    
    foreach ($Service in $Services) {
        Write-ColorOutput "🔍 Checking $($Service.Name) (port $($Service.Port))..." $InfoColor
        
        try {
            $Response = Invoke-RestMethod -Uri "http://localhost:$($Service.Port)/health" -Method Get -TimeoutSec 5
            Write-ColorOutput "✅ $($Service.Name) is healthy ✓" $SuccessColor
        }
        catch {
            Write-ColorOutput "⚠️ $($Service.Name) is not responding ✗" $WarningColor
        }
    }
}

function Remove-AllResources {
    $Response = Read-Host "⚠️ This will remove all Onebox containers and images. Continue? (y/N)"
    
    if ($Response -match "^[Yy]$") {
        Write-ColorOutput "🧹 Cleaning up containers and images..." $InfoColor
        
        try {
            # Stop and remove containers
            if (Test-Path $DockerComposeFile) {
                docker-compose -f $DockerComposeFile down -v 2>$null
            }
            
            @("onebox-api-server", "onebox-vectordb", "onebox-api-gateway") | ForEach-Object {
                try { 
                    docker stop $_ 2>$null
                    docker rm $_ 2>$null 
                }
                catch { }
            }
            
            # Remove images
            @("${ImageName}:api-server", "${ImageName}:vectordb", "${ImageName}:api-gateway") | ForEach-Object {
                try { docker rmi $_ 2>$null } catch { }
            }
            
            Write-ColorOutput "✅ Cleanup completed!" $SuccessColor
        }
        catch {
            Write-ColorOutput "❌ Cleanup failed: $($_.Exception.Message)" $ErrorColor
        }
    }
    else {
        Write-ColorOutput "🚫 Cleanup cancelled." $InfoColor
    }
}

# Main script logic
if ($Help -or $Command -eq "help" -or [string]::IsNullOrEmpty($Command)) {
    Show-Usage
    exit 0
}

if (-not (Test-DockerRunning)) {
    exit 1
}

switch ($Command) {
    "build" {
        if ([string]::IsNullOrEmpty($Service)) {
            Build-AllServices
        }
        else {
            Build-Service $Service
        }
    }
    "run" {
        if ([string]::IsNullOrEmpty($Service)) {
            Write-ColorOutput "❌ Service name required for run command" $ErrorColor
            Show-Usage
            exit 1
        }
        if (Build-Service $Service) {
            Start-Service $Service
        }
    }
    "start" {
        Start-AllServices
    }
    "stop" {
        Stop-AllServices
    }
    "restart" {
        Restart-AllServices
    }
    "logs" {
        Show-Logs $Service
    }
    "health" {
        Test-ServiceHealth
    }
    "clean" {
        Remove-AllResources
    }
    default {
        Write-ColorOutput "❌ Unknown command: $Command" $ErrorColor
        Show-Usage
        exit 1
    }
}