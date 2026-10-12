@echo off
setlocal
chcp 65001 >nul
title Internet Doctor - daktor internet
cd /d "%~dp0"

rem ----------------------------------------------
rem  Internet Doctor launcher for Windows 10/11
rem  Checks Python, installs the UI library and
rem  starts the app. Right-click this file and
rem  choose "Run as administrator" for full
rem  repair power (netsh, DNS change, Winsock).
rem ----------------------------------------------

set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY (
    where python >nul 2>nul && set PY=python
)
if not defined PY (
    echo [ERROR] Python 3 was not found on this computer.
    echo.
    echo 1. Open https://www.python.org/downloads/
    echo 2. Install Python 3.9 or newer
    echo 3. IMPORTANT: tick "Add python.exe to PATH" in the installer
    echo 4. Run this file again
    echo.
    pause
    exit /b 1
)

%PY% -c "import customtkinter, pystray, PIL" >nul 2>nul
if errorlevel 1 (
    echo Installing the required libraries ^(first run only^)...
    %PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Could not install the libraries.
        echo Check your internet once, or run manually:
        echo     %PY% -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo Starting Internet Doctor...
%PY% main.py
if errorlevel 1 (
    echo.
    echo The app stopped with an error. See logs\ for details.
    pause
)
endlocal
