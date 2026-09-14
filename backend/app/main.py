"""صيدلية السلاق — FastAPI application.
يقدّم الـ API endpoints + يخدم الـ frontend الثابت من مجلد frontend/.
"""
from fastapi import FastAPI
from app.api import router
from app.config import BACKEND_PORT

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
    return {"status": "ok", "name": "صيدلية السلاق API", "port": BACKEND_PORT, "backend_port": BACKEND_PORT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BACKEND_PORT, reload=False)
