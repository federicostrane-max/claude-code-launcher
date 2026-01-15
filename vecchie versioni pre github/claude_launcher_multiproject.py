"""
Claude Code Launcher - Multi-Project
Scansiona tutti i progetti con sessioni e permette di scegliere quale aprire
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

def get_claude_projects_dir():
    """Trova la cartella dei progetti Claude"""
    home = Path.home()
    claude_dir = home / ".claude" / "projects"
    return claude_dir

def decode_project_path(folder_name):
    """
    Decodifica il nome della cartella nel percorso originale.
    Claude Code usa un encoding dove:
    - La prima lettera è il disco (su Windows)
    - I separatori sono codificati
    """
    # Il formato sembra essere: lettera-resto-del-percorso
    # dove i backslash diventano trattini
    
    if len(folder_name) < 2:
        return None
    
    # Prima lettera = disco
    drive = folder_name[0].upper()
    
    # Il resto dopo "x-" 
    if len(folder_name) > 2 and folder_name[1] == '-':
        rest = folder_name[2:]
        # Sostituisci i trattini con backslash
        # ATTENZIONE: questo non funziona se i nomi cartella hanno trattini
        path = f"{drive}:\\" + rest.replace('-', '\\')
        return path
    
    return None

def get_project_info(project_dir):
    """Estrae informazioni sul progetto dai file di sessione"""
    info = {
        'sessions': 0,
        'last_modified': None,
        'working_directory': None
    }
    
    # Conta i file JSON (sessioni)
    json_files = list(project_dir.glob("*.json"))
    info['sessions'] = len(json_files)
    
    # Trova l'ultimo modificato
    if json_files:
        latest = max(json_files, key=lambda f: f.stat().st_mtime)
        info['last_modified'] = datetime.fromtimestamp(latest.stat().st_mtime)
        
        # Prova a leggere il working directory dal file
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Cerca in vari posti possibili
                    if 'workingDirectory' in data:
                        info['working_directory'] = data['workingDirectory']
                    elif 'cwd' in data:
                        info['working_directory'] = data['cwd']
                    elif 'path' in data:
                        info['working_directory'] = data['path']
        except:
            pass
    
    return info

def list_projects():
    """Lista tutti i progetti con sessioni"""
    projects_dir = get_claude_projects_dir()
    
    if not projects_dir.exists():
        return []
    
    projects = []
    
    for folder in projects_dir.iterdir():
        if folder.is_dir():
            info = get_project_info(folder)
            
            # Determina il percorso reale
            real_path = info.get('working_directory')
            if not real_path:
                real_path = decode_project_path(folder.name)
            
            projects.append({
                'folder_name': folder.name,
                'folder_path': folder,
                'real_path': real_path,
                'sessions': info['sessions'],
                'last_modified': info['last_modified']
            })
    
    # Ordina per ultima modifica (più recenti prima)
    projects.sort(key=lambda x: x['last_modified'] or datetime.min, reverse=True)
    
    return projects

def display_menu(projects):
    """Mostra il menu di selezione"""
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║           CLAUDE CODE LAUNCHER - Multi-Project                   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    if not projects:
        print("❌ Nessun progetto con sessioni trovato!")
        print()
        print(f"   Cartella cercata: {get_claude_projects_dir()}")
        print()
        return None
    
    print(f"📁 Trovati {len(projects)} progetti con sessioni:")
    print("─" * 70)
    print()
    
    for i, proj in enumerate(projects, 1):
        path_display = proj['real_path'] or proj['folder_name']
        sessions = proj['sessions']
        
        # Formatta la data
        if proj['last_modified']:
            date_str = proj['last_modified'].strftime("%d/%m/%Y %H:%M")
        else:
            date_str = "N/A"
        
        # Tronca il percorso se troppo lungo
        max_path_len = 45
        if len(str(path_display)) > max_path_len:
            path_display = "..." + str(path_display)[-(max_path_len-3):]
        
        print(f"  [{i:2d}] {path_display}")
        print(f"       📊 {sessions} sessioni | 🕐 {date_str}")
        print()
    
    print("─" * 70)
    print("  [0]  Esci")
    print("  [N]  Nuova sessione (inserisci percorso)")
    print("─" * 70)
    print()
    
    return input("👉 Scegli progetto: ").strip()

def launch_claude(project_path):
    """Lancia Claude nella cartella specificata"""
    if not os.path.isdir(project_path):
        print(f"\n❌ Errore: Il percorso non esiste: {project_path}")
        return False
    
    print()
    print("═" * 70)
    print(f"🚀 Avvio Claude in: {project_path}")
    print("═" * 70)
    print()
    
    # Estrai il disco (Windows)
    drive = ""
    if len(project_path) >= 2 and project_path[1] == ':':
        drive = project_path[0:2]
    
    # Crea il comando
    if sys.platform == 'win32':
        # Comando per Windows
        cmd = f'start cmd /k "{drive} && cd \\"{project_path}\\" && cls && echo. && echo ══════════════════════════════════════════════════ && echo   Claude Code - {os.path.basename(project_path)} && echo ══════════════════════════════════════════════════ && echo. && claude --resume"'
        subprocess.run(cmd, shell=True)
    else:
        # Per Linux/Mac
        print(f"Esegui manualmente: cd \"{project_path}\" && claude --resume")
    
    return True

def main():
    os.system('cls' if sys.platform == 'win32' else 'clear')
    
    projects = list_projects()
    choice = display_menu(projects)
    
    if choice is None:
        input("\nPremi INVIO per uscire...")
        return
    
    if choice == '0' or choice.lower() == 'q':
        print("\n👋 Arrivederci!")
        return
    
    if choice.lower() == 'n':
        print()
        new_path = input("📂 Inserisci il percorso del progetto: ").strip().strip('"').strip("'")
        if new_path:
            launch_claude(new_path)
        return
    
    # Selezione numerica
    try:
        idx = int(choice)
        if 1 <= idx <= len(projects):
            proj = projects[idx - 1]
            
            # Usa il percorso reale se disponibile, altrimenti chiedi
            path = proj['real_path']
            
            if not path or not os.path.isdir(path):
                print()
                print(f"⚠️  Percorso non trovato automaticamente.")
                print(f"   Nome cartella: {proj['folder_name']}")
                print()
                path = input("📂 Inserisci il percorso completo: ").strip().strip('"').strip("'")
            
            if path:
                launch_claude(path)
        else:
            print("\n❌ Scelta non valida!")
    except ValueError:
        print("\n❌ Inserisci un numero valido!")
    
    print()
    input("Premi INVIO per chiudere...")

if __name__ == "__main__":
    main()
