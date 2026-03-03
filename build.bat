@echo off
echo BDU LMS Tracker - Build Script
echo ==============================
echo.

REM 가상환경 활성화 (선택사항)
REM call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller build.spec --clean

echo.
echo Build complete!
echo Output: dist\BDU_LMS_Tracker.exe
pause
