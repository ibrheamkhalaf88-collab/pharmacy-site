import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent  # <project_root>

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))

# WhatsApp pharmacy number — comes from env
WA_PHARMACY_NUMBER = os.getenv("WA_PHARMACY_NUMBER", "9705952224444")

# إذا ضبطنا環境變量  WA_BASE_URL (مثلاً ل API واتساب تجاريّ), لازم
# لكن في التطوير العادي، الواتساب يفتح عبر الرابط المباشر wa.me
