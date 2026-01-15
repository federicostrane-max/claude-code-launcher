@echo off
setlocal EnableDelayedExpansion

REM ============================================
REM   Claude Code Launcher - Versione Batch
REM   Salva il percorso in un file config
REM ============================================

set "CONFIG_FILE=%~dp0claude_config.txt"
set "PROJECT_PATH="

REM Controlla se esiste il file di configurazione
if exist "%CONFIG_FILE%" (
    set /p PROJECT_PATH=<"%CONFIG_FILE%"
    echo.
    echo ========================================
    echo   CLAUDE CODE LAUNCHER
    echo ========================================
    echo.
    echo Percorso salvato: !PROJECT_PATH!
    echo.
    set /p "CHOICE=Usare questo percorso? [S/n] o inserisci nuovo percorso: "
    
    if /i "!CHOICE!"=="" goto :use_saved
    if /i "!CHOICE!"=="s" goto :use_saved
    if /i "!CHOICE!"=="si" goto :use_saved
    if /i "!CHOICE!"=="y" goto :use_saved
    if /i "!CHOICE!"=="yes" goto :use_saved
    if /i "!CHOICE!"=="n" goto :ask_new_path
    if /i "!CHOICE!"=="no" goto :ask_new_path
    
    REM L'utente ha inserito un percorso direttamente
    set "PROJECT_PATH=!CHOICE!"
    goto :validate_path
)

:ask_new_path
echo.
echo ========================================
echo   CLAUDE CODE LAUNCHER - Setup
echo ========================================
echo.
set /p "PROJECT_PATH=Inserisci il percorso della cartella del progetto: "

:validate_path
REM Rimuovi eventuali virgolette
set "PROJECT_PATH=!PROJECT_PATH:"=!"

REM Verifica che il percorso esista
if not exist "!PROJECT_PATH!" (
    echo.
    echo ERRORE: Il percorso "!PROJECT_PATH!" non esiste!
    echo.
    pause
    goto :ask_new_path
)

REM Salva il nuovo percorso
echo !PROJECT_PATH!>"%CONFIG_FILE%"
echo.
echo Percorso salvato: !PROJECT_PATH!

:use_saved
echo.
echo Avvio Claude Code...
echo.

REM Estrai la lettera del disco
set "DRIVE=!PROJECT_PATH:~0,2!"

REM Vai al disco
!DRIVE!

REM Vai alla cartella
cd "!PROJECT_PATH!"

echo ========================================
echo   Claude Code - Sessioni Recenti
echo ========================================
echo.

REM Avvia claude --resume
claude --resume
