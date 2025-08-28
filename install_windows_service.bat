@echo off
echo Installing GT Question Generator as Windows Service...

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as administrator...
) else (
    echo Please run this script as administrator
    pause
    exit /b 1
)

REM Install NSSM (Non-Sucking Service Manager) if not present
if not exist "nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force"
    move "nssm-2.24\win64\nssm.exe" .
    rmdir /s "nssm-2.24"
    del "nssm.zip"
)

REM Get current directory
set "CURRENT_DIR=%~dp0"
set "PYTHON_PATH=%CURRENT_DIR%venv\Scripts\python.exe"
set "SCRIPT_PATH=%CURRENT_DIR%start_production.py"

REM Install the service
echo Installing service...
nssm.exe install "GTQuestionGenerator" "%PYTHON_PATH%" "%SCRIPT_PATH%"
nssm.exe set "GTQuestionGenerator" AppDirectory "%CURRENT_DIR%"
nssm.exe set "GTQuestionGenerator" Description "GT Question Generator 2.0 - AI-powered MCQ Generator"
nssm.exe set "GTQuestionGenerator" Start SERVICE_AUTO_START

REM Set environment variables
nssm.exe set "GTQuestionGenerator" AppEnvironmentExtra "FLASK_HOST=0.0.0.0"
nssm.exe set "GTQuestionGenerator" AppEnvironmentExtra "FLASK_PORT=5000"
nssm.exe set "GTQuestionGenerator" AppEnvironmentExtra "FLASK_ENV=production"

echo Service installed successfully!
echo.
echo To start the service: net start GTQuestionGenerator
echo To stop the service: net stop GTQuestionGenerator
echo To remove the service: nssm.exe remove GTQuestionGenerator
echo.
pause 