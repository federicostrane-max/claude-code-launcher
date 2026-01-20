# Integrazione Ralph Wiggum in Claude Launcher

## Panoramica

Questo documento descrive l'integrazione della metodologia "Ralph Wiggum" nel Claude Code Launcher, aggiungendo una modalità di coding autonomo.

---

## Cos'è Ralph Wiggum

Ralph Wiggum è un workflow ideato da Geoffrey Huntley per far lavorare Claude in modo autonomo su progetti di sviluppo. Il concetto chiave è:

**Loop con contesto fresco**: invece di una singola sessione lunga (dove il contesto si "inquina"), Claude viene eseguito ripetutamente in un loop. Ogni iterazione:
1. Parte con contesto pulito
2. Legge le specifiche e il piano di implementazione
3. Sceglie UN task da completare
4. Implementa, testa, committa
5. Esce

Il loop riparte e Claude, con contesto fresco, legge il piano aggiornato e continua col prossimo task.

### Vantaggi
- **Context window ottimale**: ogni iterazione usa il contesto in modo efficiente
- **Autonomia**: Claude lavora da solo, l'utente può fare altro
- **Tracciabilità**: ogni task = un commit
- **Resilienza**: se qualcosa va storto, il contesto fresco permette di riprovare

### File chiave di Ralph
- `PROMPT_plan.md` - Istruzioni per la fase di pianificazione
- `PROMPT_build.md` - Istruzioni per la fase di implementazione
- `AGENTS.md` - Guida operativa (comandi build, test, pattern del progetto)
- `IMPLEMENTATION_PLAN.md` - Lista prioritizzata dei task (generato e aggiornato da Claude)
- `specs/*.md` - Specifiche dei requisiti

---

## Integrazione nel Claude Launcher

### Flusso utente

1. L'utente seleziona un progetto e avvia una sessione Claude (come prima)
2. Nel tab "Invia a Claude", scrive il suo obiettivo nel box messaggi
3. Invece di copiare il messaggio, clicca il bottone **"USA RALPH"**
4. Si apre un dialog di configurazione con:
   - **Obiettivo**: cosa vuole che Claude implementi (pre-compilato col messaggio)
   - **Directory sorgente**: dove si trova il codice (default: `.`)
   - **Comando test**: per la validazione (default: `npm test`)
   - **Comando build**: per la compilazione (default: `npm run build`)
   - **Modello**: `sonnet` (veloce) o `opus` (ragionamento complesso)
   - **Max iterazioni**: limite di sicurezza (1-50)
   - **Modalità**:
     - PLAN - Prima crea il piano di implementazione
     - BUILD - Va diretto all'implementazione

5. L'utente clicca "Avvia Ralph"
6. L'app:
   - Crea i file Ralph nel progetto (PROMPT_*.md, AGENTS.md, specs/)
   - Genera una spec iniziale con l'obiettivo dell'utente
   - Lancia un nuovo Windows Terminal con il loop Ralph

7. Ralph lavora in autonomia nel terminale

### Componenti implementati

#### Template dei prompt
I template sono definiti come costanti nel codice Python:
- `RALPH_PROMPT_BUILD_TEMPLATE` - Template per la fase BUILD
- `RALPH_PROMPT_PLAN_TEMPLATE` - Template per la fase PLAN
- `RALPH_AGENTS_TEMPLATE` - Template per AGENTS.md

#### Funzioni principali
- `create_ralph_files()` - Genera tutti i file necessari nel progetto
- `launch_ralph_loop()` - Crea lo script batch e lancia il loop in Windows Terminal

#### UI
- `RalphConfigDialog` - Dialog di configurazione con tutti i parametri
- Bottone "USA RALPH" nel tab di invio

### Loop batch per Windows

Il loop è implementato come script batch temporaneo:

```batch
@echo off
setlocal enabledelayedexpansion
set ITERATION=0

:loop
if !ITERATION! GEQ {max_iterations} (
    echo Reached max iterations
    pause
    exit /b 0
)

set /a ITERATION+=1
echo ======================== LOOP !ITERATION! ========================

type "{prompt_file}" | claude -p --dangerously-skip-permissions --model {model}

goto loop
```

Il loop:
- Esegue `claude -p` (modalità headless) con il prompt
- Usa `--dangerously-skip-permissions` per non chiedere conferme
- Continua fino a max iterazioni o Ctrl+C

---

## Limitazioni attuali

### Nessun push automatico
A differenza del Ralph originale, il loop attuale non fa `git push` dopo ogni iterazione. Claude fa commit ma il push rimane manuale.

### Configurazione statica
I comandi test/build sono impostati una volta all'inizio. Se il progetto usa comandi diversi per parti diverse, bisogna modificare manualmente AGENTS.md.

---

## Questioni aperte

### Rilevamento completamento task

**Problema**: Come capire automaticamente quando il loop deve terminare perché l'obiettivo è stato raggiunto?

**Situazione attuale**: Il loop termina solo quando:
1. Si raggiunge il numero massimo di iterazioni
2. L'utente preme Ctrl+C manualmente

Non c'è detection automatica del completamento.

**Possibili soluzioni da valutare**:

1. **Marker di completamento**
   - Claude scrive un file `COMPLETED` quando il piano è vuoto
   - Il loop batch controlla l'esistenza del file e si ferma
   - Pro: semplice da implementare
   - Contro: richiede che Claude segua sempre questa convenzione

2. **Analisi output Claude**
   - Il loop cattura l'output di Claude in un file
   - Cerca pattern come "All tasks completed", "Nothing left to implement"
   - Pro: non richiede file aggiuntivi
   - Contro: parsing fragile, dipende dal linguaggio di Claude

3. **Check del piano**
   - Dopo ogni iterazione, uno script analizza `IMPLEMENTATION_PLAN.md`
   - Se vuoto o tutti i task sono marcati completati, termina
   - Pro: semanticamente corretto
   - Contro: richiede parsing del markdown, Claude potrebbe usare formati diversi

4. **Approccio ibrido**
   - Combina più metodi con fallback
   - Es: prima check marker, poi analisi piano, infine max iterazioni
   - Pro: robusto
   - Contro: complessità

5. **Lasciare manuale (come l'originale)**
   - L'utente monitora il terminale e ferma quando vede che ha finito
   - Pro: zero complessità, controllo totale
   - Contro: richiede attenzione umana

**Decisione**: DA DEFINIRE

---

## Sviluppi futuri

- [ ] Decidere strategia di rilevamento completamento
- [ ] Aggiungere opzione per git push automatico
- [ ] Supporto per progetti con strutture non-standard
- [ ] Log persistente delle sessioni Ralph
- [ ] UI per monitorare il progresso senza guardare il terminale
