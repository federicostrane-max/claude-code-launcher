@echo off
REM ============================================
REM   Build script per Claude Launcher v4
REM   Con Screenshot Helper integrato
REM ============================================

echo.
echo Compilazione Claude Launcher v4
echo ================================
echo.

REM Installa dipendenze
echo Installazione dipendenze...
pip install Pillow pyinstaller --quiet

echo.
echo Compilazione in corso...

pyinstaller --onefile --windowed --name "Claude_Launcher_v4" --icon=NONE claude_launcher_v4.py

echo.
echo ================================
echo Compilazione completata!
echo L'exe si trova in: dist\Claude_Launcher_v4.exe
echo ================================
echo.

pause
