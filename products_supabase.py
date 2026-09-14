"""
Supabase-backed products service — بديل للـ JSON files الحالي.
يستخدم Supabase client للقراءة والكتابة.
"""
import os
from pathlib import Path
from fastapi import HTTPException

# Load env
BASE_DIR = Path(__file__).parent.parent
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def get_supabase_client(use_service: bool = False):
    """Get Supabase client"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    from supabase import create_client
    key = SUPABASE_SERVICE_KEY if use_service else SUPABASE_ANON_KEY
    return create_client(SUPABASE_URL, key)


def is_supabase_configured() -> bool:
    """Check if Supabase is configured"""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


# ═══════════════════════════════════════════════════════════════
# Products
# ═══════════════════════════════════════════════════════════════

def load_products() -> list[dict]:
    """جلب كل المنتجات من Supabase (أو JSON fallback)"""
    if is_supabase_configured():
        try:
            client = get_supabase_client()
            response = client.table("products").select("*").order("id").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"⚠️ Supabase products error: {e}, falling back to JSON")
    
    # Fallback to JSON
    return _load_products_json()


def _load_products_json() -> list[dict]:
    """Fallback: load from JSON file"""
    import json
    DATA_PATH = BASE_DIR / "backend/app/products.json"
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_products()


def get_product_by_id(product_id: int) -> dict:
    """جلب منتج بالـ ID"""
    if is_supabase_configured():
        try:
            client = get_supabase_client()
            response = client.table("products").select("*").eq("id", product_id).single().execute()
            if response.data:
                return response.data
        except Exception as e:
            print(f"⚠️ Supabase get_product error: {e}")
    
    # Fallback to JSON
    for p in _load_products_json():
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail=f"المنتج {product_id} غير موجود")


def save_products(products: list[dict]):
    """حفظ المنتجات — مع Supabase نستخدم upsert لكل منتج"""
    if is_supabase_configured():
        try:
            client = get_supabase_client(use_service=True)
            for p in products:
                data = {
                    "id": p.get("id"),
                    "name": p.get("name", ""),
                    "category": p.get("category", "أخرى"),
                    "desc": p.get("desc", ""),
                    "price": p.get("price", 0),
                    "icon": p.get("icon", "medical"),
                    "image": p.get("image"),
                }
                client.table("products").upsert(data, on_conflict="id").execute()
            return
        except Exception as e:
            print(f"⚠️ Supabase save error: {e}, falling back to JSON")
    
    # Fallback to JSON
    _save_products_json(products)


def _save_products_json(products: list[dict]):
    """Fallback: save to JSON file"""
    import json
    DATA_PATH = BASE_DIR / "backend/app/products.json"
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def add_product_image(product_id: int, image_url: str) -> dict:
    """تحديث صورة المنتج"""
    if is_supabase_configured():
        try:
            client = get_supabase_client(use_service=True)
            response = client.table("products").update({"image": image_url}).eq("id", product_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"⚠️ Supabase update image error: {e}")
    
    # Fallback
    all_products = _load_products_json()
    for p in all_products:
        if p["id"] == product_id:
            p["image"] = image_url
            _save_products_json(all_products)
            return p
    raise HTTPException(status_code=404, detail="المنتج غير موجود")


# ═══════════════════════════════════════════════════════════════
# Orders
# ═══════════════════════════════════════════════════════════════

def load_orders() -> list[dict]:
    """جلب كل الطلبات"""
    if is_supabase_configured():
        try:
            client = get_supabase_client()
            response = client.table("orders").select("*").order("created_at", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"⚠️ Supabase orders error: {e}")
    
    return _load_orders_json()


def _load_orders_json() -> list[dict]:
    import json
    ORDERS_PATH = BASE_DIR / "backend/app/orders.json"
    if ORDERS_PATH.exists():
        with open(ORDERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_orders(orders: list[dict]):
    """حفظ الطلبات"""
    if is_supabase_configured():
        try:
            client = get_supabase_client(use_service=True)
            for o in orders:
                data = {k: v for k, v in o.items() if v is not None}
                client.table("orders").upsert(data, on_conflict="id").execute()
            return
        except Exception as e:
            print(f"⚠️ Supabase save orders error: {e}")
    
    _save_orders_json(orders)


def _save_orders_json(orders: list[dict]):
    import json
    ORDERS_PATH = BASE_DIR / "backend/app/orders.json"
    with open(ORDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


def add_order(order_data: dict) -> dict:
    """إضافة طلب جديد"""
    if is_supabase_configured():
        try:
            client = get_supabase_client(use_service=True)
            data = {k: v for k, v in order_data.items() if v is not None}
            response = client.table("orders").insert(data).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"⚠️ Supabase add_order error: {e}")
    
    # Fallback
    return _add_order_json(order_data)


def _add_order_json(order_data: dict) -> dict:
    import json
    from datetime import datetime, timezone
    ORDERS_PATH = BASE_DIR / "backend/app/orders.json"
    
    if ORDERS_PATH.exists():
        with open(ORDERS_PATH, "r", encoding="utf-8") as f:
            orders = json.load(f)
    else:
        orders = []
    
    order_data["id"] = len(orders) + 1
    order_data["created_at"] = datetime.now(timezone.utc).isoformat()
    order_data["status"] = "pending"
    orders.append(order_data)
    
    with open(ORDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    
    return order_data


# ═══════════════════════════════════════════════════════════════
# Settings
# ═══════════════════════════════════════════════════════════════

def get_settings() -> dict:
    """جلب إعدادات الصيدلية"""
    if is_supabase_configured():
        try:
            client = get_supabase_client()
            response = client.table("settings").select("*").single().execute()
            if response.data:
                return response.data
        except Exception as e:
            print(f"⚠️ Supabase settings error: {e}")
    
    return _get_settings_json()


def _get_settings_json() -> dict:
    import json
    SETTINGS_PATH = BASE_DIR / "backend/app/settings.json"
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "name": "صيدلية السلاق",
        "address": "غزة، جنوب المول البندا",
        "phone": "9705952224444",
        "whatsapp_number": "9705952224444",
        "hours": "7 صباحًا - 11 مساءً",
        "whatsapp_api_token": "",
        "whatsapp_phone_id": "",
        "whatsapp_base_url": "https://graph.facebook.com/v17.0",
    }


def save_settings(settings: dict):
    """حفظ إعدادات الصيدلية"""
    if is_supabase_configured():
        try:
            client = get_supabase_client(use_service=True)
            allowed = ["name", "address", "phone", "whatsapp_number", "hours",
                       "whatsapp_api_token", "whatsapp_phone_id", "whatsapp_base_url"]
            filtered = {k: v for k, v in settings.items() if k in allowed}
            client.table("settings").update(filtered).eq("id", 1).execute()
            return
        except Exception as e:
            print(f"⚠️ Supabase save_settings error: {e}")
    
    _save_settings_json(settings)


def _save_settings_json(settings: dict):
    import json
    SETTINGS_PATH = BASE_DIR / "backend/app/settings.json"
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
# Default products (fallback)
# ═══════════════════════════════════════════════════════════════

def _default_products() -> list[dict]:
    return [
        {"id":1, "name":"باراسيتامول ٥٠٠ملغ × ٢٠ قرص", "category":"دواء", "desc":"مسكن حراري ومضاد للالتهاب الخفيف — مناسب للصداع والحمى.", "price":12.50, "icon":"pills"},
        {"id":2, "name":"إيبوبروفين ٤٠٠ملغ × ٢٠ قرص", "category":"دواء", "desc":"مسكن أقوى ومضاد التهاب — للألم العضلي والمفصلي.", "price":18.00, "icon":"pills"},
        {"id":3, "name":"أموكسيسلين ٥٠٠ملغ × ٢١ كبسولة", "category":"دواء", "desc":"مضاد حيوي لالتهابات البكتيريا — بوصفة طبية.", "price":22.00, "icon":"capsule"},
        {"id":4, "name":"سيراب السعال ذات العشبة × ١٢٠ مل", "category":"دواء", "desc":"مذيبات للبلغم ومسكنة للسعال — مناسبة للكبار والصغار.", "price":14.50, "icon":"syrup"},
        {"id":5, "name":"فيتامين D3 ١٠٠٠ وحدة × ٦٠ كبسولة", "category":"فيتامين", "desc":"يدعم صحة العظام والمناعة — الجرعة اليومية المثالية.", "price":32.00, "icon":"vitamin"},
        {"id":6, "name":"فيتامين C ١٠٠٠ملغ × ٦٠ قرص", "category":"فيتامين", "desc":"يعزز المناعة ويحمي من الفيروسات — استهلاك يومي مريح.", "price":24.00, "icon":"vitamin"},
        {"id":7, "name":"أوميغا ٣ زيت سمك × ٦٠ كبسولة", "category":"فيتامين", "desc":"يدعم صحة القلب والدماغ والشعر — مصدر نقي لأوميغا ٣.", "price":42.00, "icon":"vitamin"},
        {"id":8, "name":"حديد + فيتامين C × ٣٠ قرص", "category":"فيتامين", "desc":"مكمل الحديد — مناسب لفقر الدم والإرهاق.", "price":18.00, "icon":"vitamin"},
        {"id":9, "name":"كريم واقي من الشمس SPF50 × ٥٠ جم", "category":"بشرة", "desc":"حماية عالية من أشعة الشمس — غير دهني، مناسب للبشرة الحساسة.", "price":45.00, "icon":"sunscreen"},
        {"id":10, "name":"مرطب وجه يومي براتينزا × ٥٠ جم", "category":"بشرة", "desc":"يرطب ويهدئ البشرة الجافة — خالٍ من البارابين، غير كوميدوجين.", "price":28.00, "icon":"cream"},
        {"id":11, "name":"قنية طبية معقمة × ٣٠ قطعة", "category":"أدوات", "desc":"قنية وريدية معقمة — للتوصيل الوريدي والحقن.", "price":12.00, "icon":"medical"},
        {"id":12, "name":"جهاز قياس ضغط الدم إلكتروني", "category":"أدوات", "desc":"رقمي، شاشة كبيرة، مع بطاقة الذاكرة — دقيق ومعتمد.", "price":89.00, "icon":"medical"},
        {"id":13, "name":"مشرط طبي معقم × ٢٠ قطعة", "category":"أدوات", "desc":"مشرط معقم فردي — لفتح الجروح الصغيرة وتنظيفها.", "price":3.50, "icon":"medical"},
        {"id":14, "name":"قفازات مطاطية معقمة × ١٠٠ قطعة", "category":"أدوات", "desc":"قفازات لاتكس خالية من البودر — معقمة ومختومة.", "price":16.00, "icon":"medical"},
    ]


# ═══════════════════════════════════════════════════════════════
# WhatsApp helpers (unchanged)
# ═══════════════════════════════════════════════════════════════

from branch import find_nearest_branch_by_phone

def build_whatsapp_message(items: list[dict], customer_name: str = "",
                          branch_info: dict = None) -> str:
    """Build WhatsApp message with pharmacy name from settings + branch"""
    settings = get_settings()
    pharmacy_name = settings.get("name", "صيدلية السلاق")
    lines = [f"🚨 {pharmacy_name}", ""]

    if branch_info:
        lines.append(f"📍 الفرع: {branch_info.get('branch_name', branch_info.get('branch', 'الفرع الرئيسي'))}")
        lines.append(f"🗺️ عشان التوصيل: {branch_info.get('delivery_zone', '')}")
        lines.append("")

    lines.append("طلبية من الواتساب:")
    for item in items:
        lines.append(f"{item['name']} × {item['quantity']} — {item['price']:.2f} شيكل")
    lines.append("")
    total = sum(i['price'] * i['quantity'] for i in items)
    lines.append(f"المجموع: {total:.2f} شيكل")
    if customer_name:
        lines.append(f"الاسم: {customer_name}")
    lines.append("")
    return "\n".join(lines)


def compute_total(items: list[dict]) -> float:
    return sum(item["price"] * item["quantity"] for item in items)


PHARMACY_NUMBER = "9705952224444"