# Test Runner Script
# Run this script to execute tests with common configurations

Write-Host "=== Test Runner ===" -ForegroundColor Cyan
Write-Host ""

# Check if pytest is installed
try {
    $pytestVersion = uv run pytest --version 2>&1
    Write-Host "pytest found: $pytestVersion" -ForegroundColor Green
} catch {
    Write-Host "pytest not found." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Select test mode:" -ForegroundColor Yellow
Write-Host "1. Run all tests"
Write-Host "2. Run with coverage report"
Write-Host "3. Run unit tests only"
Write-Host "4. Run integration tests only"
Write-Host "5. Run workout tests"
Write-Host "6. Run feedback tests"
Write-Host "7. Run specific test file"
Write-Host "8. Run failed tests only"
Write-Host "9. Run with verbose output + coverage"
Write-Host "0. Exit"
Write-Host ""

$choice = Read-Host "Enter your choice (0-9)"

switch ($choice) {
    "1" {
        Write-Host "`nRunning all tests..." -ForegroundColor Cyan
        uv run pytest tests/
    }
    "2" {
        Write-Host "`nRunning tests with coverage..." -ForegroundColor Cyan
        uv run pytest tests/ --cov --cov-report=term-missing --cov-report=html
        Write-Host "`nCoverage report generated in htmlcov/index.html" -ForegroundColor Green
    }
    "3" {
        Write-Host "`nRunning unit tests only..." -ForegroundColor Cyan
        uv run pytest tests/ -m unit
    }
    "4" {
        Write-Host "`nRunning integration tests only..." -ForegroundColor Cyan
        uv run pytest tests/ -m integration
    }
    "5" {
        Write-Host "`nRunning workout-related tests..." -ForegroundColor Cyan
        uv run pytest tests/ -m workout
    }
    "6" {
        Write-Host "`nRunning feedback-related tests..." -ForegroundColor Cyan
        uv run pytest tests/ -m feedback
    }
    "7" {
        Write-Host "`nAvailable test files:" -ForegroundColor Yellow
        Write-Host "  a. test_workout_endpoints.py"
        Write-Host "  b. test_assignment_endpoints.py"
        Write-Host "  c. test_feedback_endpoints.py"
        $fileChoice = Read-Host "Enter your choice (a-c)"
        
        $fileName = switch ($fileChoice) {
            "a" { "test_workout_endpoints.py" }
            "b" { "test_assignment_endpoints.py" }
            "c" { "test_feedback_endpoints.py" }
            default { "" }
        }
        
        if ($fileName) {
            Write-Host "`nRunning $fileName..." -ForegroundColor Cyan
            uv run pytest tests/$fileName -v
        } else {
            Write-Host "Invalid choice" -ForegroundColor Red
        }
    }
    "8" {
        Write-Host "`nRe-running failed tests..." -ForegroundColor Cyan
        uv run pytest tests/ --lf -v
    }
    "9" {
        Write-Host "`nRunning tests with verbose output and coverage..." -ForegroundColor Cyan
        uv run pytest tests/ -v --cov --cov-report=term-missing
    }
    "0" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Test Run Complete ===" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to see the coverage report
if ($choice -eq "2" -or $choice -eq "9") {
    $openReport = Read-Host "Open HTML coverage report in browser? (y/n)"
    if ($openReport -eq "y") {
        Start-Process "htmlcov/index.html"
    }
}
