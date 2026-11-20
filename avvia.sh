#!/bin/bash
# Per PC / Raspberry (Mac e Linux). Compila prima i valori qui sotto.
export GMAIL_ADDRESS="mio.assistente@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export GEMINI_API_KEY="la_tua_chiave"
export ALLOWED_SENDERS="tuo.indirizzo@gmail.com"
pip install -r requirements.txt
python3 assistente.py
