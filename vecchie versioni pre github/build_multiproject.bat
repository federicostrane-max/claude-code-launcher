@echo off
REM ============================================
REM   Build script per Claude Launcher Multi-Project
REM ============================================

echo.
echo Compilazione Claude Launcher Multi-Project
echo ==========================================
echo.

pip install pyinstaller --quiet

pyinstaller --onefile --console --name "Claude_Launcher_MultiProject" claude_launcher_multiproject.py

echo.
echo ==========================================
echo Compilazione completata!
echo L'exe si trova in: dist\Claude_Launcher_MultiProject.exe
echo ==========================================
echo.

pause
