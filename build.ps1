# Build script for Audeo on Windows
# Usage: .\build.ps1 [--onedir] [--optimize] [--debug]
# Encoding: utf-8

param(
    [switch]$onedir = $false,
    [switch]$optimize = $false,
    [switch]$debug = $false
)

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Get the project root (directory where this script is located)
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                   Audeo Build Script                        " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check Python
Write-Host "`n[1/3] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python") {
    Write-Host "  + $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  - Python not found!" -ForegroundColor Red
    exit 1
}

# Check PyInstaller
Write-Host "`n[2/3] Checking PyInstaller..." -ForegroundColor Yellow
$pyinstaller = python -m pip show pyinstaller 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  + PyInstaller installed" -ForegroundColor Green
} else {
    Write-Host "  * Installing PyInstaller..." -ForegroundColor Yellow
    python -m pip install pyinstaller --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  + PyInstaller installed" -ForegroundColor Green
    } else {
        Write-Host "  - PyInstaller installation failed!" -ForegroundColor Red
        exit 1
    }
}

# Build arguments
Write-Host "`n[3/3] Building executable..." -ForegroundColor Yellow
$buildArgs = @("devscripts/build.py")

if ($onedir) {
    $buildArgs += "--onedir"
    Write-Host "  * Mode: Multiple files (onedir)" -ForegroundColor Cyan
} else {
    Write-Host "  * Mode: Single file (default)" -ForegroundColor Cyan
}

if ($optimize) {
    $buildArgs += "--optimize"
    Write-Host "  * Optimizing bytecode..." -ForegroundColor Cyan
}

if ($debug) {
    $buildArgs += "--debug"
    Write-Host "  * Debug mode enabled" -ForegroundColor Cyan
}

# Run build
python @buildArgs

# Check result
$lastExitCode = $LASTEXITCODE
if ($lastExitCode -eq 0) {
    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host "+ Build successful!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    
    $exePath = "$projectRoot\dist\Audeo.exe"
    if (Test-Path $exePath) {
        $sizeKB = (Get-Item $exePath).Length / 1024
        $sizeMB = [Math]::Round($sizeKB/1024, 2)
        Write-Host "`nExecutable: $exePath" -ForegroundColor Green
        Write-Host "Size: $sizeMB MB" -ForegroundColor Green
    }
} else {
    Write-Host "`n============================================================" -ForegroundColor Red
    Write-Host "- Build failed (exit code: $lastExitCode)" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    exit $lastExitCode
}
