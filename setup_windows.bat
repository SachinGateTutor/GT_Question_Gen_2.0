@echo off
echo 🚀 GT Question Generator 2.0 - Windows Setup
echo =============================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
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

REM Install dependencies
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
    echo    - Database credentials
    echo    - Other settings
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your configuration
echo 2. Set up SQL Server database
echo 3. Run: venv\Scripts\activate
echo 4. Run: python app\main.py
echo.
echo 🌐 Application will be available at: http://localhost:5000
echo.
pause 