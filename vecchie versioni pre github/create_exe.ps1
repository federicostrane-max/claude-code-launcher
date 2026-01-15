# ============================================
#   Converti BAT in EXE usando PowerShell
#   Non richiede Python!
# ============================================

$batContent = @'
@echo off
setlocal EnableDelayedExpansion

set "CONFIG_FILE=%~dp0claude_config.txt"
set "PROJECT_PATH="

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
set "PROJECT_PATH=!PROJECT_PATH:"=!"

if not exist "!PROJECT_PATH!" (
    echo.
    echo ERRORE: Il percorso "!PROJECT_PATH!" non esiste!
    echo.
    pause
    goto :ask_new_path
)

echo !PROJECT_PATH!>"%CONFIG_FILE%"
echo.
echo Percorso salvato: !PROJECT_PATH!

:use_saved
echo.
echo Avvio Claude Code...
echo.

set "DRIVE=!PROJECT_PATH:~0,2!"
!DRIVE!
cd "!PROJECT_PATH!"

echo ========================================
echo   Claude Code - Sessioni Recenti
echo ========================================
echo.

claude --resume
'@

# Percorso output
$exePath = Join-Path $PSScriptRoot "Claude_Launcher.exe"

# Crea un wrapper C# per il batch
$code = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;

class Program {
    static void Main() {
        string batPath = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location), "claude_launcher_temp.bat");
        File.WriteAllText(batPath, @"$($batContent -replace '"', '""')");
        
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "cmd.exe";
        psi.Arguments = "/k \"" + batPath + "\"";
        psi.UseShellExecute = true;
        
        Process.Start(psi);
    }
}
"@

Add-Type -TypeDefinition $code -OutputAssembly $exePath -OutputType ConsoleApplication

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   EXE creato con successo!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "File: $exePath" -ForegroundColor Yellow
Write-Host ""
