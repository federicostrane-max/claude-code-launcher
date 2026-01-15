# Claude Code Launcher 🚀

Un launcher per aprire rapidamente Claude Code con la lista delle sessioni recenti.

## 📁 File inclusi

| File | Descrizione |
|------|-------------|
| `Claude_Launcher.bat` | ⭐ **SOLUZIONE PIÙ SEMPLICE** - Funziona subito, basta cliccare |
| `claude_launcher.py` | Script Python (da compilare con PyInstaller) |
| `build_exe.bat` | Script per compilare .py → .exe con PyInstaller |
| `create_exe.ps1` | Script PowerShell per creare .exe (alternativo) |

---

## 🎯 Soluzione Consigliata: Claude_Launcher.bat

**Il modo più semplice!** Non richiede Python o altre installazioni.

### Come usarlo:

1. Copia `Claude_Launcher.bat` dove vuoi (es: Desktop)
2. Doppio click per avviarlo
3. La prima volta ti chiede il percorso della cartella del progetto
4. Il percorso viene salvato automaticamente per le volte successive

### Creare un collegamento sul Desktop:

1. Click destro su `Claude_Launcher.bat`
2. "Crea collegamento"
3. Sposta il collegamento sul Desktop
4. (Opzionale) Click destro → Proprietà → Cambia icona

---

## 🔧 Soluzione Alternativa: .EXE con Python

Se preferisci un vero .exe:

### Prerequisiti:
- Python installato
- pip disponibile

### Passaggi:

1. Apri un terminale nella cartella con i file
2. Esegui:
   ```cmd
   pip install pyinstaller
   pyinstaller --onefile --console --name "Claude_Launcher" claude_launcher.py
   ```
3. L'exe sarà in `dist\Claude_Launcher.exe`
4. Copia `Claude_Launcher.exe` dove vuoi

Oppure esegui semplicemente `build_exe.bat` che fa tutto automaticamente.

---

## 🔧 Soluzione Alternativa: .EXE con PowerShell

Se non hai Python ma vuoi comunque un .exe:

1. Click destro su `create_exe.ps1`
2. "Esegui con PowerShell"
3. Verrà creato `Claude_Launcher.exe`

**Nota:** Potrebbe essere necessario abilitare l'esecuzione di script:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📋 Funzionamento

1. **Prima esecuzione:** Ti chiede il percorso del progetto e lo salva
2. **Esecuzioni successive:** Usa il percorso salvato (puoi cambiarlo)
3. **Azione:** Apre un terminale, naviga alla cartella ed esegue `claude --resume`

Il file di configurazione viene salvato nella stessa cartella del launcher:
- Per .bat: `claude_config.txt`
- Per .py/.exe: `claude_launcher_config.json`

---

## 💡 Tip

Puoi creare più copie del launcher con configurazioni diverse per progetti diversi!
Basta copiare il .bat (o .exe) in cartelle diverse - ognuno avrà il suo file config.
