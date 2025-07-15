@echo off
echo 🧹 GT Question Generator 2.0 - Project Cleanup
echo ===============================================

echo.
echo Removing test files...
del /q test_complete_system.py 2>nul
del /q test_db_connection.py 2>nul
del /q test_graphviz_fix.py 2>nul
del /q test_fixes.py 2>nul
del /q test_dynamic_libraries.py 2>nul
del /q test_with_diagram.py 2>nul
del /q test_direct.py 2>nul
del /q test_api_key.py 2>nul
del /q test_api.py 2>nul
del /q simple_test.py 2>nul
del /q check_key.py 2>nul

echo.
echo Removing generated images from app directory...
del /q app\temp.png 2>nul
del /q app\neural_network.png 2>nul
del /q app\neural_network_diagram.png 2>nul
del /q app\compiler_phases_diagram.png 2>nul
del /q app\compiler_design.png 2>nul
del /q app\code_generation_diagram.png 2>nul
del /q app\compiler_phases.png 2>nul
del /q app\expert_system.png 2>nul
del /q app\firewall_diagram.png 2>nul
del /q app\binary_tree.png 2>nul
del /q app\batch_os_diagram.png 2>nul
del /q app\tcpip_diagram.png 2>nul

echo.
echo Removing test output directory...
rmdir /s /q test_output 2>nul

echo.
echo Removing generated images from static directories...
rmdir /s /q static\images 2>nul
rmdir /s /q app\static\images 2>nul

echo.
echo Removing Python cache files...
rmdir /s /q app\__pycache__ 2>nul
rmdir /s /q app\services\__pycache__ 2>nul

echo.
echo Removing redundant documentation...
del /q NETWORK_SETUP.md 2>nul

echo.
echo Removing old startup scripts...
del /q start_server.sh 2>nul
del /q start_server.bat 2>nul

echo.
echo Creating necessary directories...
mkdir app\static\images 2>nul
mkdir static\images 2>nul
mkdir logs 2>nul

echo.
echo ✅ Cleanup completed!
echo.
echo 📋 Summary of removed files:
echo    - Test files (11 files)
echo    - Generated images (12 files)
echo    - Test output directory
echo    - Static image directories (regenerated on use)
echo    - Python cache directories
echo    - Redundant documentation
echo    - Old startup scripts
echo.
echo 📁 Kept important files:
echo    - Core application files
echo    - Production deployment files
echo    - Documentation (README.md, DEPLOYMENT_GUIDE.md)
echo    - Configuration files
echo.
pause 