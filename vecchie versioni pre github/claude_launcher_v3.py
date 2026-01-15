"""
Claude Code Launcher - Multi-Project v3
Con supporto Ctrl+V (usa Windows Terminal)
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

def get_claude_projects_dir():
    """Trova la cartella dei progetti Claude"""
    home = Path.home()
    claude_dir = home / ".claude" / "projects"
    return claude_dir

def get_config_path():
    """Percorso file config per salvare i mapping dei percorsi"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    return base_path / "claude_paths_config.json"

def load_path_mappings():
    """Carica i mapping salvati tra nome cartella e percorso reale"""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_path_mapping(folder_name, real_path):
    """Salva un mapping tra nome cartella e percorso reale"""
    mappings = load_path_mappings()
    mappings[folder_name] = real_path
    try:
        with open(get_config_path(), 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2)
    except:
        pass

def decode_project_path(folder_name):
    """
    Decodifica il nome della cartella nel percorso originale.
    Formato: D--downloads-Lux-app-lux-1 → D:\downloads\Lux\app lux 1
    """
    # Prima controlla se abbiamo un mapping salvato
    mappings = load_path_mappings()
    if folder_name in mappings:
        return mappings[folder_name]
    
    # Decodifica euristica
    match = re.match(r'^([A-Za-z])--(.+)$', folder_name)
    if not match:
        return None
    
    drive = match.group(1).upper()
    rest = match.group(2)
    
    # Sostituisci tutti i '-' con '\' come prima approssimazione
    path_attempt = f"{drive}:\\" + rest.replace('-', '\\')
    
    # Verifica se esiste
    if os.path.isdir(path_attempt):
        save_path_mapping(folder_name, path_attempt)
        return path_attempt
    
    # Se non esiste, prova con gli spazi
    parts = rest.split('-')
    
    for i in range(len(parts)):
        if i == 0:
            test_path = f"{drive}:\\" + ' '.join(parts)
        else:
            test_path = f"{drive}:\\" + '\\'.join(parts[:i]) + '\\' + ' '.join(parts[i:])
        
        if os.path.isdir(test_path):
            save_path_mapping(folder_name, test_path)
            return test_path
    
    return f"{drive}:\\" + rest.replace('-', '\\')

def read_jsonl_first_line(filepath):
    """Legge la prima riga di un file JSONL"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line:
                return json.loads(first_line)
    except:
        pass
    return None

def get_session_summary(jsonl_path):
    """Estrae un riassunto dalla sessione (prima riga del JSONL)"""
    data = read_jsonl_first_line(jsonl_path)
    if data:
        if isinstance(data, dict):
            if 'message' in data:
                msg = data['message']
                if isinstance(msg, str):
                    return msg[:50] + "..." if len(msg) > 50 else msg
            if 'content' in data:
                content = data['content']
                if isinstance(content, str):
                    return content[:50] + "..." if len(content) > 50 else content
    return None

def get_project_info(project_dir):
    """Estrae informazioni sul progetto dai file di sessione"""
    info = {
        'sessions': [],
        'last_modified': None,
        'working_directory': None
    }
    
    jsonl_files = [f for f in project_dir.glob("*.jsonl") if f.is_file()]
    
    for jf in jsonl_files:
        session_info = {
            'id': jf.stem,
            'path': jf,
            'modified': datetime.fromtimestamp(jf.stat().st_mtime),
            'size': jf.stat().st_size,
            'summary': get_session_summary(jf)
        }
        info['sessions'].append(session_info)
    
    info['sessions'].sort(key=lambda x: x['modified'], reverse=True)
    
    if info['sessions']:
        info['last_modified'] = info['sessions'][0]['modified']
    
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
            
            if not info['sessions']:
                continue
            
            real_path = decode_project_path(folder.name)
            
            projects.append({
                'folder_name': folder.name,
                'folder_path': folder,
                'real_path': real_path,
                'sessions': info['sessions'],
                'session_count': len(info['sessions']),
                'last_modified': info['last_modified']
            })
    
    projects.sort(key=lambda x: x['last_modified'] or datetime.min, reverse=True)
    
    return projects

def format_size(size_bytes):
    """Formatta dimensione file"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    else:
        return f"{size_bytes // (1024*1024)} MB"

def display_menu(projects):
    """Mostra il menu di selezione"""
    print()
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║       CLAUDE CODE LAUNCHER v3 - Ctrl+V Supportato                 ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print()
    
    if not projects:
        print("❌ Nessun progetto con sessioni trovato!")
        print()
        print(f"   Cartella cercata: {get_claude_projects_dir()}")
        print()
        return None
    
    total_sessions = sum(p['session_count'] for p in projects)
    print(f"📂 Trovati {len(projects)} progetti con {total_sessions} sessioni totali:")
    print("─" * 70)
    print()
    
    for i, proj in enumerate(projects, 1):
        path_display = proj['real_path'] or proj['folder_name']
        sessions = proj['session_count']
        
        if proj['last_modified']:
            date_str = proj['last_modified'].strftime("%d/%m/%Y %H:%M")
        else:
            date_str = "N/A"
        
        max_path_len = 50
        if len(str(path_display)) > max_path_len:
            path_display = "..." + str(path_display)[-(max_path_len-3):]
        
        path_exists = proj['real_path'] and os.path.isdir(proj['real_path'])
        status = "✓" if path_exists else "?"
        
        print(f"  [{i:2d}] {status} {path_display}")
        print(f"       📊 {sessions} sessioni | 🕐 {date_str}")
        print()
    
    print("─" * 70)
    print("  [0]  Esci")
    print("  [N]  Nuova sessione (inserisci percorso)")
    print("─" * 70)
    print()
    
    return input("👉 Scegli progetto: ").strip()

def display_sessions(project):
    """Mostra le sessioni di un progetto"""
    print()
    print(f"📂 Progetto: {project['real_path'] or project['folder_name']}")
    print("─" * 70)
    print()
    
    for i, session in enumerate(project['sessions'], 1):
        date_str = session['modified'].strftime("%d/%m/%Y %H:%M")
        size_str = format_size(session['size'])
        
        print(f"  [{i:2d}] 🕐 {date_str} | 📦 {size_str}")
        if session['summary']:
            print(f"       💬 {session['summary']}")
        else:
            print(f"       🔑 {session['id'][:20]}...")
        print()
    
    print("─" * 70)
    print("  [0]  Torna indietro")
    print("  [A]  Apri ultima sessione (--resume)")
    print("─" * 70)
    print()
    
    return input("👉 Scegli sessione o [A]: ").strip()

def launch_claude(project_path, session_id=None):
    """Lancia Claude nella cartella specificata usando Windows Terminal"""
    if not os.path.isdir(project_path):
        print(f"\n❌ Errore: Il percorso non esiste: {project_path}")
        return False
    
    print()
    print("═" * 70)
    print(f"🚀 Avvio Claude in: {project_path}")
    print(f"   Terminal: Windows Terminal (Ctrl+V abilitato)")
    if session_id:
        print(f"   Sessione: {session_id[:30]}...")
    print("═" * 70)
    print()
    
    # Estrai il disco (Windows)
    drive = ""
    if len(project_path) >= 2 and project_path[1] == ':':
        drive = project_path[0:2]
    
    # Comando Claude
    if session_id:
        claude_cmd = f"claude --resume {session_id}"
    else:
        claude_cmd = "claude --resume"
    
    if sys.platform == 'win32':
        import tempfile
        
        batch_content = f'''@echo off
{drive}
cd "{project_path}"
cls
echo.
echo ══════════════════════════════════════════════════
echo   Claude Code - {os.path.basename(project_path)}
echo   [Ctrl+V abilitato]
echo ══════════════════════════════════════════════════
echo.
{claude_cmd}
'''
        
        # Crea file batch temporaneo
        temp_dir = tempfile.gettempdir()
        batch_path = os.path.join(temp_dir, "claude_launch_temp.bat")
        
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # === FIX: Usa Windows Terminal invece di cmd.exe ===
        # Windows Terminal supporta Ctrl+V nativamente
        subprocess.run(f'wt.exe -d "{project_path}" cmd /k "{batch_path}"', shell=True)
    else:
        print(f"Esegui manualmente: cd \"{project_path}\" && {claude_cmd}")
    
    return True

def ask_for_path(folder_name):
    """Chiede all'utente il percorso e lo salva"""
    print()
    print(f"⚠️  Percorso non trovato automaticamente.")
    print(f"   Nome cartella: {folder_name}")
    print()
    path = input("📂 Inserisci il percorso completo: ").strip().strip('"').strip("'")
    
    if path and os.path.isdir(path):
        save_path_mapping(folder_name, path)
        print(f"✅ Percorso salvato per usi futuri!")
    
    return path

def main():
    os.system('cls' if sys.platform == 'win32' else 'clear')
    
    while True:
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
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(projects):
                proj = projects[idx - 1]
                
                path = proj['real_path']
                
                if not path or not os.path.isdir(path):
                    path = ask_for_path(proj['folder_name'])
                
                if not path:
                    continue
                
                os.system('cls' if sys.platform == 'win32' else 'clear')
                proj['real_path'] = path
                
                session_choice = display_sessions(proj)
                
                if session_choice == '0':
                    os.system('cls' if sys.platform == 'win32' else 'clear')
                    continue
                
                if session_choice.lower() == 'a' or session_choice == '':
                    launch_claude(path)
                    return
                
                try:
                    sess_idx = int(session_choice)
                    if 1 <= sess_idx <= len(proj['sessions']):
                        session = proj['sessions'][sess_idx - 1]
                        launch_claude(path, session['id'])
                        return
                except ValueError:
                    pass
                
            else:
                print("\n❌ Scelta non valida!")
        except ValueError:
            print("\n❌ Inserisci un numero valido!")
        
        input("\nPremi INVIO per continuare...")
        os.system('cls' if sys.platform == 'win32' else 'clear')

if __name__ == "__main__":
    main()
