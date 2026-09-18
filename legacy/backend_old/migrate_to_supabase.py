#!/usr/bin/env python3
"""مهاجر صيدلية السلاق: JSON → Supabase (ينتظر الجداول)"""
import json, os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

url = os.getenv("SUPABASE_URL").rstrip("/")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
sb: Client = create_client(url, key)

def load_json(name):
    p = BASE_DIR / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def migrate():
    print("=== مهاجر JSON → Supabase ===\n")
    products = load_json("products.json")
    orders = load_json("orders.json")
    settings = load_json("settings.json")
    print(f"JSON: products={len(products)}, orders={len(orders)}, settings={len(settings)}\n")

    # Products
    print("مهاجر المنتجات...")
    sb.table("products").delete().execute()
    n = 0
    for p in products:
        try:
            sb.table("products").insert({
                "name": p.get("name",""), "category": p.get("category","أخرى"),
                "desc": p.get("desc",""), "price": float(p.get("price",0)),
                "icon": p.get("icon","medical"), "image": p.get("image",""),
            }).execute()
            n += 1
        except Exception as e:
            print(f"  خطأ: {e}")
    print(f"  ✅ {n}/{len(products)}")

    # Orders
    print("مهاجر الطلبات...")
    sb.table("orders").delete().execute()
    n = 0
    for o in orders:
        try:
            sb.table("orders").insert({
                "customer_name": o.get("customer_name",""),
                "customer_phone": o.get("customer_phone",""),
                "items": json.dumps(o.get("items",[]), ensure_ascii=False),
                "total": float(o.get("total",0)), "item_count": o.get("item_count",0),
                "status": o.get("status","pending"), "notes": o.get("notes",""),
                "reply": o.get("reply",""), "replied_at": o.get("replied_at"),
                "whatsapp_url": o.get("whatsapp_url",""),
            }).execute()
            n += 1
        except Exception as e:
            print(f"  خطأ: {e}")
    print(f"  ✅ {n}/{len(orders)}")

    # Settings
    print("مهاجر الإعدادات...")
    sb.table("settings").delete().execute()
    if settings:
        s = settings[0]
        sb.table("settings").insert({
            "name": s.get("name","صيدلية السلاق"), "address": s.get("address",""),
            "phone": s.get("phone",""), "whatsapp_number": s.get("whatsapp_number",""),
            "hours": s.get("hours",""), "whatsapp_api_token": s.get("whatsapp_api_token",""),
            "whatsapp_phone_id": s.get("whatsapp_phone_id",""),
            "whatsapp_base_url": s.get("whatsapp_base_url",""),
        }).execute()
        print("  ✅ 1 row")
    else:
        print("  ⚠️ لا توجد إعدادات")

    print("\n✅ تم النقل بنجاح")

if __name__ == "__main__":
    migrate()