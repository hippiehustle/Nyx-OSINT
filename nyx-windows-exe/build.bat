@echo off
REM Build script for Nyx Windows executables

echo ========================================
echo Nyx Windows Executable Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

REM Check if PyInstaller is installed
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install -r requirements-build.txt
    if errorlevel 1 (
        echo ERROR: Failed to install build dependencies
        exit /b 1
    )
)

REM Prepare resources
echo Preparing resources...
python build_scripts\prepare_resources.py
if errorlevel 1 (
    echo ERROR: Resource preparation failed
    exit /b 1
)

REM Build all variants
echo.
echo Building all executable variants...
python build_scripts\build_all.py
if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executables are in the 'dist' directory.

pause

