@echo off
setlocal enabledelayedexpansion

REM ========================================
REM BDU LMS Tracker - Release Script
REM ========================================

set VERSION=1.0.0
set APP_NAME=BDU_LMS_Tracker
set ZIP_NAME=%APP_NAME%_v%VERSION%.zip

echo ========================================
echo BDU LMS Tracker Release Script
echo Version: v%VERSION%
echo ========================================
echo.

REM Step 1: Build
echo [1/5] Building application...
call build.bat
if not exist "dist\%APP_NAME%\%APP_NAME%.exe" (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

REM Step 2: Create ZIP
echo.
echo [2/5] Creating ZIP archive...
cd dist
if exist "%ZIP_NAME%" del "%ZIP_NAME%"
powershell -Command "Compress-Archive -Path '%APP_NAME%\*' -DestinationPath '%ZIP_NAME%' -Force"
cd ..

if not exist "dist\%ZIP_NAME%" (
    echo [ERROR] ZIP creation failed!
    pause
    exit /b 1
)
echo ZIP created: dist\%ZIP_NAME%

REM Step 3: Check GitHub CLI
echo.
echo [3/5] Checking GitHub CLI...
gh --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] GitHub CLI not installed.
    echo.
    echo To install GitHub CLI:
    echo   winget install GitHub.cli
    echo.
    echo After installation, run:
    echo   gh auth login
    echo.
    echo Then re-run this script.
    echo.
    echo Your ZIP file is ready at: dist\%ZIP_NAME%
    pause
    exit /b 0
)

REM Step 4: Create git tag
echo.
echo [4/5] Creating git tag v%VERSION%...
git tag -a v%VERSION% -m "Release v%VERSION%" 2>nul
if errorlevel 1 (
    echo Tag v%VERSION% already exists, skipping...
)
git push origin v%VERSION% 2>nul

REM Step 5: Create GitHub release
echo.
echo [5/5] Creating GitHub release...
gh release create v%VERSION% ^
    --title "BDU LMS 트래커 v%VERSION%" ^
    --notes-file RELEASE_NOTES.md ^
    "dist/%ZIP_NAME%#%APP_NAME%_v%VERSION%.zip (Windows)"

if errorlevel 0 (
    echo.
    echo ========================================
    echo Release v%VERSION% created successfully!
    echo ========================================
    echo.
    for /f "tokens=*" %%i in ('git remote get-url origin 2^>nul') do set REPO_URL=%%i
    echo Check your release at GitHub!
) else (
    echo.
    echo [ERROR] Failed to create release.
    echo Your ZIP file is ready at: dist\%ZIP_NAME%
)

echo.
pause
