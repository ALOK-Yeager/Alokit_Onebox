@echo off
REM =====================================================================
REM Onebox Aggregator - Simple Service Startup Script
REM =====================================================================
REM This batch script starts all services in separate command windows
REM =====================================================================

echo.
echo ======================================================================
echo                 ONEBOX AGGREGATOR - SERVICE STARTUP
echo ======================================================================
echo.

REM Check if .env file exists
if not exist ".env" (
    if exist ".env.example" (
        echo WARNING: .env file not found. Copying from .env.example...
        copy ".env.example" ".env"
        echo Please edit .env file with your actual configuration values.
        echo.
    ) else (
        echo ERROR: No .env or .env.example file found!
        pause
        exit /b 1
    )
)

REM Create logs directory
if not exist "logs" mkdir logs

echo Starting services...
echo.

REM Start VectorDB Service (port 8001)
echo [1/3] Starting VectorDB Service on port 8001...
start "VectorDB Service" cmd /k "python vectordb_service.py > logs\vectordb_service.log 2>&1"
timeout /t 3 /nobreak

REM Start API Server (port 3000)
echo [2/3] Starting API Server on port 3000...
start "API Server" cmd /k "python api_server.py > logs\api_server.log 2>&1"
timeout /t 3 /nobreak

REM Start API Gateway (port 3001)
echo [3/3] Starting API Gateway on port 3001...
start "API Gateway" cmd /k "python api_gateway_onebox.py > logs\api_gateway.log 2>&1"
timeout /t 3 /nobreak

echo.
echo ======================================================================
echo                           SERVICES STARTED
echo ======================================================================
echo.
echo Services are starting in separate windows:
echo   • VectorDB Service: http://localhost:8001
echo   • API Server:       http://localhost:3000  
echo   • API Gateway:      http://localhost:3001
echo.
echo API Gateway endpoints:
echo   • Health Check:     http://localhost:3001/health
echo   • API Docs:         http://localhost:3001/docs
echo   • Search:           http://localhost:3001/api/search?q=test
echo   • Vector Search:    http://localhost:3001/api/vector-search?q=test
echo.
echo Logs are saved in the 'logs' directory.
echo Close the service windows to stop the services.
echo.
echo Testing gateway health in 10 seconds...
timeout /t 10 /nobreak

REM Test gateway health
echo.
echo Testing API Gateway health...
curl -s http://localhost:3001/health
echo.
echo.
echo Startup complete! Check the service windows for detailed output.
pause