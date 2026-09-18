# Pharmacy Site — صيدلية السلاق

متجر إلكتروني متكامل لصيدلية السلاق، يعمل عبر **FastAPI + Supabase (Postgres) + WhatsApp**. الطلبات تُحفظ في قاعدة البيانات، السعر يُحسب سيرفر-سايد، ولوحة الإدارة محمية بكلمة سر.

## الهيكلية

```
pharmacy_site/
├── backend/app/
│   ├── main.py            # FastAPI entry point (يُقدّم الواجهة فقط + /api/*)
│   ├── config.py          # كل الإعدادات من .env (لا أسرار في الكود)
│   ├── database.py        # الوصول لـ Supabase (products/orders/settings/stats)
│   ├── models.py          # Pydantic schemas (تحقق من المدخلات)
│   ├── security.py        # PBKDF2 + JWT-like tokens (stdlib فقط)
│   ├── deps.py            # require_admin (cookit أو Bearer)
│   ├── routers/           # auth / products / orders / settings
│   └── services/          # whatsapp (رسالة + إرسال API) / branch (كشف الفرع من الرقم)
├── frontend/
│   ├── index.html         # المتجر (عرض المنتجات + سلة + طلب)
│   ├── admin.html         # لوحة الإدارة (دخول + طلبات + منتجات + إعدادات)
│   └── assets/            # style.css / api.js / cart.js / app.js / admin.js / img/
├── supabase/migrations/   # SQL migrations (تُطبَّق على Supabase)
├── scripts/apply_migration.py  # تطبيق migrations عبر Management API
├── legacy/                # الكود القديم (للمرجعية فقط — غير مشغَّل)
├── requirements.txt
├── render.yaml
└── run.bat                # تشغيل محلي
```

## الإعداد المسبق

1. **Supabase**: أنشئ مشروعاً وانسخ `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` و `SUPABASE_ANON_KEY` إلى `.env` (انظر `.env.example`).
2. **الجدوال**: طبّق ملفات `supabase/migrations/` على قاعدة البيانات. الطريقتان:
   - **الأسهل**: افتح [Supabase Dashboard → SQL Editor](https://supabase.com/dashboard/project/vsffmvrpuwhodgqpjzcg/sql)، الصق محتوى `supabase/migrations/20260918_init.sql` واضغط Run.
   - **بالأداة**: أنشئ PAT من dashboard/account/tokens ثم شغّل:
     ```
     $env:SUPABASE_ACCESS_TOKEN="sbp_..."
     $env:SUPABASE_PROJECT_REF="vsffmvrpuwhodgqpjzcg"
     python scripts/apply_migration.py supabase/migrations/20260918_init.sql
     ```
   - أو اترك `deploy-supabase-migrations.yml` (يعمل تلقائياً بعد إضافة الـ Secrets).
3. **الإدارة**: ولّد hash كلمة السر وضعها في `.env`:
   ```
   venv\Scripts\python.exe -c "from backend.app.security import hash_password; print(hash_password('كلمة_سرك'))"
   ```
   ضع الناتج في `ADMIN_PASSWORD_HASH` وأنشئ `TOKEN_SECRET` عشوائياً.

## التشغيل

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
# أو دبل كليك run.bat
```

افتح:
- المتجر: http://localhost:8000
- لوحة الإدارة: http://localhost:8000/admin

## الـ API

| Endpoint | Auth | الوصف |
|---|---|---|
| `GET /api/products` | عام | قائمة المنتجات + الفئات |
| `POST /api/orders` | عام | إنشاء طلب (السعر من قاعدة البيانات) |
| `GET /api/orders` | إدارة | قائمة الطلبات (فلتر `?status=`) |
| `PUT /api/orders/{id}/status` | إدارة | تغيير الحالة |
| `POST /api/orders/{id}/reply` | إدارة | حفظ رد على الطلب |
| `POST /api/auth/login` | — | دخول الإدارة (كوكيز HttpOnly) |
| `POST /api/products` | إدارة | إضافة منتج |
| `PUT /api/products/{id}` | إدارة | تعديل منتج |
| `DELETE /api/products/{id}` | إدارة | حذف منتج |
| `GET/PUT /api/settings` | إدارة | إعدادات الصيدلية |

## النشر (Render)

- `render.yaml` جاهز: نقطة الدخول `backend.app.main:app`، والصحة على `/api/health`.
- أضف هذه الـ env vars في Render: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `ADMIN_PASSWORD_HASH`, `TOKEN_SECRET` (و `COOKIE_SECURE=true`).
- لتفعيل deploy hook: أضف variable `RENDER_DEPLOY_HOOK` (رابط Deploy Hook من Render) وسيتفعل `deploy-render.yml`.

## GitHub Secrets للمداومة

في Settings → Secrets and variables → Actions:
- `SUPABASE_ACCESS_TOKEN` — PAT من dashboard/account/tokens
- `SUPABASE_PROJECT_REF` — معرّف المشروع
- (ليست أسراراً بل Variables) `RENDER_DEPLOY_HOOK` للـ deploy

## ملاحظات أمان (طبّقت في هذا البناء)

- لا وجود لـ StaticFiles على جذر المشروع → ملفات `.env`, `orders.json`, الكود المصدري **لا تُقدَّم**.
- كل نصوص المنتجات/الطلبات تُعرض في المتصفح عبر `esc()` في `frontend/assets/api.js` → لا Stored XSS.
- الأسعار تُحسب من قاعدة البيانات فقط (لا تُصدَّق من المتصفح).
- `orders` و `settings` مقفولتان RLS للعامة — الوصول عبر service_role داخل الخادم فقط.
- كلمة سر الإدارة مخزّنة كـ PBKDF2-HMAC-SHA256 hash (لا نص صريح) في `.env` فقط.