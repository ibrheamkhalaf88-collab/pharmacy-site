#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DEV runner - FastAPI backend + static frontend."""
import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).parent
FRONTEND_DIR = PROJECT_ROOT
BACKEND_PORT = 8000

print(f"[OK] Project: {PROJECT_ROOT}")
print(f"[OK] frontend: {FRONTEND_DIR}")
print(f"[OK] backend port: {BACKEND_PORT}")

if not (FRONTEND_DIR / "index.html").exists():
    print(f"[ERROR] index.html not found in {FRONTEND_DIR}")
    sys.exit(1)

from main import app as backend_app
from fastapi import Request

# DEV: امنع كاش المتصفح حتى يرى المطور أحدث الملفات دائماً
@backend_app.middleware("http")
async def no_cache(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["Cache-Control"] = "no-store"
    return resp

backend_app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

print(f"\n[OK] Backend running on http://localhost:{BACKEND_PORT}")
print(f"[OK] API docs: http://localhost:{BACKEND_PORT}/docs")
print(f"[OK] Frontend: http://localhost:{BACKEND_PORT}/")

import uvicorn
uvicorn.run(backend_app, host="0.0.0.0", port=BACKEND_PORT, reload=False)
