@echo off
echo 🚀 GT Question Generator 2.0 - Hybrid Windows Setup
echo ===================================================
echo Architecture: Python Flask + .NET Backend
echo ===================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if .NET is installed
dotnet --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ .NET is not installed. Please install .NET 6/7/8 first.
    echo Download from: https://dotnet.microsoft.com/download
    echo This is required for the .NET backend service.
    pause
    exit /b 1
)

REM Check if Git is installed
git --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first.
    echo Download from: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed!

REM Create virtual environment
echo 🐍 Setting up Python virtual environment...
python -m venv venv
call venv\Scripts\activate

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo 📂 Creating directories...
if not exist "logs" mkdir logs
if not exist "app\static\images" mkdir app\static\images

REM Copy environment template
echo ⚙️ Setting up environment configuration...
if not exist ".env" (
    copy env.template .env
    echo ⚠️ Please edit .env file with your configuration:
    echo    - OpenAI API key
    echo    - .NET backend URL
    echo    - Database connection string
)

REM Configure network access
echo 🌐 Configuring network access...
python setup_network.py

echo.
echo ✅ Hybrid setup completed successfully!
echo.
echo 🏗️ Architecture Overview:
echo Frontend (HTML/JS) → Python Flask (AI Processing) → .NET Backend (Data Storage)
echo                    ↓
echo              Diagram Generation & Static Files
echo.
echo 📋 Next steps for Hybrid Architecture:
echo 1. Start .NET Backend service (port 5125)
echo 2. Start Python Flask service: python app\main.py (port 5000)
echo 3. Open index.html in your browser
echo 4. From other devices, open: http://YOUR_IP:5000
echo.
echo 🔧 Service Requirements:
echo - .NET Backend: Handles data management, storage, and retrieval
echo - Python Flask: Handles AI processing, diagram generation
echo - Both services must be running for full functionality
echo.
echo 🌐 Network Access:
echo - Frontend: http://YOUR_IP:5000 (served by Python Flask)
echo - Python API: http://YOUR_IP:5000/api/generate-question
echo - .NET API: http://YOUR_IP:5125/api/... (all data endpoints)
echo.
echo ⚠️ Important Notes:
echo - Make sure firewall allows connections on ports 5000 and 5125
echo - Both services must be running simultaneously
echo - .NET backend handles database setup via Entity Framework
echo.
pause 