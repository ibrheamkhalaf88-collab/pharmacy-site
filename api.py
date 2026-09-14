"""API routes — endpoints لـ المنتجات والطلبات والإدارة."""
from fastapi import APIRouter, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from models import Product, OrderRequest, OrderResponse, CartItem
from products import (
    load_products, save_products, get_product_by_id,
    build_whatsapp_message, compute_total,
    load_orders, save_orders, add_order,
    get_settings, save_settings, add_product_image,
)
from branch import find_nearest_branch_by_phone
from urllib.parse import quote
from datetime import datetime, timezone

router = APIRouter(prefix="/api", tags=["pharmacy"])

# ── Products ──
@router.get("/products")
def list_products(category: str = None):
    all_products = load_products()
    filtered = all_products
    if category and category != "all":
        filtered = [p for p in all_products if p["category"] == category]
    categories = sorted(set(p["category"] for p in all_products))
    return {"products": filtered, "count": len(filtered), "categories": categories}

@router.get("/products/{product_id}")
def get_product(product_id: int):
    return {"product": get_product_by_id(product_id)}

@router.post("/products", status_code=201)
async def add_product(data: dict):
    name = data.get("name","")
    category = data.get("category","أخرى")
    desc = data.get("desc","")
    try:
        price = float(data.get("price",0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="السعر يجب أن يكون رقمًا صحيحًا")
    if price <= 0:
        raise HTTPException(status_code=400, detail="السعر يجب أن يكون أكبر من صفر")
    icon = data.get("icon","medical") or "medical"
    image = data.get("image","") or ""
    if not name or not desc:
        raise HTTPException(status_code=400, detail="الاسم والوصف مطلوبان")
    all_products = load_products()
    new_id = max((p["id"] for p in all_products), default=0) + 1
    new_product = {
        "id": new_id,
        "name": name,
        "category": category,
        "desc": desc,
        "price": price,
        "icon": icon,
        "image": image,
    }
    all_products.append(new_product)
    save_products(all_products)
    return {"product": new_product, "status": "created"}

@router.put("/products/{product_id}")
def update_product(product_id: int, product: Product):
    all_products = load_products()
    for i, p in enumerate(all_products):
        if p["id"] == product_id:
            all_products[i] = {
                "id": product_id,
                "name": product.name,
                "category": product.category,
                "desc": product.desc,
                "price": product.price,
                "icon": product.icon or "medical",
                "image": product.image,
            }
            save_products(all_products)
            return {"product": all_products[i], "status": "updated"}
    raise HTTPException(status_code=404, detail="المنتج غير موجود")

@router.delete("/products/{product_id}")
def delete_product(product_id: int):
    all_products = load_products()
    before = len(all_products)
    all_products = [p for p in all_products if p["id"] != product_id]
    if len(all_products) == before:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    save_products(all_products)
    return {"status": "deleted", "product_id": product_id}

# ── Orders ──
@router.post("/order")
def create_order(order: OrderRequest):
    all_products = load_products()
    order_items = []
    for item in order.items:
        product = get_product_by_id(item.product_id)
        order_items.append({
            "name": product["name"],
            "quantity": item.quantity,
            "price": product["price"],
            "category": product["category"],
        })

    total = compute_total(order_items)
    # تحديد الفرع الأقرب بناءً على رقم الهاتف
    branch_info = find_nearest_branch_by_phone(order.customer_phone or "")
    message = build_whatsapp_message(order_items, order.customer_name or "", branch_info)
    encoded_message = quote(message, safe="")

    settings = get_settings()
    wa_number = settings.get("whatsapp_number", settings.get("phone", "9705952224444"))
    whatsapp_url = f"https://wa.me/{wa_number}?text={encoded_message}"

    order_data = {
        "customer_name": order.customer_name or "",
        "customer_phone": order.customer_phone or "",
        "notes": order.notes or "",
        "items": order_items,
        "total": total,
        "item_count": len(order_items),
        "whatsapp_url": whatsapp_url,
        "message": message,
        "branch": branch_info.get("branch", ""),
        "branch_name": branch_info.get("branch_name", ""),
        "delivery_zone": branch_info.get("delivery_zone", ""),
    }

    saved = add_order(order_data)

    return {
        "status": "received",
        "whatsapp_url": whatsapp_url,
        "total": total,
        "item_count": len(order_items),
        "customer_name": order.customer_name or "",
        "customer_phone": order.customer_phone or "",
        "notes": order.notes or "",
        "items": order_items,
        "created_at": saved["created_at"],
        "message": message,
    }

@router.get("/orders")
def list_orders(status: str = None):
    orders = load_orders()
    if status and status != "all":
        orders = [o for o in orders if o.get("status") == status]
    return {"orders": orders, "count": len(orders)}

@router.get("/orders/{order_id}")
def get_order(order_id: int):
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            return {"order": o}
    raise HTTPException(status_code=404, detail="الطلب غير موجود")

@router.put("/orders/{order_id}/status")
def update_order_status(order_id: int, status: str = "pending"):
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            valid = ["pending", "confirmed", "preparing", "dispatched", "delivered", "cancelled"]
            if status not in valid:
                raise HTTPException(status_code=400, detail=f"حالة غير صالحة. الحالات: {', '.join(valid)}")
            o["status"] = status
            save_orders(orders)
            return {"order": o, "status": "updated"}
    raise HTTPException(status_code=404, detail="الطلب غير موجود")

@router.post("/orders/{order_id}/reply")
async def reply_to_order(order_id: int, request: Request):
    body = await request.json()
    message = body.get("message","")
    orders = load_orders()
    for o in orders:
        if o["id"] == order_id:
            if not message:
                raise HTTPException(status_code=400, detail="الرسالة مطلوبة")
            o["reply"] = message
            o["replied_at"] = datetime.now(timezone.utc).isoformat()
            save_orders(orders)
            return {"order": o, "status": "replied"}
    raise HTTPException(status_code=404, detail="الطلب غير موجود")

# ── Settings (قابل للتعديل من لوحة الإدارة) ──
@router.get("/settings")
def get_pharmacy_settings():
    return {"settings": get_settings()}

@router.put("/settings")
async def update_pharmacy_settings(request: Request):
    body = await request.json()
    current = get_settings()
    # Validate and update only allowed fields
    allowed = ["name", "address", "phone", "whatsapp_number", "hours",
               "whatsapp_api_token", "whatsapp_phone_id", "whatsapp_base_url"]
    for key in allowed:
        if key in body:
            current[key] = body[key]
    save_settings(current)
    return {"settings": current, "status": "updated"}

# ── Product Image ──
@router.post("/products/{product_id}/image")
async def set_product_image(product_id: int, request: Request):
    body = await request.json()
    image_url = body.get("image", "").strip()
    if not image_url:
        raise HTTPException(status_code=400, detail="رابط الصورة مطلوب")
    updated = add_product_image(product_id, image_url)
    return {"product": updated, "status": "updated"}

# ── WhatsApp Cloud API Auto-Send ──
@router.post("/orders/{order_id}/send-whatsapp")
async def send_order_whatsapp(order_id: int):
    """
    يبعث طلب تلقائيًا على واتساب عبر WhatsApp Cloud API.
    يحتاج إعدادات whatsapp_api_token و whatsapp_phone_id في settings.json
    """
    try:
        import httpx
    except ImportError:
        return {"status": "error", "message": "حاجة httpx σημαντική (pip install httpx)"}

    orders = load_orders()
    order = None
    for o in orders:
        if o["id"] == order_id:
            order = o
            break
    if not order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")

    settings = get_settings()
    token = settings.get("whatsapp_api_token", "").strip()
    phone_id = settings.get("whatsapp_phone_id", "").strip()
    base_url = settings.get("whatsapp_base_url", "https://graph.facebook.com/v17.0")

    if not token or not phone_id:
        return {
            "status": "error",
            "message": "ما 예언 WhatsApp API مُعدّ. اذهب لـ Settings عشان تضبط token و phone ID.",
            "whatsapp_url": order.get("whatsapp_url", "")
        }

    message = build_whatsapp_message(order.get("items", []), order.get("customer_name", ""),
                                       {"branch": order.get("branch", ""), "branch_name": order.get("branch_name", ""),
                                        "delivery_zone": order.get("delivery_zone", "")})
    encoded = quote(message, safe="")

    url = f"{base_url}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": order.get("customer_phone", ""),
        "type": "text",
        "text": {"body": message}
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=data, timeout=15.0)
        result = resp.json()

    if resp.status_code == 200:
        return {"status": "sent", "data": result}
    return {
        "status": "error",
        "message": str(result),
        "whatsapp_url": f"https://wa.me/{settings.get('whatsapp_number', PHARMACY_NUMBER)}?text={encoded}"
    }

# ── Admin Dashboard Page ── (الإصدار الجديد — محدّث ومتصل بالكامل)
@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>لوحة تحكم الإدارة — صيدلية السلاق</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --green-900:#1F4D39; --green-700:#2F6B4F; --green-100:#E4F1EA;
  --blue-soft:#E6F1F4; --gray-900:#2B2B28; --gray-600:#6B6B64;
  --gray-400:#B5B5AE; --gray-200:#E8E6E1; --gray-100:#F8F7F4;
  --radius:12px; --shadow-sm:0 1px 3px rgba(0,0,0,.05);
  --shadow-md:0 4px 16px rgba(0,0,0,.08);
  --maxw:1180px;
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Tajawal',system-ui,sans-serif;background:var(--gray-100);color:var(--gray-900);line-height:1.6;min-height:100vh}
@starting-style{body{opacity:0;transform:translateY(8px)}}
body{animation:fadeUp .45s ease-out forwards}
@keyframes fadeUp{to{opacity:1;transform:translateY(0)}}
.btn{background:var(--green-700);color:#fff;border:none;border-radius:100px;padding:10px 22px;font-weight:600;cursor:pointer;transition:background .2s,transform .15s,box-shadow .2s;font-size:14px}
.btn:hover{background:var(--green-900);transform:translateY(-1px);box-shadow:var(--shadow-md)}
.btn.ghost{background:transparent;color:var(--gray-900);border:1.5px solid var(--gray-200)}
.btn.ghost:hover{border-color:var(--green-700);color:var(--green-700)}
.btn.danger{background:#c0392b;color:#fff;border:none;border-radius:100px;padding:10px 22px;font-weight:600;cursor:pointer;transition:background .2s}
.btn.danger:hover{background:#962d22}
.btn.small{padding:7px 14px;font-size:13px}
.btn.loading{pointer-events:none;opacity:.7}
.input,select,textarea{background:#fff;border:1.5px solid var(--gray-200);border-radius:10px;padding:10px 14px;width:100%;transition:border-color .2s,box-shadow .2s;font-size:14px}
.input:focus,select:focus,textarea:focus{outline:none;border-color:var(--green-700);box-shadow:0 0 0 3px rgba(47,107,79,.1)}
.card{background:#fff;border:1px solid var(--gray-200);border-radius:var(--radius);padding:24px;box-shadow:var(--shadow-sm);animation:slideUp .4s ease-out both}
.card.alt{background:var(--gray-100)}
.card h3{font-size:16px;font-weight:700;margin-bottom:16px;color:var(--gray-900)}
.card .meta{font-size:13px;color:var(--gray-600);margin-top:4px}
.card .meta strong{color:var(--gray-900)}
@keyframes slideUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}
.skeleton{background:linear-gradient(90deg,var(--gray-200) 25%,var(--gray-100) 50%,var(--gray-200) 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:8px;height:18px;margin-bottom:8px}
.badge{display:inline-block;padding:4px 10px;border-radius:100px;font-size:12px;font-weight:600}
.badge.pending{background:#FEF3C7;color:#92400E}
.badge.confirmed{background:#DBEAFE;color:#1E40AF}
.badge.preparing{background:#E4F1EA;color:#1F4D39}
.badge.dispatched{background:#DBEAFE;color:#1E40AF}
.badge.delivered{background:#D1FAE5;color:#065F46}
.badge.cancelled{background:#FEE2E2;color:#991B1B}
.admin-header{background:linear-gradient(135deg,var(--green-900),var(--green-700));color:#fff;padding:18px 0;position:sticky;top:0;z-index:50;box-shadow:0 2px 12px rgba(31,77,57,.3)}
.admin-header .container{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;max-width:var(--maxw);margin:0 auto;padding:0 20px}
.admin-header .brand{font-size:17px;font-weight:800}
.admin-header .brand small{color:rgba(255,255,255,.6);font-weight:400;font-size:13px;margin-right:6px;display:block}
.admin-header nav{display:flex;gap:6px;flex-wrap:wrap}
.admin-header nav button{color:rgba(255,255,255,.85);text-decoration:none;padding:8px 16px;border-radius:100px;font-size:14px;font-weight:500;cursor:pointer;transition:background .2s,color .2s;border:none;background:none}
.admin-header nav button:hover{background:rgba(255,255,255,.15);color:#fff}
.admin-header nav button.active{background:#fff;color:var(--green-900);font-weight:700}
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:#fff;border:1px solid var(--gray-200);border-radius:var(--radius);padding:20px 22px;box-shadow:var(--shadow-sm);animation:slideUp .5s ease-out both}
.stat-card:nth-child(1){animation-delay:.05s}.stat-card:nth-child(2){animation-delay:.1s}.stat-card:nth-child(3){animation-delay:.15s}.stat-card:nth-child(4){animation-delay:.2s}
.stat-card .stat-label{font-size:13px;color:var(--gray-600);font-weight:500;margin-bottom:4px}
.stat-card .stat-value{font-size:28px;font-weight:800;color:var(--gray-900);transition:all .3s}
.stat-card .stat-change{font-size:12px;color:var(--gray-400);margin-top:2px}
.panel-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px}
.panel-grid.single{grid-template-columns:1fr}
.table-wrap{overflow-x:auto;margin-top:16px;border:1px solid var(--gray-200);border-radius:var(--radius);animation:fadeUp .3s ease-out}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:600px}
th{text-align:right;padding:14px 16px;background:var(--gray-100);color:var(--gray-600);font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid var(--gray-200);position:sticky;top:0}
td{padding:14px 16px;border-bottom:1px solid var(--gray-200);color:var(--gray-900);vertical-align:middle}
tr:last-child td{border-bottom:none}
td.name{font-weight:600}
td.price{color:var(--green-700);font-weight:700}
td.actions{text-align:right;white-space:nowrap}
.tabs{display:flex;gap:4px;margin-bottom:20px;border-bottom:2px solid var(--gray-200);flex-wrap:wrap}
.tab{padding:10px 20px;font-size:14px;font-weight:600;color:var(--gray-600);cursor:pointer;border:none;background:none;border-bottom:2px solid transparent;margin-bottom:-2px;transition:color .2s,border-color .2s}
.tab:hover{color:var(--gray-900)}
.tab.active{color:var(--green-700);border-bottom-color:var(--green-700)}
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:100;padding:20px;opacity:0;pointer-events:none;transition:opacity .3s}
.modal-bg.open{opacity:1;pointer-events:auto}
.modal-bg .modal{background:#fff;border-radius:var(--radius);padding:28px;max-width:580px;width:100%;max-height:85vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.25);transform:translateY(20px) scale(.95);transition:transform .3s}
.modal-bg.open .modal{transform:translateY(0) scale(1)}
.modal h2{font-size:18px;margin-bottom:20px}
.modal .field{margin-bottom:16px}
.modal .field label{display:block;font-size:14px;font-weight:600;margin-bottom:6px;color:var(--gray-900)}
.modal .field .hint{font-size:12px;color:var(--gray-400);margin-top:4px}
.modal .actions{display:flex;gap:10px;justify-content:flex-end;margin-top:24px}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(100px);background:var(--green-900);color:#fff;padding:12px 24px;border-radius:100px;font-size:14px;font-weight:600;z-index:200;opacity:0;transition:all .3s ease-out;box-shadow:0 4px 16px rgba(0,0,0,.2)}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
.toast.error{background:#c0392b}
.toast.info{background:var(--blue-soft);color:var(--gray-900)}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
.pulse{animation:pulse .3s ease-out}
select.status-select{width:auto;padding:6px 10px;border-radius:100px;font-size:12px;font-weight:600;background:var(--green-100);border:1px solid var(--green-100);cursor:pointer}
select.status-select:focus{outline:none;border-color:var(--green-700);background:var(--green-100)}
@media(max-width:900px){
  .stats-row{grid-template-columns:repeat(2,1fr)}
  .panel-grid{grid-template-columns:1fr}
}
@media(max-width:560px){
  .admin-header .container{flex-direction:column;align-items:flex-start}
  .admin-header nav{width:100%}
  .stats-row{grid-template-columns:1fr}
  .container{padding:0 14px}
}
</style>
</head>
<body>

<header class="admin-header">
  <div class="container">
    <div class="brand">صيدلية السلاق <small>لوحة تحكم الإدارة</small></div>
    <nav>
      <button class="tab active" data-tab="products">المنتجات</button>
      <button class="tab" data-tab="orders">الطلبات</button>
      <button class="tab" data-tab="stats">إحصائيات</button>
      <button class="tab" data-tab="settings">الإعدادات</button>
    </nav>
  </div>
</header>

<main class="container" style="padding-top:28px;padding-bottom:48px">

  <div class="stats-row">
    <div class="stat-card"><div class="stat-label">إجمالي الطلبات</div><div class="stat-value" id="statOrders">—</div></div>
    <div class="stat-card"><div class="stat-label">الطلبات اليوم</div><div class="stat-value" id="statToday">—</div></div>
    <div class="stat-card"><div class="stat-label">المنتجات النشطة</div><div class="stat-value" id="statProducts">—</div></div>
    <div class="stat-card"><div class="stat-label">إجمالي الإيرادات</div><div class="stat-value" id="statRevenue">—</div></div>
  </div>

  <!-- Products Panel -->
  <div id="productsPanel">
    <div class="card">
      <h3>📦 إدارة المنتجات <span style="font-weight:400;font-size:13px;color:var(--gray-600);margin-right:8px">أضف — عدّل — حذف</span></h3>
      <div class="tabs" id="productTabs">
        <button class="tab active" data-ptab="list">القائمة</button>
        <button class="tab" data-ptab="add">إضافة منتج</button>
      </div>
      <div id="productList"></div>
      <div id="productAddForm" style="display:none">
        <div class="field"><label>اسم المنتج</label><input class="input" id="pName" placeholder="مثال: باراسيتامول ٥٠٠ملغ × ٢٠ قرص"></div>
        <div class="field"><label>التصنيف</label>
          <select id="pCategory">
            <option value="دواء">دواء</option><option value="فيتامين">فيتامين</option><option value="بشرة">بشرة</option><option value="أدوات">أدوات</option><option value="أخرى">أخرى</option>
          </select>
        </div>
        <div class="field"><label>السعر (شيكل)</label><input class="input" id="pPrice" type="number" step="0.01" placeholder="مثال: 12.50"></div>
        <div class="field"><label>الوصف</label><textarea class="input" id="pDesc" rows="3" placeholder="وصف موجز للمنتج..."></textarea></div>
        <div class="field"><label>الرمز</label>
          <select id="pIcon">
            <option value="pills">قرص/حبوب</option><option value="capsule">كبسولة</option><option value="syrup">شراب</option><option value="vitamin">فيتامين</option><option value="sunscreen">واقي شمس</option><option value="cream">مرطب</option><option value="medical">أدوات طبية</option>
          </select>
        </div>
        <div class="field"><label>رابط الصورة (اختياري)</label>
          <input class="input" id="pImage" placeholder="https://example.com/product.jpg">
          <p class="meta" style="margin-top:4px;font-size:12px;color:var(--gray-400)">اتركها فاضية للصورة الافتراضية حسب التصنيف.</p>
        </div>
        <div class="actions" style="margin-top:12px">
          <button class="btn ghost small" id="pCancel">إلغاء</button>
          <button class="btn small" id="pSave">حفظ المنتج</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Orders Panel -->
  <div id="ordersPanel" style="display:none">
    <div class="card">
      <h3>📋 إدارة الطلبات <span style="font-weight:400;font-size:13px;color:var(--gray-600);margin-right:8px">تصفية — حالة — رد</span></h3>
      <div class="tabs" id="orderTabs">
        <button class="tab active" data-otab="all">كل الطلبات</button>
        <button class="tab" data-otab="pending">معلقة</button>
        <button class="tab" data-otab="confirmed">مؤكدة</button>
        <button class="tab" data-otab="preparing">بتحضير</button>
        <button class="tab" data-otab="dispatched">صادر</button>
        <button class="tab" data-otab="delivered">وصلت</button>
        <button class="tab" data-otab="cancelled">ملغية</button>
      </div>
      <div class="table-wrap">
        <table><thead><tr><th>#</th><th>الزبون</th><th>الهاتف</th><th>الفرع</th><th>المنتجات</th><th>المجموع</th><th>الحالة</th><th>الوقت</th><th>إجراءات</th></tr></thead><tbody id="ordersBody"></tbody></table>
      </div>
    </div>
    <div class="card">
      <h3>💬 الرد على الزبون</h3>
      <p class="meta" style="margin-bottom:16px">اختر طلب من الجدول ثم اكتب ردك.</p>
      <div class="field"><label>رقم الطلب</label><input class="input" id="replyOrderId" placeholder="اختر من الجدول"></div>
      <div class="field"><label>الرسالة</label><textarea class="input" id="replyMsg" rows="4" placeholder="هنا تكتب الرد..."></textarea></div>
      <div class="actions">
        <button class="btn ghost small" id="replyCancel">إلغاء</button>
        <button class="btn small" id="replySend">إرسال الرد</button>
        <button class="btn small" id="replyWhatsappBtn" style="background:#25D366">📱 إرسال على واتساب</button>
      </div>
    </div>
  </div>

  <!-- Stats Panel -->
  <div id="statsPanel" style="display:none">
    <div class="card">
      <h3>📊 إحصائيات</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:16px">
        <div><div class="stat-label" style="font-size:14px;font-weight:700;color:var(--gray-900)">أعلى ٥ منتجات بالمبيعات</div><div id="topProducts" style="margin-top:12px"></div></div>
        <div><div class="stat-label" style="font-size:14px;font-weight:700;color:var(--gray-900)">توزيع الطلبات حسب الحالة</div><div id="statusBreakdown" style="margin-top:12px"></div></div>
      </div>
    </div>
  </div>

  <!-- Settings Panel -->
  <div id="settingsPanel" style="display:none">
    <div class="card">
      <h3>⚙️ إعدادات الصيدلية</h3>
      <div class="field"><label>اسم الصيدلية</label><input class="input" id="sName" placeholder="صيدلية السلاق"></div>
      <div class="field"><label>العنوان</label><textarea class="input" id="sAddress" rows="2" placeholder="غزة، جنوب المول البندا"></textarea></div>
      <div class="field"><label>رقم الهاتف</label><input class="input" id="sPhone" placeholder="9705952224444"></div>
      <div class="field"><label>رقم واتساب</label><input class="input" id="sWA" placeholder="9705952224444"></div>
      <div class="field"><label>ساعات العمل</label><input class="input" id="sHours" placeholder="7 صباحاً - 11 مساءً"></div>
      <div class="field"><label>Telegram Bot Token (اختياري)</label><input class="input" id="sToken" placeholder="استخرج من @BotFather"></div>
      <div class="field"><label>WhatsApp Phone ID</label><input class="input" id="sPhoneId" placeholder="رقم الهوية من ميتا"></div>
      <div class="actions" style="margin-top:12px">
        <button class="btn ghost small" id="sCancel">إلغاء</button>
        <button class="btn small" id="sSave">حفظ الإعدادات</button>
      </div>
    </div>
  </div>

</main>

<!-- Modal -->
<div class="modal-bg" id="orderModal">
  <div class="modal">
    <h2 id="modalTitle">تفاصيل الطلب</h2>
    <div id="modalBody"></div>
    <div class="actions">
      <button class="btn ghost small" id="modalClose">إغلاق</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
const API = '/api';
let currentFilter = 'all';
let allOrders = [];

// ── Toast ──
function showToast(msg, type='success'){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + type;
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => t.classList.remove('show'), 3000);
}
function showToastError(msg){ showToast(msg,'error') }

// ── API Calls ──
async function api(endpoint, opts={}){
  try {
    const r = await fetch(API + endpoint, opts);
    if(!r.ok){
      const err = await r.json().catch(()=>({detail:'HTTP ' + r.status}));
      showToastError(err.detail || 'HTTP Error ' + r.status);
      return null;
    }
    return await r.json();
  } catch(e) {
    showToastError('خطأ في الاتصال: ' + e.message);
    return null;
  }
}
async function loadProducts(){ return await api('/products'); }
async function loadOrders(filter='all'){ return await api('/orders?status=' + filter); }
async function updateStatus(id, status){ return await api('/orders/' + id + '/status?status=' + status, {method:'PUT'}); }
async function replyOrder(id, msg){ return await api('/orders/' + id + '/reply', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:msg})}); }
async function sendWhatsApp(id){ return await api('/orders/' + id + '/send-whatsapp', {method:'POST'}); }
async function saveProduct(data){ return await api('/products', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); }
async function updateProduct(id, data){ return await api('/products/' + id, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); }
async function deleteProduct(id){ return await api('/products/' + id, {method:'DELETE'}); }
async function loadSettings(){ return await api('/settings'); }
async function saveSettings(data){ return await api('/settings', {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); }

// ── Stats ──
async function updateStats(){
  const [ordersData, productsData] = await Promise.all([loadOrders('all'), loadProducts()]);
  if(!ordersData || !productsData) return;
  const orders = ordersData.orders || [];
  const products = productsData.products || [];
  animateValue('statOrders', orders.length);
  const today = new Date().toDateString();
  const todayOrders = orders.filter(o => new Date(o.created_at).toDateString() === today);
  animateValue('statToday', todayOrders.length);
  animateValue('statProducts', products.length);
  const revenue = orders.reduce((sum,o) => sum + (o.total||0), 0);
  animateValue('statRevenue', revenue.toFixed(2) + ' شيكل');
}
function animateValue(id, val){
  const el = document.getElementById(id);
  el.style.opacity = '.3';
  setTimeout(() => { el.textContent = val; el.style.opacity = '1'; }, 150);
}

// ── Products ──
async function renderProductList(){
  const data = await loadProducts();
  if(!data) return;
  const products = data.products || [];
  if(!products.length){
    document.getElementById('productList').innerHTML = '<div style="text-align:center;padding:40px;color:var(--gray-400)">لا توجد منتجات بعد. أضف أول منتج!</div>';
    return;
  }
  document.getElementById('productList').innerHTML = `<div class="table-wrap"><table><thead><tr><th>الصورة</th><th>الاسم</th><th>التصنيف</th><th>الوصف</th><th>السعر</th><th>إجراءات</th></tr></thead><tbody>${products.map(p => `
    <tr>
      <td>${p.image ? `<img src="${escHtml(p.image)}" alt="" style="width:48px;height:48px;object-fit:cover;border-radius:8px" onerror="this.style.display='none'">` : '<span style="color:var(--gray-400);font-size:12px">افتراضية</span>'}</td>
      <td class="name">${escHtml(p.name)}</td>
      <td>${escHtml(p.category)}</td>
      <td style="font-size:13px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(p.desc)}</td>
      <td class="price">${p.price.toFixed(2)} شيكل</td>
      <td class="actions">
        <button class="btn ghost small edit-btn" data-id="${p.id}">تعديل</button>
        <button class="btn danger small del-btn" data-id="${p.id}">حذف</button>
      </td>
    </tr>`).join('')}</tbody></table></div>`;
  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.onclick = () => editProduct(btn.dataset.id);
  });
  document.querySelectorAll('.del-btn').forEach(btn => {
    btn.onclick = async () => {
      if(!confirm('حذف هذا المنتج؟ هذا الإجراء غير قابل للرجوع.')) return;
      const result = await deleteProduct(btn.dataset.id);
      if(result) showToast('تم الحذف');
      renderProductList();
      updateStats();
    };
  });
}
async function editProduct(id){
  const data = await loadProducts();
  const products = (data && data.products) || [];
  const p = products.find(p=>p.id==id);
  if(!p) return;
  document.getElementById('pName').value = p.name;
  document.getElementById('pCategory').value = p.category;
  document.getElementById('pPrice').value = p.price;
  document.getElementById('pDesc').value = p.desc;
  document.getElementById('pIcon').value = p.icon || 'medical';
  document.getElementById('pImage').value = p.image || '';
  document.getElementById('pSave').textContent = 'تحديث المنتج';
  document.getElementById('pSave').dataset.editId = id;
  switchPTab('add');
}
document.getElementById('pSave').onclick = async () => {
  const name = document.getElementById('pName').value.trim();
  const category = document.getElementById('pCategory').value;
  const price = parseFloat(document.getElementById('pPrice').value);
  const desc = document.getElementById('pDesc').value.trim();
  const icon = document.getElementById('pIcon').value;
  if(!name || !price || !desc){ showToastError('الاسم والسعر والوصف مطلوبين'); return; }
  const image = document.getElementById('pImage').value.trim();
  const editId = document.getElementById('pSave').dataset.editId;
  let result;
  if(editId){
    result = await updateProduct(editId, {id:parseInt(editId),name,category,desc,price,icon,image});
  } else {
    result = await saveProduct({name,category,desc,price,icon,image});
  }
  if(result){
    document.getElementById('pName').value=''; document.getElementById('pCategory').value='دواء';
    document.getElementById('pPrice').value=''; document.getElementById('pDesc').value='';
    document.getElementById('pIcon').value='pills'; document.getElementById('pImage').value=''; delete document.getElementById('pSave').dataset.editId;
    document.getElementById('pSave').textContent='حفظ المنتج';
    switchPTab('list'); renderProductList(); updateStats();
    showToast(editId ? 'تم التحديث' : 'تم الإضافة');
  }
};
document.getElementById('pCancel').onclick = () => {
  document.getElementById('pName').value=''; document.getElementById('pCategory').value='دواء';
  document.getElementById('pPrice').value=''; document.getElementById('pDesc').value='';
  document.getElementById('pIcon').value='pills'; document.getElementById('pImage').value='';
  delete document.getElementById('pSave').dataset.editId;
  document.getElementById('pSave').textContent='حفظ المنتج'; switchPTab('list');
};
document.querySelectorAll('#productTabs .tab').forEach(t => t.onclick = () => switchPTab(t.dataset.ptab));
function switchPTab(name){
  document.querySelectorAll('#productTabs .tab').forEach(t=>t.classList.remove('active'));
  document.querySelector(`[data-ptab="${name}"]`).classList.add('active');
  document.getElementById('productList').style.display = name==='list' ? '' : 'none';
  document.getElementById('productAddForm').style.display = name==='add' ? '' : 'none';
}

// ── Orders ──
async function renderOrders(filter='all'){
  const data = await loadOrders(filter);
  if(!data) return;
  const orders = data.orders || [];
  allOrders = orders;
  if(!orders.length){
    document.getElementById('ordersBody').innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--gray-400)">لا توجد طلبات.</td></tr>';
    return;
  }
  document.getElementById('ordersBody').innerHTML = orders.map(o => `
    <tr>
      <td>#${o.id}</td>
      <td class="name">${escHtml(o.customer_name||'—')}</td>
      <td>${escHtml(o.customer_phone||'—')}</td>
      <td style="font-size:12px;color:var(--green-700);font-weight:600">${escHtml(o.branch_name||'الفرع الرئيسي')}</td>
      <td style="font-size:13px;max-width:150px">${(o.items||[]).map(i=>escHtml(i.name)+' ×'+i.quantity).join('<br>')||'—'}</td>
      <td class="price">${(o.total||0).toFixed(2)}</td>
      <td><span class="badge ${o.status||'pending'}">${o.status||'pending'}</span></td>
      <td style="font-size:13px;color:var(--gray-600)">${o.created_at ? new Date(o.created_at).toLocaleString('ar-EG') : '—'}</td>
      <td class="actions">
        <button class="btn ghost small view-btn" data-id="${o.id}">تفاصيل</button>
        <select class="status-select" data-id="${o.id}">
          ${['pending','confirmed','preparing','dispatched','delivered','cancelled'].map(s=>`<option value="${s}" ${o.status===s?'selected':''}>${s==='pending'?'معلقة':s==='confirmed'?'مؤكدة':s==='preparing'?'بتحضير':s==='dispatched'?'صادر':s==='delivered'?'وصلت':'ملغية'}</option>`).join('')}
        </select>
        <button class="btn small reply-from-table-btn" data-id="${o.id}">رد</button>
      </td>
    </tr>`).join('');
  document.querySelectorAll('.status-select').forEach(sel => {
    sel.onchange = async () => {
      const id = parseInt(sel.dataset.id);
      const status = sel.value;
      const result = await updateStatus(id, status);
      if(result) showToast('تم تحديث الحالة');
      renderOrders(currentFilter); updateStats();
    };
  });
  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.onclick = async () => {
      const id = parseInt(btn.dataset.id);
      const data = await api('/orders/' + id);
      if(data && data.order) showOrderModal(data.order);
    };
  });
  document.querySelectorAll('.reply-from-table-btn').forEach(btn => {
    btn.onclick = () => {
      document.getElementById('replyOrderId').value = btn.dataset.id;
      switchTab('orders'); document.getElementById('replyMsg').focus();
    };
  });
}
document.querySelectorAll('#orderTabs .tab').forEach(tab => {
  tab.onclick = () => {
    document.querySelectorAll('#orderTabs .tab').forEach(t=>t.classList.remove('active'));
    tab.classList.add('active');
    currentFilter = tab.dataset.otab;
    renderOrders(currentFilter);
  };
});

// ── Reply ──
document.getElementById('replySend').onclick = async () => {
  const orderId = document.getElementById('replyOrderId').value.trim();
  const msg = document.getElementById('replyMsg').value.trim();
  if(!msg){ showToastError('الرسالة مطلوبة'); return; }
  if(!orderId){ showToastError('اختر طلب من الجدول'); return; }
  const result = await replyOrder(orderId, msg);
  if(result){
    document.getElementById('replyMsg').value=''; document.getElementById('replyOrderId').value='';
    showToast('تم إرسال الرد');
  } else showToastError('فشل الإرسال');
};
document.getElementById('replyCancel').onclick = () => {
  document.getElementById('replyMsg').value=''; document.getElementById('replyOrderId').value='';
};
document.getElementById('replyWhatsappBtn').onclick = async () => {
  const orderId = document.getElementById('replyOrderId').value.trim();
  if(!orderId){ showToastError('اختر طلب أولاً'); return; }
  const data = await api('/orders/' + orderId);
  if(!data || !data.order) return;
  const o = data.order;
  const settings = await loadSettings();
  const s = settings?.settings || {};
  const waNumber = s.whatsapp_number || s.phone || '9705952224444';
  const items = (o.items||[]).map(i=>`${i.name} × ${i.quantity} — ${(i.price*i.quantity).toFixed(2)} شيكل`).join(String.fromCharCode(10));
  const msg = `🚨 طلب #${o.id}\nالزبون: ${o.customer_name||'—'}\nالهاتف: ${o.customer_phone||'—'}\n\nالمنتجات:\n${items}\n\nالمجموع: ${(o.total||0).toFixed(2)} شيكل`;
  const url = `https://wa.me/${waNumber.replace(/[^0-9+]/g,'')}?text=${encodeURIComponent(msg)}`;
  window.open(url, '_blank');
  showToast('تم فتح واتساب');
};

// ── Modal ──
function showOrderModal(order){
  if(!order || !order.id) return;
  const itemsHtml = (order.items||[]).length
    ? order.items.map(i => `<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--gray-200);font-size:14px"><span>${escHtml(i.name)} × ${i.quantity}</span><span style="font-weight:700;color:var(--green-700)">${(i.price*i.quantity).toFixed(2)}</span></div>`).join('')
    : '<div style="color:var(--gray-400)">لا يوجد منتجات.</div>';
  const total = order.total||0;
  document.getElementById('modalTitle').textContent = 'الطلب #' + order.id + ' — ' + (order.status||'pending');
  document.getElementById('modalBody').innerHTML = `
    <div style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">الزبون</span><strong>${escHtml(order.customer_name||'—')}</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">الهاتف</span><strong>${escHtml(order.customer_phone||'—')}</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">الفرع</span><strong style="color:var(--green-700)">${escHtml(order.branch_name||'الفرع الرئيسي')} — ${escHtml(order.branch||'')}</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">منطقة التوصيل</span><strong>${escHtml(order.delivery_zone||'—')}</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">ملاحظات</span><strong>${escHtml(order.notes||'—')}</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">عدد المنتجات</span><strong>${order.item_count||0}</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">المجموع</span><strong style="font-size:18px;color:var(--green-700)">${total.toFixed(2)} شيكل</strong></div>
      <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="color:var(--gray-600)">الوقت</span><strong>${order.created_at ? new Date(order.created_at).toLocaleString('ar-EG') : '—'}</strong></div>
    </div>
    <div><strong>المنتجات:</strong><div style="margin-top:8px">${itemsHtml}</div></div>
    ${order.reply ? `<div style="margin-top:16px;padding:12px;background:var(--blue-soft);border-radius:8px"><strong>الرد:</strong><div style="margin-top:6px;white-space:pre-wrap">${escHtml(order.reply)}</div><div style="font-size:12px;color:var(--gray-400);margin-top:4px">في ${order.replied_at ? new Date(order.replied_at).toLocaleString('ar-EG') : ''}</div></div>` : ''}
    <div style="margin-top:16px"><button class="btn" id="modalWhatsappBtn">📱 إرسال الطلب على واتساب</button></div>
  `;
  document.getElementById('orderModal').classList.add('open');
  setTimeout(() => {
    const wb = document.getElementById('modalWhatsappBtn');
    if(wb) wb.onclick = async () => {
      const result = await sendWhatsApp(order.id);
      if(result?.status==='sent') showToast('تم الإرسال بنجاح');
      else showToastError('فشل الإرسال');
    };
  }, 50);
}
document.getElementById('modalClose').onclick = () => document.getElementById('orderModal').classList.remove('open');
document.getElementById('orderModal').onclick = (e) => { if(e.target.id==='orderModal') document.getElementById('orderModal').classList.remove('open'); };

// ── Settings ──
document.getElementById('sSave').onclick = async () => {
  const settings = {
    name: document.getElementById('sName').value.trim(),
    address: document.getElementById('sAddress').value.trim(),
    phone: document.getElementById('sPhone').value.trim(),
    whatsapp_number: document.getElementById('sWA').value.trim(),
    hours: document.getElementById('sHours').value.trim(),
    whatsapp_api_token: document.getElementById('sToken').value.trim(),
    whatsapp_phone_id: document.getElementById('sPhoneId').value.trim(),
  };
  const result = await saveSettings(settings);
  if(result) showToast('تم حفظ الإعدادات');
};
document.getElementById('sCancel').onclick = async () => {
  const data = await loadSettings();
  const s = data?.settings || {};
  document.getElementById('sName').value = s.name||'';
  document.getElementById('sAddress').value = s.address||'';
  document.getElementById('sPhone').value = s.phone||'';
  document.getElementById('sWA').value = s.whatsapp_number||'';
  document.getElementById('sHours').value = s.hours||'';
  document.getElementById('sToken').value = s.whatsapp_api_token||'';
  document.getElementById('sPhoneId').value = s.whatsapp_phone_id||'';
};

// ── Stats Panel ──
async function renderStats(){
  const [ordersData, productsData] = await Promise.all([loadOrders('all'), loadProducts()]);
  if(!ordersData || !productsData) return;
  const orders = ordersData.orders || [];
  const products = productsData.products || [];
  const productCounts = {};
  orders.forEach(o => (o.items||[]).forEach(i => { productCounts[i.name] = (productCounts[i.name]||0)+1; }));
  const top5 = Object.entries(productCounts).sort((a,b)=>b[1]-a[1]).slice(0,5);
  document.getElementById('topProducts').innerHTML = top5.length
    ? top5.map(([name,count]) => `<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--gray-200);font-size:14px"><span>${escHtml(name)}</span><strong style="color:var(--green-700)">${count} طلب</strong></div>`).join('')
    : '<div style="color:var(--gray-400)">لا يوجد بيانات بعد.</div>';
  const statusOrder = ['pending','confirmed','preparing','dispatched','delivered','cancelled'];
  const maxCount = Math.max(...statusOrder.map(s=>orders.filter(o=>o.status===s).length), 1);
  document.getElementById('statusBreakdown').innerHTML = statusOrder.map(s => {
    const count = orders.filter(o=>o.status===s).length;
    const pct = (count/maxCount*100).toFixed(0);
    const labels = {pending:'معلقة',confirmed:'مؤكدة',preparing:'بتحضير',dispatched:'صادر',delivered:'وصلت',cancelled:'ملغية'};
    return `<div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--gray-200)">
      <span class="badge ${s}" style="text-transform:capitalize;min-width:80px">${labels[s]}</span>
      <div style="flex:1"><div style="height:8px;background:var(--gray-200);border-radius:100px;overflow:hidden"><div style="height:100%;width:${pct}%;background:var(--green-700);border-radius:100px;transition:width .5s"></div></div></div>
      <strong style="font-size:14px">${count}</strong></div>`;
  }).join('');
}

// ── Tab Switching ──
function switchTab(name){
  document.querySelectorAll('[data-tab]').forEach(t=>t.classList.remove('active'));
  document.querySelector(`[data-tab="${name}"]`).classList.add('active');
  document.getElementById('productsPanel').style.display = name==='products' ? '' : 'none';
  document.getElementById('ordersPanel').style.display = name==='orders' ? '' : 'none';
  document.getElementById('statsPanel').style.display = name==='stats' ? '' : 'none';
  document.getElementById('settingsPanel').style.display = name==='settings' ? '' : 'none';
  if(name==='orders') renderOrders(currentFilter);
  if(name==='stats') renderStats();
  if(name==='settings') document.getElementById('sCancel').click();
}
document.querySelectorAll('[data-tab]').forEach(t => t.onclick = () => switchTab(t.dataset.tab));

// ── Utilities ──
function escHtml(str){
  if(!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

// ── Init ──
(async () => {
  await updateStats();
  await renderProductList();
})();
</script>
</body>
</html>""".strip()