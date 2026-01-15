"""
Claude Code Launcher v6
- Multi-Project con selezione sessioni
- NUOVO: Scelta tra NUOVA SESSIONE e RIPRENDI SESSIONE
- Windows Terminal
- GUI Screenshot Helper (Ctrl+V)
- FILE UPLOAD Helper (Browse per selezionare file)
- --dangerously-skip-permissions sempre attivo
"""

import os
import sys
import json
import subprocess
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from datetime import datetime
import tempfile

# Per clipboard immagini
try:
    from PIL import Image, ImageTk, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ============================================================
#                    FUNZIONI PROGETTI
# ============================================================

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
    """Decodifica il nome della cartella nel percorso originale."""
    mappings = load_path_mappings()
    if folder_name in mappings:
        return mappings[folder_name]
    
    match = re.match(r'^([A-Za-z])--(.+)$', folder_name)
    if not match:
        return None
    
    drive = match.group(1).upper()
    rest = match.group(2)
    
    path_attempt = f"{drive}:\\" + rest.replace('-', '\\')
    
    if os.path.isdir(path_attempt):
        save_path_mapping(folder_name, path_attempt)
        return path_attempt
    
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
    """Estrae un riassunto dalla sessione"""
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
    """Estrae informazioni sul progetto"""
    info = {
        'sessions': [],
        'last_modified': None,
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

def launch_claude_terminal(project_path, session_id=None, new_session=False):
    """
    Lancia Claude in Windows Terminal
    
    Args:
        project_path: percorso del progetto
        session_id: ID specifico della sessione (opzionale)
        new_session: se True, avvia una NUOVA sessione (senza --resume)
    """
    if not os.path.isdir(project_path):
        return False
    
    drive = ""
    if len(project_path) >= 2 and project_path[1] == ':':
        drive = project_path[0:2]
    
    # Costruisci il comando Claude
    if new_session:
        # NUOVA SESSIONE - senza --resume
        claude_cmd = "claude --dangerously-skip-permissions"
        session_type = "NUOVA SESSIONE"
    elif session_id:
        # Riprendi sessione specifica
        claude_cmd = f"claude --dangerously-skip-permissions --resume {session_id}"
        session_type = f"Sessione: {session_id[:8]}..."
    else:
        # Riprendi ultima sessione (menu selezione)
        claude_cmd = "claude --dangerously-skip-permissions --resume"
        session_type = "RIPRENDI SESSIONE"
    
    if sys.platform == 'win32':
        batch_content = f'''@echo off
{drive}
cd "{project_path}"
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo   Claude Code - {os.path.basename(project_path)}
echo   Modalita: {session_type}
echo   [Click destro per incollare]
echo ══════════════════════════════════════════════════════════════
echo.
{claude_cmd}
'''
        
        temp_dir = tempfile.gettempdir()
        batch_path = os.path.join(temp_dir, "claude_launch_temp.bat")
        
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Usa Windows Terminal
        subprocess.run(f'wt.exe -d "{project_path}" cmd /k "{batch_path}"', shell=True)
    
    return True


# ============================================================
#                    DIALOGO SCELTA SESSIONE
# ============================================================

class SessionChoiceDialog:
    """Dialogo per scegliere tra nuova sessione e riprendi"""
    
    def __init__(self, parent, project_name):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Tipo di sessione")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centra rispetto al parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Contenuto
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        title = ttk.Label(
            frame,
            text=f"📂 {project_name}",
            font=("Segoe UI", 12, "bold")
        )
        title.pack(pady=(0, 5))
        
        subtitle = ttk.Label(
            frame,
            text="Come vuoi avviare Claude Code?",
            font=("Segoe UI", 10),
            foreground="gray"
        )
        subtitle.pack(pady=(0, 20))
        
        # Bottoni
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        btn_new = ttk.Button(
            btn_frame,
            text="🆕 Nuova Sessione",
            command=self.choose_new,
            width=20
        )
        btn_new.pack(side=tk.LEFT, expand=True, padx=(0, 10))
        
        btn_resume = ttk.Button(
            btn_frame,
            text="📂 Riprendi Sessione",
            command=self.choose_resume,
            width=20
        )
        btn_resume.pack(side=tk.LEFT, expand=True)
        
        # Info
        info = ttk.Label(
            frame,
            text="Nuova = conversazione pulita | Riprendi = scegli sessione precedente",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        info.pack(pady=(15, 0))
        
        # Bottone annulla
        btn_cancel = ttk.Button(
            frame,
            text="Annulla",
            command=self.cancel
        )
        btn_cancel.pack(pady=(10, 0))
        
        # Bind Escape
        self.dialog.bind("<Escape>", lambda e: self.cancel())
        
        # Focus
        btn_new.focus_set()
        
    def choose_new(self):
        self.result = "new"
        self.dialog.destroy()
        
    def choose_resume(self):
        self.result = "resume"
        self.dialog.destroy()
        
    def cancel(self):
        self.result = None
        self.dialog.destroy()
        
    def get_result(self):
        self.dialog.wait_window()
        return self.result


# ============================================================
#                    GUI PRINCIPALE
# ============================================================

class ClaudeLauncherGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 Claude Code Launcher v6")
        self.root.geometry("750x850")
        self.root.resizable(True, True)
        
        # Stato
        self.projects = []
        self.selected_project = None
        self.screenshots = []
        self.files = []
        self.temp_dir = Path(tempfile.gettempdir()) / "claude_screenshots"
        self.temp_dir.mkdir(exist_ok=True)
        self.terminal_launched = False
        self.current_project_path = None
        
        self.setup_ui()
        self.load_projects()
        
    def setup_ui(self):
        """Crea l'interfaccia"""
        # Notebook per tab
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Selezione Progetto
        self.tab_projects = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_projects, text="📂 Progetti")
        self.setup_projects_tab()
        
        # Tab 2: Screenshot & File Helper (inizialmente disabilitato)
        self.tab_send = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_send, text="📤 Invia a Claude", state="disabled")
        self.setup_send_tab()
        
    def setup_projects_tab(self):
        """Setup tab selezione progetti"""
        frame = self.tab_projects
        
        # Titolo
        title = ttk.Label(
            frame, 
            text="🚀 Claude Code Launcher",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=(10, 5))
        
        subtitle = ttk.Label(
            frame,
            text="Seleziona un progetto per avviare Claude Code",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        subtitle.pack(pady=(0, 15))
        
        # Lista progetti
        list_frame = ttk.LabelFrame(frame, text="Progetti disponibili", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview per progetti
        columns = ("path", "sessions", "last_modified")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("path", text="📂 Percorso")
        self.tree.heading("sessions", text="📊 Sessioni")
        self.tree.heading("last_modified", text="🕐 Ultima modifica")
        
        self.tree.column("path", width=350)
        self.tree.column("sessions", width=80, anchor="center")
        self.tree.column("last_modified", width=150, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selezione
        self.tree.bind("<<TreeviewSelect>>", self.on_project_select)
        self.tree.bind("<Double-1>", self.on_project_double_click)
        
        # Bottoni principali
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.btn_launch = ttk.Button(
            btn_frame,
            text="🚀 Avvia Claude Code",
            command=self.launch_selected,
            state=tk.DISABLED
        )
        self.btn_launch.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        btn_refresh = ttk.Button(
            btn_frame,
            text="🔄 Aggiorna",
            command=self.load_projects
        )
        btn_refresh.pack(side=tk.LEFT)
        
        btn_new = ttk.Button(
            btn_frame,
            text="📁 Nuovo percorso",
            command=self.new_path_dialog
        )
        btn_new.pack(side=tk.LEFT, padx=(5, 0))
        
        # Status
        self.status_projects = tk.StringVar(value="Caricamento progetti...")
        status = ttk.Label(frame, textvariable=self.status_projects, foreground="gray")
        status.pack(pady=(0, 10))
        
    def setup_send_tab(self):
        """Setup tab per inviare screenshot e file a Claude"""
        frame = self.tab_send
        
        # Info progetto attivo
        self.project_label = ttk.Label(
            frame,
            text="📂 Nessun progetto attivo",
            font=("Segoe UI", 11, "bold")
        )
        self.project_label.pack(pady=(10, 5))
        
        info_label = ttk.Label(
            frame,
            text="Aggiungi screenshot (Ctrl+V) e/o file, poi copia e incolla nel terminale",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # ============ SEZIONE SCREENSHOT ============
        screenshot_frame = ttk.LabelFrame(frame, text="📷 Screenshot (Ctrl+V per incollare)", padding="10")
        screenshot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        # Canvas per thumbnail
        self.canvas = tk.Canvas(screenshot_frame, height=100, bg="#2b2b2b", highlightthickness=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.placeholder_id = self.canvas.create_text(
            300, 50,
            text="Ctrl+V per aggiungere screenshot",
            fill="#666666",
            font=("Segoe UI", 10)
        )
        
        self.thumb_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.thumb_frame, anchor="nw")
        
        btn_clear_screenshots = ttk.Button(
            screenshot_frame,
            text="🗑️ Rimuovi screenshot",
            command=self.clear_screenshots
        )
        btn_clear_screenshots.pack(pady=(5, 0))
        
        # ============ SEZIONE FILE ============
        files_frame = ttk.LabelFrame(frame, text="📁 File (clicca per aggiungere)", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 5))
        
        # Lista file
        self.files_listbox = tk.Listbox(
            files_frame, 
            height=4, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            selectmode=tk.EXTENDED
        )
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Bottoni file
        btn_files_frame = ttk.Frame(files_frame)
        btn_files_frame.pack(fill=tk.X, pady=(5, 0))
        
        btn_add_files = ttk.Button(
            btn_files_frame,
            text="➕ Aggiungi file...",
            command=self.add_files
        )
        btn_add_files.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_remove_file = ttk.Button(
            btn_files_frame,
            text="➖ Rimuovi selezionati",
            command=self.remove_selected_files
        )
        btn_remove_file.pack(side=tk.LEFT, padx=(0, 5))
        
        btn_clear_files = ttk.Button(
            btn_files_frame,
            text="🗑️ Rimuovi tutti",
            command=self.clear_files
        )
        btn_clear_files.pack(side=tk.LEFT)
        
        # ============ SEZIONE MESSAGGIO ============
        msg_frame = ttk.LabelFrame(frame, text="💬 Messaggio per Claude", padding="10")
        msg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 5))
        
        self.msg_text = tk.Text(msg_frame, height=3, wrap=tk.WORD, font=("Segoe UI", 10))
        self.msg_text.pack(fill=tk.BOTH, expand=True)
        self.msg_text.insert("1.0", "Descrivi cosa vuoi che Claude faccia...")
        self.msg_text.bind("<FocusIn>", self.on_msg_focus_in)
        self.msg_text.bind("<FocusOut>", self.on_msg_focus_out)
        self.msg_text.bind("<KeyRelease>", lambda e: self.update_output())
        self.msg_placeholder = True
        
        # ============ OUTPUT ============
        output_frame = ttk.LabelFrame(frame, text="📋 Comando da copiare", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=(5, 5))
        
        self.output_text = tk.Text(
            output_frame,
            height=3,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.output_text.pack(fill=tk.X)
        self.output_text.config(state=tk.DISABLED)
        
        # Bottoni azione
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.btn_copy = ttk.Button(
            btn_frame,
            text="📋 Copia negli Appunti",
            command=self.copy_to_clipboard,
            state=tk.DISABLED
        )
        self.btn_copy.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        btn_back = ttk.Button(
            btn_frame,
            text="◀ Torna ai progetti",
            command=self.back_to_projects
        )
        btn_back.pack(side=tk.RIGHT)
        
        # Status
        self.status_send = tk.StringVar(value="Pronto")
        status = ttk.Label(frame, textvariable=self.status_send, foreground="gray")
        status.pack(pady=(0, 10))
        
        # Binding Ctrl+V globale
        self.root.bind("<Control-v>", self.paste_screenshot)
        self.root.bind("<Control-V>", self.paste_screenshot)
        
    # ============================================================
    #                    FUNZIONI PROGETTI
    # ============================================================
        
    def load_projects(self):
        """Carica lista progetti"""
        # Pulisci lista
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.projects = list_projects()
        
        if not self.projects:
            self.status_projects.set("❌ Nessun progetto trovato")
            return
        
        for proj in self.projects:
            path_display = proj['real_path'] or proj['folder_name']
            if len(str(path_display)) > 45:
                path_display = "..." + str(path_display)[-42:]
            
            date_str = ""
            if proj['last_modified']:
                date_str = proj['last_modified'].strftime("%d/%m/%Y %H:%M")
            
            self.tree.insert("", tk.END, values=(
                path_display,
                proj['session_count'],
                date_str
            ), tags=(proj['folder_name'],))
        
        total = sum(p['session_count'] for p in self.projects)
        self.status_projects.set(f"✅ {len(self.projects)} progetti, {total} sessioni totali")
        
    def on_project_select(self, event):
        """Quando si seleziona un progetto"""
        selection = self.tree.selection()
        if selection:
            self.btn_launch.config(state=tk.NORMAL)
            idx = self.tree.index(selection[0])
            self.selected_project = self.projects[idx]
        else:
            self.btn_launch.config(state=tk.DISABLED)
            self.selected_project = None
            
    def on_project_double_click(self, event):
        """Doppio click = avvia"""
        self.launch_selected()
        
    def launch_selected(self):
        """Avvia il progetto selezionato - MOSTRA DIALOGO SCELTA"""
        if not self.selected_project:
            return
        
        path = self.selected_project['real_path']
        
        if not path or not os.path.isdir(path):
            # Chiedi il percorso
            path = self.ask_path_dialog(self.selected_project['folder_name'])
            if not path:
                return
        
        # NUOVO: Mostra dialogo per scegliere tipo sessione
        project_name = os.path.basename(path)
        dialog = SessionChoiceDialog(self.root, project_name)
        choice = dialog.get_result()
        
        if choice is None:
            # Annullato
            return
        
        self.current_project_path = path
        
        # Lancia terminale con la scelta appropriata
        new_session = (choice == "new")
        success = launch_claude_terminal(path, new_session=new_session)
        
        if success:
            self.terminal_launched = True
            
            # Abilita tab send
            self.notebook.tab(1, state="normal")
            self.notebook.select(1)
            
            # Aggiorna label
            mode = "🆕 Nuova" if new_session else "📂 Riprendi"
            self.project_label.config(text=f"📂 {project_name} ({mode})")
            self.status_send.set("✅ Terminale avviato! Aggiungi screenshot/file e copia")
        else:
            messagebox.showerror("Errore", f"Impossibile avviare Claude in:\n{path}")
            
    def ask_path_dialog(self, folder_name):
        """Dialog per chiedere il percorso"""
        path = simpledialog.askstring(
            "Percorso mancante",
            f"Inserisci il percorso per:\n{folder_name}",
            parent=self.root
        )
        if path and os.path.isdir(path):
            save_path_mapping(folder_name, path)
            return path
        return None
        
    def new_path_dialog(self):
        """Dialog per nuovo percorso - con scelta sessione"""
        path = simpledialog.askstring(
            "Nuovo progetto",
            "Inserisci il percorso del progetto:",
            parent=self.root
        )
        if path and os.path.isdir(path):
            # Mostra dialogo scelta sessione
            project_name = os.path.basename(path)
            dialog = SessionChoiceDialog(self.root, project_name)
            choice = dialog.get_result()
            
            if choice is None:
                return
            
            self.current_project_path = path
            new_session = (choice == "new")
            success = launch_claude_terminal(path, new_session=new_session)
            
            if success:
                self.terminal_launched = True
                self.notebook.tab(1, state="normal")
                self.notebook.select(1)
                mode = "🆕 Nuova" if new_session else "📂 Riprendi"
                self.project_label.config(text=f"📂 {project_name} ({mode})")
        elif path:
            messagebox.showerror("Errore", f"Percorso non valido:\n{path}")
            
    def back_to_projects(self):
        """Torna al tab progetti"""
        self.notebook.select(0)
        
    # ============================================================
    #                    SCREENSHOT HELPER
    # ============================================================
    
    def paste_screenshot(self, event=None):
        """Incolla screenshot dalla clipboard"""
        # Solo se siamo nel tab send
        if self.notebook.index(self.notebook.select()) != 1:
            return
            
        if not PIL_AVAILABLE:
            messagebox.showerror(
                "Errore",
                "Pillow non installato!\n\nEsegui: pip install Pillow"
            )
            return
        
        try:
            img = ImageGrab.grabclipboard()
            
            if img is None:
                self.status_send.set("⚠️ Nessuna immagine nella clipboard")
                return
                
            if not isinstance(img, Image.Image):
                if isinstance(img, list) and len(img) > 0:
                    try:
                        img = Image.open(img[0])
                    except:
                        self.status_send.set("⚠️ Clipboard contiene file, non immagine")
                        return
                else:
                    self.status_send.set("⚠️ Clipboard non contiene un'immagine")
                    return
            
            # Salva immagine
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_{len(self.screenshots)+1}.png"
            filepath = self.temp_dir / filename
            
            img.save(filepath, "PNG")
            
            # Crea thumbnail
            thumb_size = (80, 60)
            thumb = img.copy()
            thumb.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            thumb_tk = ImageTk.PhotoImage(thumb)
            
            self.screenshots.append({
                'path': str(filepath),
                'thumbnail': thumb_tk,
            })
            
            self.update_thumbnails()
            self.update_output()
            self.status_send.set(f"✅ Screenshot aggiunto: {filename}")
            
        except Exception as e:
            self.status_send.set(f"❌ Errore: {str(e)}")
            
    def update_thumbnails(self):
        """Aggiorna visualizzazione thumbnail"""
        if self.placeholder_id:
            self.canvas.delete(self.placeholder_id)
            self.placeholder_id = None
        
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
            
        if not self.screenshots:
            self.placeholder_id = self.canvas.create_text(
                300, 50,
                text="Ctrl+V per aggiungere screenshot",
                fill="#666666",
                font=("Segoe UI", 10)
            )
            return
        
        for i, ss in enumerate(self.screenshots):
            frame = ttk.Frame(self.thumb_frame)
            frame.pack(side=tk.LEFT, padx=5, pady=5)
            
            label = ttk.Label(frame, image=ss['thumbnail'])
            label.pack()
            
            btn = ttk.Button(
                frame,
                text="✕",
                width=3,
                command=lambda idx=i: self.remove_screenshot(idx)
            )
            btn.pack(pady=(2, 0))
            
    def remove_screenshot(self, index):
        """Rimuove uno screenshot"""
        if 0 <= index < len(self.screenshots):
            try:
                os.remove(self.screenshots[index]['path'])
            except:
                pass
            
            del self.screenshots[index]
            self.update_thumbnails()
            self.update_output()
            
    def clear_screenshots(self):
        """Rimuove tutti gli screenshot"""
        for ss in self.screenshots:
            try:
                os.remove(ss['path'])
            except:
                pass
        
        self.screenshots = []
        self.update_thumbnails()
        self.update_output()
        self.status_send.set("Screenshot rimossi")
    
    # ============================================================
    #                    FILE HELPER
    # ============================================================
    
    def add_files(self):
        """Apre dialogo per selezionare file"""
        filepaths = filedialog.askopenfilenames(
            title="Seleziona file da condividere con Claude",
            filetypes=[
                ("Tutti i file", "*.*"),
                ("Immagini", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("Documenti", "*.pdf *.docx *.doc *.txt *.md"),
                ("Codice", "*.py *.js *.ts *.html *.css *.json *.yaml *.yml"),
            ]
        )
        
        if filepaths:
            for fp in filepaths:
                if fp not in self.files:
                    self.files.append(fp)
            
            self.update_files_listbox()
            self.update_output()
            self.status_send.set(f"✅ Aggiunti {len(filepaths)} file")
    
    def update_files_listbox(self):
        """Aggiorna la listbox dei file"""
        self.files_listbox.delete(0, tk.END)
        
        for fp in self.files:
            # Mostra solo nome file + estensione per leggibilità
            display = os.path.basename(fp)
            self.files_listbox.insert(tk.END, f"📄 {display}")
    
    def remove_selected_files(self):
        """Rimuove i file selezionati dalla lista"""
        selection = self.files_listbox.curselection()
        
        if not selection:
            self.status_send.set("⚠️ Seleziona i file da rimuovere")
            return
        
        # Rimuovi in ordine inverso per non sballare gli indici
        for idx in reversed(selection):
            del self.files[idx]
        
        self.update_files_listbox()
        self.update_output()
        self.status_send.set("File rimossi")
    
    def clear_files(self):
        """Rimuove tutti i file"""
        self.files = []
        self.update_files_listbox()
        self.update_output()
        self.status_send.set("Tutti i file rimossi")
        
    # ============================================================
    #                    OUTPUT & CLIPBOARD
    # ============================================================
        
    def on_msg_focus_in(self, event):
        """Rimuovi placeholder"""
        if self.msg_placeholder:
            self.msg_text.delete("1.0", tk.END)
            self.msg_placeholder = False
            
    def on_msg_focus_out(self, event):
        """Ripristina placeholder se vuoto"""
        if not self.msg_text.get("1.0", tk.END).strip():
            self.msg_text.insert("1.0", "Descrivi cosa vuoi che Claude faccia...")
            self.msg_placeholder = True
            
    def update_output(self):
        """Aggiorna comando output con screenshot + file + messaggio"""
        parts = []
        
        # Prima gli screenshot
        for ss in self.screenshots:
            parts.append(ss['path'])
        
        # Poi i file
        for fp in self.files:
            parts.append(fp)
        
        # Infine il messaggio
        msg = self.msg_text.get("1.0", tk.END).strip()
        if msg and not self.msg_placeholder:
            parts.append(msg)
        
        if parts:
            output = " ".join(parts)
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", output)
            self.output_text.config(state=tk.DISABLED)
            self.btn_copy.config(state=tk.NORMAL)
        else:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.config(state=tk.DISABLED)
            self.btn_copy.config(state=tk.DISABLED)
            
    def copy_to_clipboard(self):
        """Copia negli appunti"""
        output = self.output_text.get("1.0", tk.END).strip()
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_send.set("✅ Copiato! Usa CLICK DESTRO nel terminale per incollare")
            
    def run(self):
        """Avvia l'applicazione"""
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "Dipendenza mancante",
                "Pillow non installato.\n\n"
                "La funzione screenshot non sarà disponibile.\n\n"
                "Installa con: pip install Pillow"
            )
        
        self.root.mainloop()


def main():
    app = ClaudeLauncherGUI()
    app.run()


if __name__ == "__main__":
    main()
