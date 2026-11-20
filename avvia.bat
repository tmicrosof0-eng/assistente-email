@echo off
REM Per PC Windows. Compila prima i valori qui sotto.
set GMAIL_ADDRESS=mio.assistente@gmail.com
set GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
set GEMINI_API_KEY=la_tua_chiave
set ALLOWED_SENDERS=tuo.indirizzo@gmail.com
pip install -r requirements.txt
python assistente.py
pause
