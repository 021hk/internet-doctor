@echo off
setlocal
cd /d "%~dp0"
title Internet Doctor - EXE Builder
echo ==================================================
echo   Internet Doctor ^| Build Windows EXE
echo   (installers need Inno Setup - see installer.iss)
echo ==================================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (set "PY=py") else (set "PY=python")

echo [1/3] Installing build requirements...
%PY% -m pip install --upgrade pip >nul
%PY% -m pip install -r requirements.txt pyinstaller
if %errorlevel% neq 0 goto :fail

echo.
echo [2/3] Building dist\InternetDoctor.exe (this takes a few minutes)...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name InternetDoctor ^
  --icon assets\icon.ico ^
  --add-data "assets;assets" ^
  --collect-all customtkinter ^
  --hidden-import pystray._win32 ^
  main.py
if %errorlevel% neq 0 goto :fail

echo.
echo [3/3] Cleaning temp build folders...
if exist build rmdir /s /q build
del InternetDoctor.spec >nul 2>nul

echo.
echo ==================================================
echo   DONE!
echo   EXE:       dist\InternetDoctor.exe
echo   Installer: build it with Inno Setup (installer.iss)
echo              OR download InternetDoctor-Setup.exe
echo              from the GitHub Releases page.
echo ==================================================
pause
exit /b 0

:fail
echo.
echo BUILD FAILED - check the messages above.
pause
exit /b 1
