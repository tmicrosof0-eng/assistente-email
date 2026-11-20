"""
Assistente AI via email, collegato a Groq (piano gratuito).

Uso:
  python assistente.py          -> gira all'infinito, controlla ogni 2 minuti (per PC / Raspberry)
  python assistente.py --once   -> controlla una volta sola ed esce (per GitHub Actions)

Variabili d'ambiente richieste:
  GMAIL_ADDRESS        indirizzo Gmail dell'assistente
  GMAIL_APP_PASSWORD   password per le app di quell'account Gmail
  GROQ_API_KEY         chiave API da console.groq.com
  ALLOWED_SENDERS      i tuoi indirizzi autorizzati, separati da virgola

Variabili opzionali:
  GROQ_MODEL           modello da provare per primo
"""
import email
import imaplib
import json
import os
import smtplib
import sys
import time
import urllib.error
import urllib.request
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

GMAIL = os.environ["GMAIL_ADDRESS"]
APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
ALLOWED = {a.strip().lower() for a in os.environ["ALLOWED_SENDERS"].split(",") if a.strip()}
GROQ_API_KEY = os.environ["GROQ_API_KEY"].strip()

# Modelli provati in ordine: se uno non funziona, passa al successivo
MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
if os.environ.get("GROQ_MODEL"):
    MODELS.insert(0, os.environ["GROQ_MODEL"].strip())

API_URL = "https://api.groq.com/openai/v1/chat/completions"
CHECK_EVERY_SECONDS = 120
AI_TIMEOUT = 40      # secondi per ogni richiesta all'AI
NET_TIMEOUT = 30     # secondi per Gmail

SYSTEM_PROMPT = (
    "Sei un assistente che risponde a email. Rispondi nella stessa lingua "
    "in cui è scritta la richiesta. Scrivi in testo semplice, senza markdown "
    "(niente asterischi, cancelletti o tabelle), in modo chiaro e utile, "
    "come in una email ben scritta."
)


def log(*args):
    print(*args, flush=True)


def get_text(msg):
    """Estrae il testo semplice dall'email."""
    parts = msg.walk() if msg.is_multipart() else [msg]
    for p in parts:
        if p.get_content_type() == "text/plain" and not p.get_filename():
            payload = p.get_payload(decode=True)
            if payload:
                return payload.decode(p.get_content_charset() or "utf-8", errors="replace")
    return ""


def clean_quoted(text):
    """Toglie le righe citate (>) e l'intestazione 'Il giorno ... ha scritto:'."""
    lines = []
    for line in text.splitlines():
        if line.startswith(">"):
            continue
        lowered = line.lower()
        if lowered.startswith(("il giorno ", "on ")) and ("scritto" in lowered or "wrote" in lowered):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def send_reply(to, subject, text, msg_id):
    out = EmailMessage()
    out["From"] = GMAIL
    out["To"] = to
    out["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if msg_id:
        out["In-Reply-To"] = msg_id
        out["References"] = msg_id
    out.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=NET_TIMEOUT) as smtp:
        smtp.login(GMAIL, APP_PASSWORD)
        smtp.send_message(out)


def call_model(model, prompt):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "email-assistant/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=AI_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = (data["choices"][0]["message"]["content"] or "").strip()
    if not text:
        raise RuntimeError("risposta vuota")
    return text


def ask_ai(prompt):
    """Prova i modelli in ordine finché uno risponde."""
    last_error = None
    for model in MODELS:
        log(f"Chiedo a Groq ({model})...")
        try:
            return call_model(model, prompt)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:300]
            last_error = f"HTTP {e.code}: {detail}"
        except Exception as e:
            last_error = str(e)
        log(f"Modello {model} non ha funzionato: {last_error}")
        time.sleep(3)
    raise RuntimeError(last_error)


def check_inbox():
    log("Mi collego a Gmail...")
    imap = imaplib.IMAP4_SSL("imap.gmail.com", timeout=NET_TIMEOUT)
    imap.login(GMAIL, APP_PASSWORD)
    imap.select("INBOX")
    _, data = imap.search(None, "UNSEEN")
    ids = data[0].split()
    log(f"Email non lette trovate: {len(ids)}")

    for num in ids:
        _, raw = imap.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(raw[0][1])
        sender = parseaddr(msg["From"])[1].lower()

        if sender not in ALLOWED:
            log(f"Ignorata email da mittente non autorizzato: {sender}")
            continue

        subject = str(make_header(decode_header(msg["Subject"] or ""))) or "(senza oggetto)"
        body = clean_quoted(get_text(msg))
        prompt = f"Oggetto: {subject}\n\n{body}".strip()

        try:
            answer = ask_ai(prompt)
        except Exception as e:
            log(f"Nessun modello ha risposto ({e}); riprovo al prossimo giro.")
            imap.store(num, "-FLAGS", "\\Seen")  # la rimette come non letta
            continue

        send_reply(sender, subject, answer, msg["Message-ID"])
        log(f"Risposto a {sender}: {subject}")

    imap.logout()
    log("Fine controllo.")


def main():
    if "--once" in sys.argv:
        check_inbox()
        return
    while True:
        try:
            check_inbox()
        except Exception as e:
            log("Errore:", e)
        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
