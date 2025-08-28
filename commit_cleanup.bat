@echo off
echo ========================================
echo Committing cleanup changes to GitHub
echo ========================================
echo.

echo Checking git status...
git status

echo.
echo Adding all changes...
git add -A

echo.
echo Committing cleanup changes...
git commit -m "chore: Clean up codebase - Remove unnecessary test files and temporary artifacts - Delete debug scripts and temporary diagrams - Clean up backup files and temporary scripts - Improve codebase organization and reduce repository size - Remove test_*.py, debug_*.py, and temporary *.png files - Clean up app/ directory of temporary files - Remove backup renderer files and temporary batch files"

echo.
echo Pushing to GitHub...
git push origin v4.5_ML

echo.
echo ========================================
echo Cleanup changes pushed successfully!
echo ========================================
echo.
echo Summary of cleanup:
echo - Removed test files (test_*.py, test_*.png)
echo - Removed debug files (debug_*.py)
echo - Removed temporary diagram files (*.png)
echo - Removed temporary scripts (fix_*.py, update_*.py)
echo - Removed backup files (*.backup, *.bak)
echo - Cleaned up app/ directory
echo - Removed temporary batch files
echo.
pause 