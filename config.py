"""
Configuración centralizada del proyecto BuscaCasas.
Carga variables de entorno desde .env si existe.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Scraping ---
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION", "madrid")
MAX_PAGES = int(os.getenv("MAX_PAGES", "3"))

# --- Email (SMTP) ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

# --- Salida ---
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")

# --- Scoring ---
MIN_SCORE = float(os.getenv("MIN_SCORE", "3.5"))
MAX_EMAIL_RESULTS = int(os.getenv("MAX_EMAIL_RESULTS", "10"))

# --- Scrapers activos ---
ACTIVE_SCRAPERS = os.getenv("ACTIVE_SCRAPERS", "fotocasa,pisos,redpiso")
