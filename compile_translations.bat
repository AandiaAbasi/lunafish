@echo off
REM Script to compile translation messages on Windows
REM Usage: Double-click this file or run: compile_translations.bat

echo.
echo ========================================
echo   Fofofish - Compile Translation Files
echo ========================================
echo.

cd /d "%~dp0"

if not exist "manage.py" (
    echo Error: manage.py not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

echo Running: python compile_translations.py
python compile_translations.py

if errorlevel 1 (
    echo.
    echo Translation compilation failed!
    pause
    exit /b 1
) else (
    echo.
    echo Done!
    pause
    exit /b 0
)
