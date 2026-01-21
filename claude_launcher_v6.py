"""
Claude Code Launcher v8
- Multi-Project con selezione sessioni
- Scelta tra NUOVA SESSIONE e RIPRENDI SESSIONE
- Windows Terminal
- GUI Screenshot Helper (Ctrl+V)
- FILE UPLOAD Helper (Browse per selezionare file)
- --dangerously-skip-permissions sempre attivo
- USA RALPH - Modalità autonoma basata su Ralph Wiggum
- NUOVO: Multi-Tab support - Apri più progetti nella stessa finestra Windows Terminal
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
#                    RALPH WIGGUM - AUTONOMOUS MODE
# ============================================================

RALPH_PROMPT_BUILD_TEMPLATE = """0a. Study `specs/*` with up to 500 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md.
0c. For reference, the application source code is in `{src_dir}`.

1. Your task is to implement functionality per the specifications using parallel subagents. Follow @IMPLEMENTATION_PLAN.md and choose the most important item to address. Before making changes, search the codebase (don't assume not implemented) using Sonnet subagents. You may use up to 500 parallel Sonnet subagents for searches/reads and only 1 Sonnet subagent for build/tests. Use Opus subagents when complex reasoning is needed (debugging, architectural decisions).
2. After implementing functionality or resolving problems, run the tests for that unit of code that was improved. If functionality is missing then it's your job to add it as per the application specifications. Ultrathink.
3. When you discover issues, immediately update @IMPLEMENTATION_PLAN.md with your findings using a subagent. When resolved, update and remove the item.
4. When the tests pass, update @IMPLEMENTATION_PLAN.md, then `git add -A` then `git commit` with a message describing the changes. After the commit, `git push`.

99999. Important: When authoring documentation, capture the why — tests and implementation importance.
999999. Important: Single sources of truth, no migrations/adapters. If tests unrelated to your work fail, resolve them as part of the increment.
9999999. As soon as there are no build or test errors create a git tag. If there are no git tags start at 0.0.0 and increment patch by 1 for example 0.0.1 if 0.0.0 does not exist.
99999999. You may add extra logging if required to debug issues.
999999999. Keep @IMPLEMENTATION_PLAN.md current with learnings using a subagent — future work depends on this to avoid duplicating efforts. Update especially after finishing your turn.
9999999999. When you learn something new about how to run the application, update @AGENTS.md using a subagent but keep it brief.
99999999999. For any bugs you notice, resolve them or document them in @IMPLEMENTATION_PLAN.md using a subagent even if it is unrelated to the current piece of work.
999999999999. Implement functionality completely. Placeholders and stubs waste efforts and time redoing the same work.
9999999999999. When @IMPLEMENTATION_PLAN.md becomes large periodically clean out the items that are completed from the file using a subagent.
99999999999999. If you find inconsistencies in the specs/* then use an Opus 4.5 subagent with 'ultrathink' requested to update the specs.
999999999999999. IMPORTANT: Keep @AGENTS.md operational only — status updates and progress notes belong in `IMPLEMENTATION_PLAN.md`.
"""

RALPH_PROMPT_PLAN_TEMPLATE = """0a. Study `specs/*` with up to 250 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md (if present) to understand the plan so far.
0c. Study `{src_dir}` with up to 250 parallel Sonnet subagents to understand shared utilities & components.
0d. For reference, the application source code is in `{src_dir}`.

1. Study @IMPLEMENTATION_PLAN.md (if present; it may be incorrect) and use up to 500 Sonnet subagents to study existing source code in `{src_dir}` and compare it against `specs/*`. Use an Opus subagent to analyze findings, prioritize tasks, and create/update @IMPLEMENTATION_PLAN.md as a bullet point list sorted in priority of items yet to be implemented. Ultrathink. Consider searching for TODO, minimal implementations, placeholders, skipped/flaky tests, and inconsistent patterns. Study @IMPLEMENTATION_PLAN.md to determine starting point for research and keep it up to date with items considered complete/incomplete using subagents.

IMPORTANT: Plan only. Do NOT implement anything. Do NOT assume functionality is missing; confirm with code search first. Treat `{src_dir}` as the project's standard library for shared utilities and components. Prefer consolidated, idiomatic implementations there over ad-hoc copies.

ULTIMATE GOAL: {goal}. Consider missing elements and plan accordingly. If an element is missing, search first to confirm it doesn't exist, then if needed author the specification at specs/FILENAME.md. If you create a new element then document the plan to implement it in @IMPLEMENTATION_PLAN.md using a subagent.
"""

RALPH_AGENTS_TEMPLATE = """## Build & Run

Project: {project_name}
Source: {src_dir}

## Validation

Run these after implementing to get immediate feedback:

- Tests: `{test_cmd}`
- Build: `{build_cmd}`

## Operational Notes

- This is a Ralph-automated session
- Goal: {goal}
"""


def create_ralph_files(project_path, goal, src_dir=".", test_cmd="npm test", build_cmd="npm run build"):
    """Crea i file necessari per Ralph nel progetto"""
    project_name = os.path.basename(project_path)

    # Crea cartella specs se non esiste
    specs_dir = os.path.join(project_path, "specs")
    os.makedirs(specs_dir, exist_ok=True)

    # Crea spec iniziale con il goal dell'utente
    spec_content = f"""# User Goal Specification

## Objective
{goal}

## Requirements
- Implement the functionality as described above
- Follow existing code patterns and conventions
- Add appropriate tests
- Update documentation as needed

## Acceptance Criteria
- The implementation should fully address the objective
- All tests should pass
- Code should be clean and maintainable
"""

    spec_path = os.path.join(specs_dir, "user-goal.md")
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    # Crea PROMPT_plan.md
    prompt_plan = RALPH_PROMPT_PLAN_TEMPLATE.format(
        src_dir=src_dir,
        goal=goal
    )
    with open(os.path.join(project_path, "PROMPT_plan.md"), 'w', encoding='utf-8') as f:
        f.write(prompt_plan)

    # Crea PROMPT_build.md
    prompt_build = RALPH_PROMPT_BUILD_TEMPLATE.format(src_dir=src_dir)
    with open(os.path.join(project_path, "PROMPT_build.md"), 'w', encoding='utf-8') as f:
        f.write(prompt_build)

    # Crea AGENTS.md
    agents = RALPH_AGENTS_TEMPLATE.format(
        project_name=project_name,
        src_dir=src_dir,
        test_cmd=test_cmd,
        build_cmd=build_cmd,
        goal=goal
    )
    with open(os.path.join(project_path, "AGENTS.md"), 'w', encoding='utf-8') as f:
        f.write(agents)

    return True


def launch_ralph_loop(project_path, mode="plan", max_iterations=5, model="sonnet"):
    """
    Lancia il loop Ralph in Windows Terminal

    Args:
        project_path: percorso del progetto
        mode: 'plan' o 'build'
        max_iterations: numero massimo di iterazioni
        model: 'opus' o 'sonnet'
    """
    if not os.path.isdir(project_path):
        return False

    drive = ""
    if len(project_path) >= 2 and project_path[1] == ':':
        drive = project_path[0:2]

    prompt_file = f"PROMPT_{mode}.md"

    # Script batch per il loop Ralph
    batch_content = f'''@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
{drive}
cd "{project_path}"
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo   RALPH WIGGUM - Autonomous Mode
echo   Project: {os.path.basename(project_path)}
echo   Mode: {mode.upper()}
echo   Model: {model}
echo   Max Iterations: {max_iterations}
echo ══════════════════════════════════════════════════════════════
echo.
echo   Press Ctrl+C to stop the loop at any time
echo.

set ITERATION=0

:loop
if !ITERATION! GEQ {max_iterations} (
    echo.
    echo ══════════════════════════════════════════════════════════════
    echo   Reached max iterations: {max_iterations}
    echo   Ralph loop completed!
    echo ══════════════════════════════════════════════════════════════
    pause
    exit /b 0
)

set /a ITERATION+=1
echo.
echo ======================== LOOP !ITERATION! / {max_iterations} ========================
echo.

type "{prompt_file}" | claude -p --dangerously-skip-permissions --model {model}

if errorlevel 1 (
    echo.
    echo [WARNING] Claude exited with error. Continuing to next iteration...
)

echo.
echo Loop !ITERATION! completed. Starting next iteration...
timeout /t 2 /nobreak >nul

goto loop
'''

    temp_dir = tempfile.gettempdir()
    batch_path = os.path.join(temp_dir, "ralph_loop_temp.bat")

    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)

    # Lancia in Windows Terminal
    subprocess.run(f'wt.exe -d "{project_path}" cmd /k "{batch_path}"', shell=True)

    return True


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

def launch_claude_terminal(project_path, session_id=None, new_session=False, as_new_tab=False):
    """
    Lancia Claude in Windows Terminal

    Args:
        project_path: percorso del progetto
        session_id: ID specifico della sessione (opzionale)
        new_session: se True, avvia una NUOVA sessione (senza --resume)
        as_new_tab: se True, apre come nuovo TAB nella finestra WT esistente
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

    project_name = os.path.basename(project_path)

    if sys.platform == 'win32':
        batch_content = f'''@echo off
chcp 65001 >nul
{drive}
cd "{project_path}"
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo   Claude Code - {project_name}
echo   Modalita: {session_type}
echo   [Click destro per incollare]
echo ══════════════════════════════════════════════════════════════
echo.
{claude_cmd}
'''

        temp_dir = tempfile.gettempdir()
        # Usa nome unico per batch file per evitare conflitti con tab multipli
        batch_filename = f"claude_launch_{project_name.replace(' ', '_')}_{id(project_path)}.bat"
        batch_path = os.path.join(temp_dir, batch_filename)

        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)

        if as_new_tab:
            # Apri come NUOVO TAB nella finestra Windows Terminal esistente
            # -w 0 = usa la finestra WT più recente (o creane una se non esiste)
            # new-tab = crea un nuovo tab
            # --title = titolo del tab
            subprocess.run(
                f'wt.exe -w 0 new-tab --title "{project_name}" -d "{project_path}" cmd /k "{batch_path}"',
                shell=True
            )
        else:
            # Comportamento originale: apri nuova finestra
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
#                    DIALOGO CONFIGURAZIONE RALPH
# ============================================================

class RalphConfigDialog:
    """Dialogo per configurare e avviare Ralph"""

    def __init__(self, parent, project_path, initial_goal=""):
        self.result = None
        self.project_path = project_path

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Ralph Wiggum - Configurazione")
        self.dialog.geometry("550x520")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Centra rispetto al parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 520) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # Contenuto
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Titolo
        title = ttk.Label(
            frame,
            text="🤖 Ralph Wiggum - Autonomous Mode",
            font=("Segoe UI", 14, "bold")
        )
        title.pack(pady=(0, 5))

        subtitle = ttk.Label(
            frame,
            text="Claude lavorerà in autonomia sul tuo obiettivo",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        subtitle.pack(pady=(0, 15))

        # Goal
        goal_frame = ttk.LabelFrame(frame, text="🎯 Obiettivo (cosa vuoi che faccia)", padding="10")
        goal_frame.pack(fill=tk.X, pady=(0, 10))

        self.goal_text = tk.Text(goal_frame, height=4, wrap=tk.WORD, font=("Segoe UI", 10))
        self.goal_text.pack(fill=tk.X)
        if initial_goal:
            self.goal_text.insert("1.0", initial_goal)

        # Configurazione
        config_frame = ttk.LabelFrame(frame, text="⚙️ Configurazione", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Source directory
        src_row = ttk.Frame(config_frame)
        src_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(src_row, text="Directory sorgente:", width=18).pack(side=tk.LEFT)
        self.src_var = tk.StringVar(value=".")
        ttk.Entry(src_row, textvariable=self.src_var, width=30).pack(side=tk.LEFT, padx=(5, 0))

        # Test command
        test_row = ttk.Frame(config_frame)
        test_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(test_row, text="Comando test:", width=18).pack(side=tk.LEFT)
        self.test_var = tk.StringVar(value="npm test")
        ttk.Entry(test_row, textvariable=self.test_var, width=30).pack(side=tk.LEFT, padx=(5, 0))

        # Build command
        build_row = ttk.Frame(config_frame)
        build_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(build_row, text="Comando build:", width=18).pack(side=tk.LEFT)
        self.build_var = tk.StringVar(value="npm run build")
        ttk.Entry(build_row, textvariable=self.build_var, width=30).pack(side=tk.LEFT, padx=(5, 0))

        # Model selection
        model_row = ttk.Frame(config_frame)
        model_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(model_row, text="Modello:", width=18).pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="sonnet")
        model_combo = ttk.Combobox(model_row, textvariable=self.model_var, values=["sonnet", "opus"], state="readonly", width=15)
        model_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Max iterations
        iter_row = ttk.Frame(config_frame)
        iter_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(iter_row, text="Max iterazioni:", width=18).pack(side=tk.LEFT)
        self.iter_var = tk.IntVar(value=5)
        iter_spin = ttk.Spinbox(iter_row, from_=1, to=50, textvariable=self.iter_var, width=10)
        iter_spin.pack(side=tk.LEFT, padx=(5, 0))

        # Mode selection
        mode_frame = ttk.LabelFrame(frame, text="🔄 Modalità di avvio", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.mode_var = tk.StringVar(value="plan")

        plan_radio = ttk.Radiobutton(
            mode_frame,
            text="📋 PLAN - Prima crea il piano di implementazione",
            variable=self.mode_var,
            value="plan"
        )
        plan_radio.pack(anchor=tk.W)

        build_radio = ttk.Radiobutton(
            mode_frame,
            text="🔨 BUILD - Vai diretto all'implementazione",
            variable=self.mode_var,
            value="build"
        )
        build_radio.pack(anchor=tk.W)

        # Info box
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_text = """⚠️ ATTENZIONE: Ralph lavorerà in autonomia!
• Creerà/modificherà file nel progetto
• Farà commit automatici su git
• Premi Ctrl+C nel terminale per fermare"""

        info_label = ttk.Label(
            info_frame,
            text=info_text,
            font=("Segoe UI", 9),
            foreground="#cc7700",
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)

        # Bottoni
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        btn_cancel = ttk.Button(
            btn_frame,
            text="Annulla",
            command=self.cancel
        )
        btn_cancel.pack(side=tk.LEFT)

        btn_start = ttk.Button(
            btn_frame,
            text="🚀 Avvia Ralph!",
            command=self.start_ralph
        )
        btn_start.pack(side=tk.RIGHT)

        # Bind Escape
        self.dialog.bind("<Escape>", lambda e: self.cancel())

    def start_ralph(self):
        """Avvia Ralph con la configurazione"""
        goal = self.goal_text.get("1.0", tk.END).strip()

        if not goal:
            messagebox.showwarning("Obiettivo mancante", "Inserisci un obiettivo per Ralph!", parent=self.dialog)
            return

        self.result = {
            'goal': goal,
            'src_dir': self.src_var.get(),
            'test_cmd': self.test_var.get(),
            'build_cmd': self.build_var.get(),
            'model': self.model_var.get(),
            'max_iterations': self.iter_var.get(),
            'mode': self.mode_var.get()
        }
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
        self.root.title("🚀 Claude Code Launcher v8")
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

        # Bottone per aggiungere come nuovo TAB
        self.btn_add_tab = ttk.Button(
            btn_frame,
            text="➕ Nuovo Tab",
            command=self.add_as_new_tab,
            state=tk.DISABLED
        )
        self.btn_add_tab.pack(side=tk.LEFT, padx=(0, 5))

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

        # Frame per Text + Scrollbar
        msg_inner_frame = ttk.Frame(msg_frame)
        msg_inner_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar verticale per il campo messaggio
        msg_scrollbar = ttk.Scrollbar(msg_inner_frame, orient=tk.VERTICAL)
        msg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text widget con altezza minima 3 ma espandibile
        self.msg_text = tk.Text(
            msg_inner_frame,
            height=3,  # Altezza minima
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            yscrollcommand=msg_scrollbar.set
        )
        self.msg_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        msg_scrollbar.config(command=self.msg_text.yview)

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

        # NUOVO: Bottone USA RALPH
        self.btn_ralph = ttk.Button(
            btn_frame,
            text="🤖 USA RALPH",
            command=self.launch_ralph_mode,
            state=tk.DISABLED
        )
        self.btn_ralph.pack(side=tk.LEFT, padx=(0, 5))

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
            # Abilita "Nuovo Tab" solo se c'è già un terminale aperto
            if self.terminal_launched:
                self.btn_add_tab.config(state=tk.NORMAL)
            else:
                self.btn_add_tab.config(state=tk.DISABLED)
            idx = self.tree.index(selection[0])
            self.selected_project = self.projects[idx]
        else:
            self.btn_launch.config(state=tk.DISABLED)
            self.btn_add_tab.config(state=tk.DISABLED)
            self.selected_project = None

    def on_project_double_click(self, event):
        """Doppio click = avvia"""
        self.launch_selected()

    def add_as_new_tab(self):
        """Apre il progetto selezionato come NUOVO TAB in Windows Terminal esistente"""
        if not self.selected_project:
            return

        if not self.terminal_launched:
            messagebox.showinfo(
                "Info",
                "Prima avvia un progetto con '🚀 Avvia Claude Code',\n"
                "poi potrai aggiungere altri progetti come tab."
            )
            return

        path = self.selected_project['real_path']

        if not path or not os.path.isdir(path):
            path = self.ask_path_dialog(self.selected_project['folder_name'])
            if not path:
                return

        # Mostra dialogo per scegliere tipo sessione
        project_name = os.path.basename(path)
        dialog = SessionChoiceDialog(self.root, project_name)
        choice = dialog.get_result()

        if choice is None:
            return

        # Lancia come NUOVO TAB
        new_session = (choice == "new")
        success = launch_claude_terminal(path, new_session=new_session, as_new_tab=True)

        if success:
            mode = "🆕 Nuova" if new_session else "📂 Riprendi"
            self.status_projects.set(f"✅ Tab aggiunto: {project_name} ({mode})")
        else:
            messagebox.showerror("Errore", f"Impossibile aggiungere tab per:\n{path}")
        
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

            # Abilita bottone Ralph
            self.btn_ralph.config(state=tk.NORMAL)

            # Abilita bottone "Nuovo Tab" per aggiungere altri progetti
            self.btn_add_tab.config(state=tk.NORMAL)
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
                self.btn_ralph.config(state=tk.NORMAL)
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
            self.btn_ralph.config(state=tk.NORMAL)
        else:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.config(state=tk.DISABLED)
            self.btn_copy.config(state=tk.DISABLED)
            # Ralph sempre abilitato se c'è un progetto attivo
            if self.current_project_path:
                self.btn_ralph.config(state=tk.NORMAL)

    def copy_to_clipboard(self):
        """Copia negli appunti"""
        output = self.output_text.get("1.0", tk.END).strip()
        if output:
            self.root.clipboard_clear()
            self.root.clipboard_append(output)
            self.status_send.set("✅ Copiato! Usa CLICK DESTRO nel terminale per incollare")

    def launch_ralph_mode(self):
        """Avvia Ralph Wiggum - modalità autonoma"""
        if not self.current_project_path:
            messagebox.showerror("Errore", "Nessun progetto selezionato!")
            return

        # Prendi il messaggio come goal iniziale
        initial_goal = ""
        msg = self.msg_text.get("1.0", tk.END).strip()
        if msg and not self.msg_placeholder:
            initial_goal = msg

        # Mostra dialog di configurazione Ralph
        dialog = RalphConfigDialog(self.root, self.current_project_path, initial_goal)
        config = dialog.get_result()

        if config is None:
            return

        # Crea i file Ralph
        self.status_send.set("🔧 Creazione file Ralph...")
        self.root.update()

        try:
            create_ralph_files(
                self.current_project_path,
                goal=config['goal'],
                src_dir=config['src_dir'],
                test_cmd=config['test_cmd'],
                build_cmd=config['build_cmd']
            )

            # Avvia il loop Ralph
            self.status_send.set("🚀 Avvio Ralph loop...")
            self.root.update()

            success = launch_ralph_loop(
                self.current_project_path,
                mode=config['mode'],
                max_iterations=config['max_iterations'],
                model=config['model']
            )

            if success:
                self.status_send.set(f"✅ Ralph avviato! Mode: {config['mode'].upper()}, Iterations: {config['max_iterations']}")
                messagebox.showinfo(
                    "Ralph Avviato",
                    f"Ralph è in esecuzione!\n\n"
                    f"Modalità: {config['mode'].upper()}\n"
                    f"Modello: {config['model']}\n"
                    f"Max iterazioni: {config['max_iterations']}\n\n"
                    f"Controlla il terminale per vedere il progresso.\n"
                    f"Premi Ctrl+C nel terminale per fermare.",
                    parent=self.root
                )
            else:
                self.status_send.set("❌ Errore avvio Ralph")
                messagebox.showerror("Errore", "Impossibile avviare Ralph loop!")

        except Exception as e:
            self.status_send.set(f"❌ Errore: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'avvio di Ralph:\n{str(e)}")

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
