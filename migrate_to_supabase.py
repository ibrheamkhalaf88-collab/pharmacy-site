#!/usr/bin/env python3
"""
Supabase Database Migration Script
يملأ قاعدة البيانات من JSON files الحالية إلى Supabase tables.
"""
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ خطأ: SUPABASE_URL و SUPABASE_SERVICE_ROLE_KEY مطلوبان في .env")
    sys.exit(1)

from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print(f"🔗 متصل بـ Supabase: {SUPABASE_URL}")


def migrate_products():
    """نقل المنتجات من products.json إلى جدول products"""
    products_path = BASE_DIR / "backend/app/products.json"
    if not products_path.exists():
        print("⚠️  products.json غير موجود")
        return

    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"📦 نقل {len(products)} منتج...")

    for p in products:
        # Supabase يتوقع snake_case، البيانات عندنا snake_case بالفعل
        data = {
            "id": p.get("id"),
            "name": p.get("name", ""),
            "category": p.get("category", "أخرى"),
            "desc": p.get("desc", ""),
            "price": p.get("price", 0),
            "icon": p.get("icon", "medical"),
            "image": p.get("image"),
        }
        try:
            # Upsert — لو موجود يتعدل، لو مش موجود يضاف
            result = client.table("products").upsert(data, on_conflict="id").execute()
            print(f"  ✅ {p.get('name')[:30]}...")
        except Exception as e:
            print(f"  ❌ {p.get('name')}: {e}")

    print(f"✅ اكتمل نقل المنتجات")


def migrate_orders():
    """نقل الطلبات من orders.json إلى جدول orders"""
    orders_path = BASE_DIR / "backend/app/orders.json"
    if not orders_path.exists():
        print("⚠️  orders.json غير موجود")
        return

    with open(orders_path, "r", encoding="utf-8") as f:
        orders = json.load(f)

    print(f"📋 نقل {len(orders)} طلب...")

    for o in orders:
        data = {
            "id": o.get("id"),
            "customer_name": o.get("customer_name", ""),
            "customer_phone": o.get("customer_phone", ""),
            "items": o.get("items", []),
            "total": o.get("total", 0),
            "item_count": o.get("item_count", 0),
            "status": o.get("status", "pending"),
            "notes": o.get("notes", ""),
            "reply": o.get("reply"),
            "replied_at": o.get("replied_at"),
            "whatsapp_url": o.get("whatsapp_url"),
            "message": o.get("message"),
            "branch": o.get("branch", ""),
            "branch_name": o.get("branch_name", ""),
            "delivery_zone": o.get("delivery_zone", ""),
            "created_at": o.get("created_at"),
        }
        # إزالة None values
        data = {k: v for k, v in data.items() if v is not None}

        try:
            result = client.table("orders").upsert(data, on_conflict="id").execute()
            print(f"  ✅ طلب #{o.get('id')}")
        except Exception as e:
            print(f"  ❌ طلب #{o.get('id')}: {e}")

    print(f"✅ اكتمل نقل الطلبات")


def migrate_settings():
    """نقل الإعدادات من settings.json إلى جدول settings"""
    settings_path = BASE_DIR / "backend/app/settings.json"
    if not settings_path.exists():
        print("⚠️  settings.json غير موجود")
        return

    with open(settings_path, "r", encoding="utf-8") as f:
        s = json.load(f)

    print("⚙️  نقل الإعدادات...")

    data = {
        "id": 1,
        "name": s.get("name", "صيدلية السلاق"),
        "address": s.get("address", ""),
        "phone": s.get("phone", ""),
        "whatsapp_number": s.get("whatsapp_number", ""),
        "hours": s.get("hours", ""),
        "whatsapp_api_token": s.get("whatsapp_api_token", ""),
        "whatsapp_phone_id": s.get("whatsapp_phone_id", ""),
        "whatsapp_base_url": s.get("whatsapp_base_url", "https://graph.facebook.com/v17.0"),
    }

    try:
        result = client.table("settings").upsert(data, on_conflict="id").execute()
        print(f"  ✅ إعدادات الصيدلية")
    except Exception as e:
        print(f"  ❌ إعدادات: {e}")

    print(f"✅ اكتمل نقل الإعدادات")


def verify_migration():
    """التحقق من البيانات المنقولة"""
    print("\n🔍 التحقق من البيانات المنقولة...")
    
    try:
        products = client.table("products").select("id, name, category, price").execute()
        print(f"📦 منتجات في Supabase: {len(products.data)}")
        
        orders = client.table("orders").select("id, customer_name, status, branch").execute()
        print(f"📋 طلبات في Supabase: {len(orders.data)}")
        
        settings = client.table("settings").select("*").execute()
        if settings.data:
            s = settings.data[0]
            print(f"⚙️  الإعدادات: {s.get('name')} — واتساب: {s.get('whatsapp_number')}")
            
    except Exception as e:
        print(f"❌ خطأ في التحقق: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Supabase Migration — صيدلية السلاق")
    print("=" * 50)
    
    migrate_products()
    migrate_orders()
    migrate_settings()
    verify_migration()
    
    print("\n🎉 اكتمل النقل بنجاح!")
    print("يمكنك الآن استخدام Supabase في الـ backend.")