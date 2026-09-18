"""Configuration — كل الإعدادات من env variables فقط (لا أسرار في الكود)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# جذر المشروع = parents[2] لأن هذا الملف في backend/app/config.py
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# ── Supabase ──
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if BACKEND_PORT := os.getenv("BACKEND_PORT", "").strip():
    PORT = int(BACKEND_PORT)
else:
    PORT = 8000

# ── Auth ──
# ADMIN_PASSWORD_HASH بصيغة: salt_hex$digest_hex (PBKDF2-HMAC-SHA256, 200k)
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "").strip()
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "24"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").strip().lower() == "true"

# ── WhatsApp ──
WA_PHARMACY_NUMBER = os.getenv("WA_PHARMACY_NUMBER", "9705952224444").strip()