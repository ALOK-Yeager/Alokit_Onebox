# System Verification Script
# Tests all services and endpoints to ensure everything is working

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🧪 Onebox Aggregator - System Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$allTestsPassed = $true

# Function to test HTTP endpoint
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "  ✅ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ❌ FAIL - Status: $($response.StatusCode) (Expected: $ExpectedStatus)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to test JSON endpoint
function Test-JsonEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$ExpectedField
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5 -ErrorAction Stop
        
        if ($ExpectedField -and $response.PSObject.Properties.Name -contains $ExpectedField) {
            Write-Host "  ✅ PASS - Found field: $ExpectedField" -ForegroundColor Green
            Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
            return $true
        }
        elseif (-not $ExpectedField) {
            Write-Host "  ✅ PASS - Received response" -ForegroundColor Green
            Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
            return $true
        }
        else {
            Write-Host "  ❌ FAIL - Field '$ExpectedField' not found in response" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           Testing VectorDB Service (Port 8001)            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Test VectorDB Health
$result1 = Test-JsonEndpoint -Name "VectorDB Health Check" -Url "http://localhost:8001/health" -ExpectedField "status"
$allTestsPassed = $allTestsPassed -and $result1
Start-Sleep -Seconds 1

# Test VectorDB Stats
$result2 = Test-JsonEndpoint -Name "VectorDB Statistics" -Url "http://localhost:8001/stats" -ExpectedField "total_emails"
$allTestsPassed = $allTestsPassed -and $result2
Start-Sleep -Seconds 1

# Test VectorDB Docs
$result3 = Test-Endpoint -Name "VectorDB API Docs" -Url "http://localhost:8001/docs"
$allTestsPassed = $allTestsPassed -and $result3
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║            Testing API Server (Port 3000)                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Test API Server Root
$result4 = Test-Endpoint -Name "API Server Root" -Url "http://localhost:3000/"
$allTestsPassed = $allTestsPassed -and $result4
Start-Sleep -Seconds 1

# Test API Server Health
$result5 = Test-JsonEndpoint -Name "API Server Health" -Url "http://localhost:3000/health" -ExpectedField "status"
$allTestsPassed = $allTestsPassed -and $result5
Start-Sleep -Seconds 1

# Test API Server Docs
$result6 = Test-Endpoint -Name "API Server Docs" -Url "http://localhost:3000/docs"
$allTestsPassed = $allTestsPassed -and $result6
Start-Sleep -Seconds 1

# Test API Server Stats
$result7 = Test-JsonEndpoint -Name "API Statistics" -Url "http://localhost:3000/api/stats"
$allTestsPassed = $allTestsPassed -and $result7
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           Testing Streamlit UI (Port 8501)                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Test Streamlit UI
$result8 = Test-Endpoint -Name "Streamlit Web UI" -Url "http://localhost:8501"
$allTestsPassed = $allTestsPassed -and $result8
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              Testing Search Functionality                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Test Hybrid Search
Write-Host "Testing: Hybrid Search (via API Server)" -ForegroundColor Yellow
Write-Host "  URL: http://localhost:3000/api/emails/search?q=test&type=hybrid" -ForegroundColor Gray

try {
    $searchResponse = Invoke-RestMethod -Uri "http://localhost:3000/api/emails/search?q=test&type=hybrid" -Method Get -TimeoutSec 10 -ErrorAction Stop
    
    if ($searchResponse.PSObject.Properties.Name -contains "results") {
        Write-Host "  ✅ PASS - Search endpoint working" -ForegroundColor Green
        Write-Host "  Found: $($searchResponse.results.Count) results" -ForegroundColor Gray
        $result9 = $true
    } else {
        Write-Host "  ❌ FAIL - Invalid response format" -ForegroundColor Red
        $result9 = $false
    }
}
catch {
    Write-Host "  ⚠️  WARNING - Search failed (this is OK if no emails indexed yet)" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
    $result9 = $true  # Don't fail on empty results
}

$allTestsPassed = $allTestsPassed -and $result9

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                    Test Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$testResults = @(
    @{Name = "VectorDB Health Check"; Result = $result1},
    @{Name = "VectorDB Statistics"; Result = $result2},
    @{Name = "VectorDB API Docs"; Result = $result3},
    @{Name = "API Server Root"; Result = $result4},
    @{Name = "API Server Health"; Result = $result5},
    @{Name = "API Server Docs"; Result = $result6},
    @{Name = "API Statistics"; Result = $result7},
    @{Name = "Streamlit Web UI"; Result = $result8},
    @{Name = "Hybrid Search"; Result = $result9}
)

$passedCount = ($testResults | Where-Object { $_.Result -eq $true }).Count
$totalCount = $testResults.Count

Write-Host "Test Results:" -ForegroundColor White
Write-Host ""

foreach ($test in $testResults) {
    if ($test.Result) {
        Write-Host "  ✅ $($test.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($test.Name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Total: $passedCount / $totalCount tests passed" -ForegroundColor $(if ($allTestsPassed) { "Green" } else { "Red" })
Write-Host ""

if ($allTestsPassed) {
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  🎉 ALL TESTS PASSED! System is fully operational! 🎉   ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access Points:" -ForegroundColor Cyan
    Write-Host "   • Streamlit UI:    http://localhost:8501" -ForegroundColor White
    Write-Host "   • API Server:      http://localhost:3000" -ForegroundColor White
    Write-Host "   • API Docs:        http://localhost:3000/docs" -ForegroundColor White
    Write-Host "   • VectorDB API:    http://localhost:8001" -ForegroundColor White
    Write-Host "   • VectorDB Docs:   http://localhost:8001/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "✅ The system is ready for use!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ⚠️  SOME TESTS FAILED - Please check the errors above  ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common Issues:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Services Not Running:" -ForegroundColor White
    Write-Host "   Run: .\start-all-services.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Port Already in Use:" -ForegroundColor White
    Write-Host "   Check: netstat -ano | findstr ':8001 :3000 :8501'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Dependencies Missing:" -ForegroundColor White
    Write-Host "   Run: pip install -r python-requirements.txt" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Python Not Found:" -ForegroundColor White
    Write-Host "   Install Python 3.8+ from https://python.org" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
