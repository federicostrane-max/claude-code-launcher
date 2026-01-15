# Claude Code Rules

## GIT Auto
Dopo ogni modifica ai file, esegui automaticamente commit e push senza chiedere conferma:
```bash
git add . && git commit -m "<descrizione modifica>" && git push
```

## REBUILD EXE
Dopo ogni modifica ai file Python (`.py`), ricompila automaticamente l'eseguibile:
```bash
build_launcher_v6.bat
```

## Workflow
1. Modifica il codice
2. Commit + push automatico
3. Se modificato un file `.py` → rebuild exe
