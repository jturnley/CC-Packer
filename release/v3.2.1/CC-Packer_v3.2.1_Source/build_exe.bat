@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Checking required files...
if not exist "bsarch.exe" (
    echo ERROR: bsarch.exe not found in project directory!
    echo Please place bsarch.exe in the same directory as this script.
    pause
    exit /b 1
)
if not exist "BSARCH_LICENSE.txt" (
    echo ERROR: BSARCH_LICENSE.txt not found in project directory!
    echo Please ensure the license file exists.
    pause
    exit /b 1
)
echo Found bsarch.exe and license file.

echo.
echo Building executable...
pyinstaller --noconfirm CCPacker.spec

echo.
echo Copying additional files to dist...
copy /Y "bsarch.exe" "dist\bsarch.exe"
copy /Y "BSARCH_LICENSE.txt" "dist\BSARCH_LICENSE.txt"
copy /Y "LICENSE" "dist\LICENSE"
copy /Y "README.md" "dist\README.md"

echo.
echo Build complete! Files are in the 'dist' folder.
echo Contents:
dir /b dist
pause