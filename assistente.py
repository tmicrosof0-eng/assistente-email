"""
Assistente AI via email, collegato a Gemini (piano gratuito).

Uso:
  python assistente.py          -> gira all'infinito, controlla ogni 2 minuti (per PC / Raspberry)
  python assistente.py --once   -> controlla una volta sola ed esce (per GitHub Actions)

Variabili d'ambiente richieste:
  GMAIL_ADDRESS        indirizzo Gmail dell'assistente
  GMAIL_APP_PASSWORD   password per le app di quell'account Gmail
  GEMINI_API_KEY       chiave API da Google AI Studio
  ALLOWED_SENDERS      i tuoi indirizzi autorizzati, separati da virgola

Variabili opzionali:
  GEMINI_MODEL         modello da usare (default: gemini-2.5-flash)
"""
import email
import imaplib
import os
import smtplib
import sys
import time
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

from google import genai
from google.genai import types

GMAIL = os.environ["GMAIL_ADDRESS"]
APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
ALLOWED = {a.strip().lower() for a in os.environ["ALLOWED_SENDERS"].split(",") if a.strip()}
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
CHECK_EVERY_SECONDS = 120

SYSTEM_PROMPT = (
    "Sei un assistente che risponde a email. Rispondi nella stessa lingua "
    "in cui è scritta la richiesta. Scrivi in testo semplice, senza markdown "
    "(niente asterischi, cancelletti o tabelle), in modo chiaro e utile, "
    "come in una email ben scritta."
)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


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
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL, APP_PASSWORD)
        smtp.send_message(out)


def ask_gemini(prompt):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    return (response.text or "").strip()


def check_inbox():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(GMAIL, APP_PASSWORD)
    imap.select("INBOX")
    _, data = imap.search(None, "UNSEEN")

    for num in data[0].split():
        _, raw = imap.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(raw[0][1])
        sender = parseaddr(msg["From"])[1].lower()

        if sender not in ALLOWED:
            print(f"Ignorata email da mittente non autorizzato: {sender}")
            continue

        subject = str(make_header(decode_header(msg["Subject"] or ""))) or "(senza oggetto)"
        body = clean_quoted(get_text(msg))
        prompt = f"Oggetto: {subject}\n\n{body}".strip()

        try:
            answer = ask_gemini(prompt)
            if not answer:
                raise RuntimeError("risposta vuota da Gemini")
        except Exception as e:
            print(f"Errore Gemini ({e}); riprovo al prossimo giro.")
            imap.store(num, "-FLAGS", "\\Seen")  # la rimette come non letta
            continue

        send_reply(sender, subject, answer, msg["Message-ID"])
        print(f"Risposto a {sender}: {subject}")

    imap.logout()


def main():
    if "--once" in sys.argv:
        check_inbox()
        return
    while True:
        try:
            check_inbox()
        except Exception as e:
            print("Errore:", e)
        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
