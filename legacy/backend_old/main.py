"""صيدلية السلاق — FastAPI application.
يقدّم الـ API endpoints + يخدم الـ frontend الثابت.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api import router
from config import BACKEND_PORT

app = FastAPI(
    title="صيدلية السلاق API",
    description="API لطلبات الأدوية والمنتجات الصيدلانية",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# الـ API routes
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "name": "صيدلية السلاق API"}

# ── Admin dashboard redirect ──
# البان节 الإدارية موجودة تحت /api/admin (عبر الـ router prefix).
# نRedirect من /admin إلى /api/admin للوصول إليها من العنوان الرئيسي.
from fastapi.responses import RedirectResponse

@app.get("/admin")
def admin_redirect():
    return RedirectResponse(url="/api/admin", status_code=302)

# Serve frontend static files (index.html, style.css, app.js, img/, etc.)
FRONTEND_DIR = Path(__file__).parent
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BACKEND_PORT, reload=False)
