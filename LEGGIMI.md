# Assistente AI via email (Gemini, gratis)

Scrivi un'email a una casella Gmail dedicata e Gemini ti risponde via email.

## PASSO 1 - Crea la casella Gmail dell'assistente
1. Crea un nuovo account Gmail (es. `mio.assistente@gmail.com`).
2. Attiva la **verifica in due passaggi**: myaccount.google.com/security
3. Crea una **password per le app**: myaccount.google.com/apppasswords
   Dai un nome qualsiasi (es. "assistente") e copia le 16 lettere che ti mostra.
   (Se la pagina non compare, la verifica in due passaggi non e' attiva.)

## PASSO 2 - Prendi la chiave Gemini (gratis)
1. Vai su https://aistudio.google.com/apikey
2. Accedi con un account Google e clicca "Create API key".
3. Copia la chiave.

## PASSO 3 - Scegli dove farlo girare

### Opzione A: GitHub Actions (nessun PC acceso, gratis)
1. Crea un account su github.com e un **nuovo repository PUBBLICO**
   (i repository pubblici hanno minuti gratuiti illimitati; il codice non contiene password).
2. Carica tutti i file di questa cartella nel repository
   (comprese la cartella `.github` e il file dentro `workflows`).
3. Nel repository vai su **Settings > Secrets and variables > Actions > New repository secret**
   e crea 4 secret, con questi nomi esatti:
   - `GMAIL_ADDRESS` = indirizzo Gmail dell'assistente
   - `GMAIL_APP_PASSWORD` = le 16 lettere del passo 1
   - `GEMINI_API_KEY` = la chiave del passo 2
   - `ALLOWED_SENDERS` = il TUO indirizzo email personale (da cui scriverai)
4. Vai nella scheda **Actions**, abilita i workflow se richiesto, apri
   "Assistente email" e clicca **Run workflow** per provare.
Poi parte da solo ogni ~5 minuti (GitHub puo' ritardare di qualche minuto).
Nota: GitHub sospende i workflow programmati dopo 60 giorni senza attivita' nel repository;
se succede, riattivali dalla scheda Actions.

### Opzione B: sul tuo PC / Raspberry (deve restare acceso)
1. Installa Python da python.org (su Windows spunta "Add Python to PATH").
2. Apri `avvia.bat` (Windows) o `avvia.sh` (Mac/Linux) con un editor di testo
   e sostituisci i 4 valori con i tuoi.
3. Avvia il file con doppio clic (Windows) o `./avvia.sh` da terminale.
Controlla la casella ogni 2 minuti finche' la finestra resta aperta.

## PASSO 4 - Provalo
Dal tuo indirizzo personale scrivi una email all'assistente, con la domanda
nell'oggetto e/o nel testo. Dopo qualche minuto arriva la risposta.

## Problemi comuni
- **Nessuna risposta:** controlla che scrivi dall'indirizzo messo in `ALLOWED_SENDERS`.
- **Errore di login:** usa la password per le app, non quella normale dell'account.
- **Errore Gemini / limite raggiunto:** il piano gratuito ha limiti giornalieri;
  lo script riprova da solo al giro successivo.
- **Modello non trovato:** in AI Studio guarda il nome di un modello gratuito attuale
  e impostalo con la variabile `GEMINI_MODEL`.
- Sul piano gratuito Google puo' usare i contenuti per migliorare i suoi prodotti:
  non inviare dati sensibili.
