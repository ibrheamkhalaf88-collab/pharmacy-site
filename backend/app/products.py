"""
المنتجات والمنطق التجاري — حفظ في ملف JSON عشان يقرأه الفرونت إند examiner.
"""
import json
from pathlib import Path
from fastapi import HTTPException

DATA_PATH = Path(__file__).parent / "products.json"

def load_products() -> list[dict]:
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_products()

def save_products(products: list[dict]):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

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

def get_product_by_id(product_id: int) -> dict:
    for p in load_products():
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail=f"المنتج {product_id} غير موجود")

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

def add_product_image(product_id: int, image_url: str) -> dict:
    """Set or update product image URL"""
    all_products = load_products()
    for p in all_products:
        if p["id"] == product_id:
            p["image"] = image_url
            save_products(all_products)
            return p
    raise HTTPException(status_code=404, detail="المنتج غير موجود")

PHARMACY_NUMBER = "9705952224444"

# ── Orders storage ──
ORDERS_PATH = Path(__file__).parent / "orders.json"

def load_orders() -> list[dict]:
    if ORDERS_PATH.exists():
        with open(ORDERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_orders(orders: list[dict]):
    with open(ORDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def add_order(order_data: dict) -> dict:
    orders = load_orders()
    order_data["id"] = len(orders) + 1
    from datetime import datetime, timezone
    order_data["created_at"] = datetime.now(timezone.utc).isoformat()
    order_data["status"] = "pending"
    orders.append(order_data)
    save_orders(orders)
    return order_data

# ── Settings ──
SETTINGS_PATH = Path(__file__).parent / "settings.json"

def get_settings() -> dict:
    """Get pharmacy settings from JSON file"""
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
    """Save pharmacy settings to JSON file"""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
