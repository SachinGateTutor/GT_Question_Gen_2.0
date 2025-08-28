#!/bin/bash

echo "🧹 GT Question Generator 2.0 - Project Cleanup"
echo "================================================"

echo ""
echo "Removing test files..."
rm -f test_complete_system.py
rm -f test_db_connection.py
rm -f test_graphviz_fix.py
rm -f test_fixes.py
rm -f test_dynamic_libraries.py
rm -f test_with_diagram.py
rm -f test_direct.py
rm -f test_api_key.py
rm -f test_api.py
rm -f simple_test.py
rm -f check_key.py

echo ""
echo "Removing generated images from app directory..."
rm -f app/temp.png
rm -f app/neural_network.png
rm -f app/neural_network_diagram.png
rm -f app/compiler_phases_diagram.png
rm -f app/compiler_design.png
rm -f app/code_generation_diagram.png
rm -f app/compiler_phases.png
rm -f app/expert_system.png
rm -f app/firewall_diagram.png
rm -f app/binary_tree.png
rm -f app/batch_os_diagram.png
rm -f app/tcpip_diagram.png

echo ""
echo "Removing test output directory..."
rm -rf test_output

echo ""
echo "Removing generated images from static directories..."
rm -rf static/images
rm -rf app/static/images

echo ""
echo "Removing Python cache files..."
rm -rf app/__pycache__
rm -rf app/services/__pycache__

echo ""
echo "Removing redundant documentation..."
rm -f NETWORK_SETUP.md

echo ""
echo "Removing old startup scripts..."
rm -f start_server.sh
rm -f start_server.bat

echo ""
echo "Creating necessary directories..."
mkdir -p app/static/images
mkdir -p static/images
mkdir -p logs

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📋 Summary of removed files:"
echo "   - Test files (11 files)"
echo "   - Generated images (12 files)"
echo "   - Test output directory"
echo "   - Static image directories (regenerated on use)"
echo "   - Python cache directories"
echo "   - Redundant documentation"
echo "   - Old startup scripts"
echo ""
echo "📁 Kept important files:"
echo "   - Core application files"
echo "   - Production deployment files"
echo "   - Documentation (README.md, DEPLOYMENT_GUIDE.md)"
echo "   - Configuration files"
echo "" 