@echo off
REM Build KA-BOL-AI executable and installer
REM Run from the installer/ directory

echo ============================================
echo  KA-BOL-AI Build Script
echo ============================================
echo.

REM Step 1: PyInstaller
echo [1/2] Building with PyInstaller...
echo.
pyinstaller kabolai.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed!
    pause
    exit /b 1
)

echo.
echo [1/2] PyInstaller build complete!
echo Output: dist\KA-BOL-AI\KA-BOL-AI.exe
echo.

REM Step 2: Inno Setup (if available)
where iscc >nul 2>nul
if %errorlevel% equ 0 (
    echo [2/2] Creating installer with Inno Setup...
    echo.
    iscc installer.iss
    if errorlevel 1 (
        echo.
        echo ERROR: Inno Setup failed!
        pause
        exit /b 1
    )
    echo.
    echo [2/2] Installer created!
    echo Output: ..\dist\KA-BOL-AI-Setup.exe
) else (
    echo [2/2] Inno Setup not found, skipping installer creation.
    echo Install it from: https://jrsoftware.org/isdl.php
    echo Then run: iscc installer.iss
)

echo.
echo ============================================
echo  Build complete!
echo ============================================
echo.
echo To test: dist\KA-BOL-AI\KA-BOL-AI.exe
echo.
pause
