@echo off
setlocal enabledelayedexpansion

:: InstanceLLM Installer for Windows
:: This script sets up the InstanceLLM environment

color 0A
echo.
echo ================================================================================
echo   InstanceLLM Installer
echo   Windows 95 Style LLM Instance Manager
echo ================================================================================
echo.

:: Check for Python
echo [1/6] Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

:: Create virtual environment
echo.
echo [2/6] Creating virtual environment...
if exist ".venv" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

:: Activate virtual environment and install dependencies
echo.
echo [3/6] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
) else (
    echo Installing core dependencies...
    pip install fastapi uvicorn llama-cpp-python python-multipart huggingface_hub
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
)
echo Dependencies installed successfully!

:: Create models directory
echo.
echo [4/6] Setting up directories...
if not exist "models" mkdir models
echo models\ directory ready

:: Create desktop shortcut
echo.
echo [5/6] Creating shortcuts...

:: Create start script
echo @echo off > start-instancellm.bat
echo cd /d "%%~dp0" >> start-instancellm.bat
echo echo Starting InstanceLLM Server... >> start-instancellm.bat
echo echo. >> start-instancellm.bat
echo echo Checking for downloaded models... >> start-instancellm.bat
echo if not exist "models\*.gguf" ( >> start-instancellm.bat
echo     echo [WARNING] No models found in models\ directory >> start-instancellm.bat
echo     echo. >> start-instancellm.bat
echo     echo You can download models from the web interface: >> start-instancellm.bat
echo     echo 1. Click on the Models tab >> start-instancellm.bat
echo     echo 2. Choose a model and click "Download" >> start-instancellm.bat
echo     echo. >> start-instancellm.bat
echo     echo Starting with default configuration... >> start-instancellm.bat
echo     echo. >> start-instancellm.bat
echo     .venv\Scripts\python.exe llm_server.py 8000 >> start-instancellm.bat
echo ^) else ( >> start-instancellm.bat
echo     for %%%%f in (models\*.gguf) do ( >> start-instancellm.bat
echo         echo Using model: %%%%f >> start-instancellm.bat
echo         echo. >> start-instancellm.bat
echo         echo Access the interface at: http://localhost:8000 >> start-instancellm.bat
echo         echo. >> start-instancellm.bat
echo         .venv\Scripts\python.exe llm_server.py "%%%%f" 8000 >> start-instancellm.bat
echo         goto :end >> start-instancellm.bat
echo     ^) >> start-instancellm.bat
echo ^) >> start-instancellm.bat
echo :end >> start-instancellm.bat
echo pause >> start-instancellm.bat

echo Start script created: start-instancellm.bat

:: Create README
echo.
echo [6/6] Creating documentation...
if not exist "INSTALLATION.txt" (
    echo InstanceLLM - Installation Complete! > INSTALLATION.txt
    echo. >> INSTALLATION.txt
    echo TO START THE SERVER: >> INSTALLATION.txt
    echo   Double-click: start-instancellm.bat >> INSTALLATION.txt
    echo. >> INSTALLATION.txt
    echo FIRST TIME SETUP: >> INSTALLATION.txt
    echo   1. Run start-instancellm.bat >> INSTALLATION.txt
    echo   2. Open http://localhost:8000 in your browser >> INSTALLATION.txt
    echo   3. Go to the Models tab >> INSTALLATION.txt
    echo   4. Download a model (TinyLlama recommended for testing) >> INSTALLATION.txt
    echo   5. Restart the server >> INSTALLATION.txt
    echo. >> INSTALLATION.txt
    echo CREATING INSTANCES: >> INSTALLATION.txt
    echo   1. Click the + button in the Instances panel >> INSTALLATION.txt
    echo   2. Enter a name, select a model, and choose a port >> INSTALLATION.txt
    echo   3. Click Start to launch the instance >> INSTALLATION.txt
    echo. >> INSTALLATION.txt
    echo FEATURES: >> INSTALLATION.txt
    echo   - Windows 95 retro interface >> INSTALLATION.txt
    echo   - Multiple LLM instances on different ports >> INSTALLATION.txt
    echo   - Model downloading from Hugging Face >> INSTALLATION.txt
    echo   - Microsoft Sam text-to-speech >> INSTALLATION.txt
    echo   - Streaming and non-streaming chat modes >> INSTALLATION.txt
    echo. >> INSTALLATION.txt
    echo TROUBLESHOOTING: >> INSTALLATION.txt
    echo   - Port already in use: Change the port number in start script >> INSTALLATION.txt
    echo   - Model not loading: Check models\ folder for .gguf files >> INSTALLATION.txt
    echo   - Voice not working: Check browser audio permissions >> INSTALLATION.txt
    echo. >> INSTALLATION.txt
    echo For more info: https://github.com/yourusername/InstanceLLM >> INSTALLATION.txt
)

echo.
echo ================================================================================
echo   Installation Complete!
echo ================================================================================
echo.
echo Next steps:
echo   1. Double-click start-instancellm.bat to start the server
echo   2. Open http://localhost:8000 in your web browser
echo   3. Download a model from the Models tab
echo.
echo Read INSTALLATION.txt for detailed instructions
echo.
pause
