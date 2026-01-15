@echo off
REM ============================================
REM   Build script per Claude Launcher v5
REM   Con Screenshot + File Helper
REM ============================================

echo.
echo Compilazione Claude Launcher v5
echo ================================
echo.

REM Installa dipendenze
echo Installazione dipendenze...
pip install Pillow pyinstaller --quiet

echo.
echo Compilazione in corso...

pyinstaller --onefile --windowed --name "Claude_Launcher_v5" --icon=NONE claude_launcher_v5.py

echo.
echo ================================
echo Compilazione completata!
echo L'exe si trova in: dist\Claude_Launcher_v5.exe
echo ================================
echo.

pause
