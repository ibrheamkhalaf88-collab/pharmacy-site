# Pharmacy Site - صيدلية السلاق

## هيكلية المشروع

```
pharmacy_site/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration (API keys, settings)
│   │   ├── models.py        # Pydantic models for data validation
│   │   ├── api.py           # API routes (GET /api/products, POST /api/order)
│   │   └── products.py      # Product data + business logic
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # HTML structure (RTL, semantic)
│   ├── css/
│   │   └── style.css        # All styles (responsive, tokens, animations)
│   ├── js/
│   │   ├── app.js           # Main app logic (fetch products, render)
│   │   ├── cart.js          # Cart state + floating bar
│   │   └── whatsapp.js      # WhatsApp order message builder
│   └── img/                 # Static assets (logos, icons if any)
├── .env.example             # Environment variables (copy to .env)
├── README.md                # كيف تشغل المشروع
└── run.py                   # DEV: ي backend + serve frontend
```

## البنية الصحيحة للمواقع (Best Practices):

### 1. Separation of Concerns
- **Backend (FastAPI)**: مسؤول عن البيانات، API endpoints، التحقق، منطق الأعمال.
- **Frontend (HTML/CSS/JS)**: مسؤول عن العرض، التفاعل، الطلبات للـ API.
- لا يخلطوا بين backend logic و frontend rendering.

### 2. API-First Design
- Frontend_bi_kom_con_ fetch() إلى endpoints backend.
- Backend_bicek JSON only (لا HTML).
- الأخطاء ترجع كـ JSON مع.status codes صحيحة.

### 3. Responsive Design
- CSS media queries للـ breakpoints.
- Flexbox/Grid للـ layouts.
- no fixed widths إلا للـ max-width للـ container.
- fluid typography (clamp()).

### 4. State Management
- Cart state في frontend (JS objects) + sync مع backend على submit.
- لا perlu session معقدة للطلب البسيط.

### 5. WhatsApp Integration
- Backend_yufi رابط واتساب pre-filled.
- أو frontend_yufi الرابط من data products.
```

## Run DEV:

```bash
cd pharmacy_site
python run.py
# ي有限公司 backend على port 8000 و serve frontend
# افتح http://localhost:8000
```

## منتجات تانية ممكن تضيفها لاحقًا:

- Database (SQLite / PostgreSQL) بدل JSON
- Authentication للصيدلاني (اللوحة الداخلية)
- دفع إلكتروني
- تتبع الطلبات
- استشارة فيديو

```