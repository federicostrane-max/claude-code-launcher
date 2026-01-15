"""
Claude Code Launcher
Apre un terminale, naviga alla cartella del progetto e lancia claude --resume
Il percorso viene salvato in un file config per usi futuri
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# File di configurazione nella stessa cartella dell'exe
def get_config_path():
    if getattr(sys, 'frozen', False):
        # Se è un exe compilato
        base_path = Path(sys.executable).parent
    else:
        # Se è uno script python
        base_path = Path(__file__).parent
    return base_path / "claude_launcher_config.json"

def load_config():
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def get_project_path():
    config = load_config()
    
    if 'project_path' in config:
        path = config['project_path']
        print(f"\n📁 Percorso salvato: {path}")
        print("\nVuoi usare questo percorso? [S/n] oppure inserisci un nuovo percorso: ", end="")
        response = input().strip()
        
        if response.lower() in ['', 's', 'si', 'sì', 'y', 'yes']:
            return path
        elif response.lower() in ['n', 'no']:
            # Chiedi nuovo percorso
            print("\nInserisci il nuovo percorso della cartella del progetto: ", end="")
            new_path = input().strip().strip('"').strip("'")
        else:
            # L'utente ha inserito direttamente un percorso
            new_path = response.strip('"').strip("'")
    else:
        print("\n🚀 Claude Code Launcher - Prima configurazione")
        print("=" * 50)
        print("\nInserisci il percorso della cartella del progetto")
        print("(es: D:\\downloads\\Lux\\app lux 1): ", end="")
        new_path = input().strip().strip('"').strip("'")
    
    # Verifica che il percorso esista
    if os.path.isdir(new_path):
        config['project_path'] = new_path
        save_config(config)
        print(f"\n✅ Percorso salvato: {new_path}")
        return new_path
    else:
        print(f"\n❌ Errore: Il percorso '{new_path}' non esiste!")
        input("\nPremi INVIO per riprovare...")
        return get_project_path()

def main():
    print("\n" + "=" * 50)
    print("   🤖 CLAUDE CODE LAUNCHER")
    print("=" * 50)
    
    project_path = get_project_path()
    
    # Estrai la lettera del disco se presente (es: D:)
    drive = ""
    if len(project_path) >= 2 and project_path[1] == ':':
        drive = project_path[0:2]
    
    print(f"\n🚀 Avvio Claude nella cartella: {project_path}")
    print("📋 Caricamento lista sessioni recenti...\n")
    
    # Crea il comando batch da eseguire
    # Usa cmd /k per mantenere la finestra aperta
    batch_commands = f'''
@echo off
{drive}
cd "{project_path}"
echo.
echo ========================================
echo   Claude Code - Sessioni Recenti
echo ========================================
echo.
claude --resume
'''
    
    # Crea un file batch temporaneo
    temp_bat = Path(os.environ.get('TEMP', '/tmp')) / 'claude_launch_temp.bat'
    with open(temp_bat, 'w') as f:
        f.write(batch_commands)
    
    # Apri una nuova finestra cmd ed esegui il batch
    if sys.platform == 'win32':
        subprocess.Popen(
            f'start cmd /k "{temp_bat}"',
            shell=True
        )
    else:
        # Per Linux/Mac (anche se stai usando Windows)
        print("Questo script è progettato per Windows.")
        print(f"Comando da eseguire manualmente:")
        print(f"  cd {project_path} && claude --resume")
    
    print("✅ Finestra terminale aperta!")
    print("\nQuesta finestra si chiuderà tra 2 secondi...")
    
    import time
    time.sleep(2)

if __name__ == "__main__":
    main()
