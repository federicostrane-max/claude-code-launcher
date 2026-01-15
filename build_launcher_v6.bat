@echo off
REM ============================================
REM   Build script per Claude Launcher v6
REM   Con Screenshot + File Helper + Scelta Sessione
REM ============================================

echo.
echo Compilazione Claude Launcher v6
echo ================================
echo.

REM Installa dipendenze
echo Installazione dipendenze...
pip install Pillow pyinstaller --quiet

echo.
echo Compilazione in corso...

pyinstaller --onefile --windowed --name "Claude_Launcher_v6" --icon=NONE claude_launcher_v6.py

echo.
echo ================================
echo Compilazione completata!
echo L'exe si trova in: dist\Claude_Launcher_v6.exe
echo ================================
echo.

pause
