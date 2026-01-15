@echo off
REM ============================================
REM   Apri cartella sessioni Claude
REM   Per esplorare manualmente i progetti
REM ============================================

set "CLAUDE_PROJECTS=%USERPROFILE%\.claude\projects"

echo.
echo Cartella progetti Claude: %CLAUDE_PROJECTS%
echo.

if exist "%CLAUDE_PROJECTS%" (
    echo Apertura cartella...
    explorer "%CLAUDE_PROJECTS%"
    
    echo.
    echo Contenuto:
    echo ─────────────────────────────────────────
    dir /b "%CLAUDE_PROJECTS%"
    echo ─────────────────────────────────────────
) else (
    echo [ERRORE] Cartella non trovata!
    echo Non hai ancora sessioni salvate con Claude Code.
)

echo.
pause
