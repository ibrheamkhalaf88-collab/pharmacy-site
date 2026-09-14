#!/usr/bin/env python3
"""DEV runner — بيأذن backend على port 8000 ويerior frontend ثابت."""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
APP_DIR = BACKEND_DIR / "app"

# ✅ أضف المسارات عشان الإيمبورت يعمل
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

print(f"📦 المشروع: {PROJECT_ROOT}")
print(f"📄 frontend: {FRONTEND_DIR}")
print(f"🔧 backend:  {BACKEND_DIR}")

if not FRONTEND_DIR.exists():
    print(f"⚠️  frontend dir ناقص: {FRONTEND_DIR}")
    sys.exit(1)

print("\n🚀 بتشغيل الباك إند على http://localhost:8000")
print("   - API المنتجات:   GET  /api/products")
print("   - منتج معين:     GET  /api/products/1")
print("   - إرسال طلب:     POST /api/order")
print("   - لوحة الإدارة:   GET  /api/admin")
print("   - توثيق Swagger:  http://localhost:8000/docs")
print(f"   - الصفحة الرئيسية: http://localhost:8000")
print()

from app.main import app as backend_app
from fastapi.staticfiles import StaticFiles

backend_app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

import uvicorn
uvicorn.run(backend_app, host="0.0.0.0", port=8000, reload=False)
