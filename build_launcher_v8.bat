@echo off
REM ============================================
REM   Build script per Claude Launcher v8
REM   Con Multi-Tab Support
REM ============================================

echo.
echo Compilazione Claude Launcher v8
echo ================================
echo.

REM Installa dipendenze
echo Installazione dipendenze...
pip install Pillow pyinstaller --quiet

echo.
echo Compilazione in corso...

pyinstaller --onefile --windowed --name "Claude_Launcher_v8" --icon=NONE claude_launcher_v6.py

echo.
echo ================================
echo Compilazione completata!
echo L'exe si trova in: dist\Claude_Launcher_v8.exe
echo ================================
echo.

pause
