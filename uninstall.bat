@echo off
setlocal enabledelayedexpansion

:: InstanceLLM Uninstaller

color 0C
echo.
echo ================================================================================
echo   InstanceLLM Uninstaller
echo ================================================================================
echo.
echo This will remove:
echo   - Virtual environment (.venv)
echo   - Start script (start-instancellm.bat)
echo   - Installation file (INSTALLATION.txt)
echo.
echo This will NOT remove:
echo   - Downloaded models (models\ folder)
echo   - Your instance configurations (localStorage in browser)
echo   - Source code files
echo.

choice /C YN /M "Do you want to continue with uninstallation"
if errorlevel 2 goto :cancel
if errorlevel 1 goto :uninstall

:uninstall
echo.
echo Uninstalling...

if exist ".venv" (
    echo Removing virtual environment...
    rmdir /s /q .venv
    echo Virtual environment removed
)

if exist "start-instancellm.bat" (
    echo Removing start script...
    del start-instancellm.bat
    echo Start script removed
)

if exist "INSTALLATION.txt" (
    echo Removing installation file...
    del INSTALLATION.txt
    echo Installation file removed
)

echo.
echo ================================================================================
echo   Uninstallation Complete!
echo ================================================================================
echo.
echo To completely remove InstanceLLM:
echo   1. Delete the models\ folder (if you want to remove downloaded models)
echo   2. Delete this entire directory
echo.
pause
exit /b 0

:cancel
echo.
echo Uninstallation cancelled.
echo.
pause
exit /b 0
