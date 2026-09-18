"""صيدلية السلاق — FastAPI entry point.

يقدّم فقط ملفات الواجهة (frontend/) مجزأة: index في / وما في /admin.
لا توجد أي StaticFiles على جذر المشروع — لا يمكن الوصول للـ .env أو الملفات الداخلية.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import PORT
from .routers import auth, orders, products, settings
from .services import branch

STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="Salaq Pharmacy API", version="2.0.0")

app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/branch-info")
def branch_info():
    return {"branches": branch.AREA_CODE_BRANCHES, "default": branch.DEFAULT_BRANCH}


@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html; charset=utf-8")


@app.get("/admin", include_in_schema=False)
def serve_admin():
    return FileResponse(STATIC_DIR / "admin.html", media_type="text/html; charset=utf-8")


app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=PORT, reload=False)