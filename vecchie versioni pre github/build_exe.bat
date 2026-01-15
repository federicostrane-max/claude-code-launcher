@echo off
REM ============================================
REM   Build script per Claude Launcher
REM   Richiede Python e PyInstaller installati
REM ============================================

echo.
echo Compilazione Claude Launcher in .exe
echo =====================================
echo.

REM Installa PyInstaller se non presente
pip install pyinstaller --quiet

REM Compila lo script in un singolo .exe
pyinstaller --onefile --console --name "Claude_Launcher" --icon=NONE claude_launcher.py

echo.
echo =====================================
echo Compilazione completata!
echo L'exe si trova in: dist\Claude_Launcher.exe
echo =====================================
echo.

pause
