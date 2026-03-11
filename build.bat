@echo off
echo ========================================
echo BDU LMS Tracker - Build Script
echo ========================================
echo.

REM 의존성 설치
echo [1/3] Installing dependencies...
pip install -r requirements.txt -q

REM 이전 빌드 정리
echo [2/3] Cleaning previous build...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM PyInstaller 빌드
echo [3/3] Building EXE (folder format)...
pyinstaller build.spec --noconfirm

echo.
if exist "dist\BDU_LMS_Tracker\BDU_LMS_Tracker.exe" (
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo Output folder: dist\BDU_LMS_Tracker\
    echo EXE file: dist\BDU_LMS_Tracker\BDU_LMS_Tracker.exe
) else (
    echo ========================================
    echo Build failed! Check errors above.
    echo ========================================
)
echo.
pause
