@echo off
echo ========================================
echo Comprehensive Codebase Cleanup
echo ========================================
echo.

echo Removing test files...
del /q test_*.py 2>nul
del /q test_*.png 2>nul

echo Removing debug files...
del /q debug_*.py 2>nul

echo Removing temporary diagram files...
del /q array_diagram.png 2>nul
del /q binary_search_tree_diagram.png 2>nul
del /q binary_tree_height.png 2>nul
del /q decision_tree_id3.png 2>nul
del /q hash_table_diagram.png 2>nul
del /q intermediate_code_generation_diagram.png 2>nul
del /q recursion_diagram.png 2>nul
del /q test_fallback_diagram.png 2>nul
del /q test_output.png 2>nul
del /q test_output2.png 2>nul
del /q test_output6.png 2>nul

echo Removing temporary scripts...
del /q update_graphviz.py 2>nul
del /q transfer_data.py 2>nul
del /q fixes.txt 2>nul
del /q app/fix_renderer.py 2>nul

echo Removing temporary batch files...
del /q update_to_github.bat 2>nul
del /q push_to_github.bat 2>nul
del /q cleanup_unnecessary_files.bat 2>nul

echo Removing backup renderer files...
del /q app/services/renderers/*.backup 2>nul

echo Removing temporary files from app directory...
del /q app/*.png 2>nul

echo.
echo ========================================
echo Cleanup Summary
echo ========================================
echo.
echo Removed files:
echo - Test files (test_*.py, test_*.png)
echo - Debug files (debug_*.py)
echo - Temporary diagram files (*.png in root)
echo - Temporary scripts (update_*.py, transfer_*.py)
echo - Temporary batch files (*.bat)
echo - Backup renderer files (*.backup)
echo - Temporary files in app/ directory
echo.
echo The codebase is now clean!
echo ========================================
pause 