@echo off
echo 🗄️ GT Question Generator 2.0 - Database Setup
echo ===============================================

echo.
echo Checking SQL Server installation...

REM Check if SQL Server is installed
sqlcmd -S localhost -Q "SELECT @@VERSION" >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ SQL Server not found or not accessible.
    echo.
    echo 📋 Please install SQL Server first:
    echo    1. Download SQL Server Express from Microsoft
    echo    2. Install with default settings
    echo    3. Enable TCP/IP protocol
    echo    4. Restart SQL Server service
    echo.
    echo 🔗 Download: https://www.microsoft.com/en-us/sql-server/sql-server-downloads
    pause
    exit /b 1
)

echo ✅ SQL Server is accessible.

echo.
echo Creating database and tables...
sqlcmd -S localhost -i database_setup.sql

if %errorLevel% neq 0 (
    echo ❌ Database setup failed.
    echo.
    echo 📋 Troubleshooting:
    echo    1. Check if SQL Server service is running
    echo    2. Verify you have database creation permissions
    echo    3. Check if database_setup.sql exists in current directory
    echo    4. Try running as administrator
    pause
    exit /b 1
)

echo ✅ Database setup completed successfully!

echo.
echo Testing database connection...
sqlcmd -S localhost -Q "USE GTQuestionDB; SELECT COUNT(*) FROM CourseMaster;" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ Database connection test passed.
) else (
    echo ⚠️ Database connection test failed.
)

echo.
echo 📋 Next steps:
echo    1. Update your application configuration
echo    2. Test the application
echo    3. Generate some test questions
echo.
echo 🔧 Configuration files to update:
echo    - app/services/db_service.py
echo    - .env file (if using environment variables)
echo.
pause 