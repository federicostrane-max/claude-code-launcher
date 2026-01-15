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

## Documentazione Automatica

Aggiorna la documentazione secondo questa matrice:

| Trigger | File da aggiornare | Azione |
|---------|-------------------|--------|
| Nuovo componente/modulo | `docs/architecture.md` | Aggiungi sezione con scopo, interfacce, dipendenze |
| Modifica DB | `docs/database-schema.md` | Aggiorna schema e relazioni |
| Nuovo pattern obbligatorio | `.claude/rules/critical-rules.md` | Aggiungi regola con rationale |
| Bug risolto non ovvio | `docs/troubleshooting.md` | Documenta sintomo → causa → fix |
| Cambio architettura core | `CLAUDE.md` | Aggiorna overview |
| Nuova API/endpoint | `docs/api-reference.md` | Documenta path, payload, response |

### Criteri per "significativo"
- Un altro sviluppatore ne avrebbe bisogno per capire il cambio
- Il comportamento differisce da quello atteso
- È stato risolto un bug che potrebbe ripresentarsi

### NON aggiornare per
- Refactoring senza cambio interfaccia
- Fix typo
- Ottimizzazioni interne

## Workflow
1. Modifica il codice
2. Se necessario → aggiorna documentazione
3. Commit + push automatico
4. Se modificato un file `.py` → rebuild exe
