@echo off
REM Script to extract and compile translations
REM Usage: Double-click this file or run: translations.bat

echo.
echo ========================================
echo   Fofofish - Translation Management
echo ========================================
echo.

cd /d "%~dp0"

if not exist "manage.py" (
    echo Error: manage.py not found!
    pause
    exit /b 1
)

echo Choose an option:
echo 1 - Extract translation strings from project
echo 2 - List all translation strings
echo 3 - Compile translations
echo 4 - Extract and Compile
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Extracting translations...
    python extract_translations.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo Listing translations...
    python list_translations.py
    pause
) else if "%choice%"=="3" (
    echo.
    echo Compiling translations...
    python compile_translations.py
    pause
) else if "%choice%"=="4" (
    echo.
    echo Extracting translations...
    python extract_translations.py
    echo.
    echo Compiling translations...
    python compile_translations.py
    pause
) else (
    echo Invalid choice!
    pause
    exit /b 1
)
