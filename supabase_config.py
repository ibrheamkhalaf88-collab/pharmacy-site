"""
التكوين الخاص بـ Supabase.
يوفر دوال مساعدة لربط الـ backend بـ Supabase tables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# مسارات الملفات
BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"

# ── Supabase ──
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# أسماء الجداول في Supabase
TABLE_PRODUCTS = "products"
TABLE_ORDERS = "orders"
TABLE_SETTINGS = "settings"

# ── WhatsApp ──
WA_PHARMACY_NUMBER = os.getenv("WA_PHARMACY_NUMBER", "9705952224444")

# ── ports ──
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))

# ── دوال مساعدة ──
def is_supabase_configured() -> bool:
    """هل تم تكوين Supabase؟"""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)

def get_supabase_urls() -> dict:
    """إرجاع URLs للـ frontend عشان يعمل API calls"""
    return {
        "api_base": f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else "",
        "anon_key": SUPABASE_ANON_KEY,
    }
