@echo off 
cd /d "%~dp0" 
echo Starting InstanceLLM Server... 
echo. 
echo Checking for downloaded models... 
if not exist "models\*.gguf" ( 
    echo [WARNING] No models found in models\ directory 
    echo. 
    echo You can download models from the web interface: 
    echo 1. Click on the Models tab 
    echo 2. Choose a model and click "Download" 
    echo. 
    echo Starting with default configuration... 
    echo. 
    .venv\Scripts\python.exe llm_server.py 8000 
) else ( 
    for %%f in (models\*.gguf) do ( 
        echo Using model: %%f 
        echo. 
        echo Access the interface at: http://localhost:8000 
        echo. 
        .venv\Scripts\python.exe llm_server.py "%%f" 8000 
        goto :end 
    ) 
) 
:end 
pause 
