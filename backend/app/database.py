"""Database — كل الوصول لقاعدة بيانات Supabase (Postgres) عبر service role key."""
from typing import Any

from supabase import Client, create_client

from .config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL

_client: Client | None = None


def db() -> Client:
    global _client
    if _client is None:
        if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
            raise RuntimeError("Supabase غير مُعد. تأكد من SUPABASE_URL و SUPABASE_SERVICE_ROLE_KEY في .env")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ═════════ PRODUCERS ═════════
def _product_row(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("name", ""),
        "category": row.get("category", "أخرى"),
        "desc": row.get("desc", ""),
        "price": _num(row.get("price")),
        "icon": row.get("icon", "medical"),
        "image": row.get("image") or "",
        "active": bool(row.get("active", True)),
    }


def list_products(category: str | None = None) -> list[dict]:
    q = db().table("products").select("*").order("id")
    if category and category != "all":
        q = q.eq("category", category)
    rows = q.execute().data or []
    return [_product_row(r) for r in rows]


def get_product(product_id: int) -> dict | None:
    rows = db().table("products").select("*").eq("id", product_id).execute().data or []
    return _product_row(rows[0]) if rows else None


def create_product(data: dict) -> dict:
    rows = db().table("products").insert(data).execute().data or []
    return _product_row(rows[0])


def update_product(product_id: int, data: dict) -> dict | None:
    rows = db().table("products").update(data).eq("id", product_id).execute().data or []
    return _product_row(rows[0]) if rows else None


def delete_product(product_id: int) -> bool:
    rows = db().table("products").delete().eq("id", product_id).execute().data or []
    return bool(rows)


# ═════════ ORDERS ═════════
def _order_row(row: dict) -> dict:
    items = row.get("items") or []
    total = _num(row.get("total"))
    return {
        "id": row.get("id"),
        "customer_name": row.get("customer_name", "") or "",
        "customer_phone": row.get("customer_phone", "") or "",
        "notes": row.get("notes", "") or "",
        "items": items if isinstance(items, list) else [],
        "total": total,
        "item_count": int(row.get("item_count") or 0),
        "status": row.get("status", "pending"),
        "reply": row.get("reply") or "",
        "replied_at": row.get("replied_at"),
        "whatsapp_url": row.get("whatsapp_url") or "",
        "branch": row.get("branch") or "",
        "branch_name": row.get("branch_name") or "",
        "delivery_zone": row.get("delivery_zone") or "",
        "created_at": row.get("created_at"),
    }


def create_order(data: dict) -> dict:
    rows = db().table("orders").insert(data).execute().data or []
    return _order_row(rows[0])


def list_orders(status: str | None = None) -> list[dict]:
    q = db().table("orders").select("*").order("created_at", desc=True)
    if status and status != "all":
        q = q.eq("status", status)
    rows = q.execute().data or []
    return [_order_row(r) for r in rows]


def get_order(order_id: int) -> dict | None:
    rows = db().table("orders").select("*").eq("id", order_id).execute().data or []
    return _order_row(rows[0]) if rows else None


def update_order(order_id: int, patch: dict) -> dict | None:
    rows = db().table("orders").update(patch).eq("id", order_id).execute().data or []
    return _order_row(rows[0]) if rows else None


# ═════════ SETTINGS ═════════
def _settings_row(row: dict) -> dict:
    return {
        "name": row.get("name", "صيدلية السلاق"),
        "address": row.get("address", "") or "",
        "phone": row.get("phone", "") or "",
        "whatsapp_number": row.get("whatsapp_number", "") or "",
        "hours": row.get("hours", "") or "",
        "whatsapp_api_token": row.get("whatsapp_api_token") or "",
        "whatsapp_phone_id": row.get("whatsapp_phone_id") or "",
        "whatsapp_base_url": row.get("whatsapp_base_url") or "https://graph.facebook.com/v17.0",
    }


def get_settings() -> dict:
    rows = db().table("settings").select("*").eq("id", 1).execute().data or []
    return _settings_row(rows[0]) if rows else {}


def update_settings(patch: dict) -> dict:
    rows = db().table("settings").update(patch).eq("id", 1).execute().data or []
    if not rows:
        # إن لم يوجد صف، أنشئه بالبيانات الافتراضية
        base = {
            "id": 1,
            "name": "صيدلية السلاق",
            "address": "غزة، جنوب المول البندا",
            "phone": "9705952224444",
            "whatsapp_number": "9705952224444",
            "hours": "7 صباحًا - 11 مساءً",
            "whatsapp_api_token": "",
            "whatsapp_phone_id": "",
            "whatsapp_base_url": "https://graph.facebook.com/v17.0",
        }
        base.update(patch)
        rows = db().table("settings").insert(base).execute().data or []
    return _settings_row(rows[0])


def stats() -> dict:
    """إحصائيات بسيطة للوحة التحكم."""
    orders = list_orders()
    products = list_products()
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).date().isoformat()
    today_orders = [o for o in orders if (o.get("created_at") or "").startswith(today)]
    revenue = sum(o.get("total", 0) for o in orders if o.get("status") != "cancelled")
    return {
        "total_orders": len(orders),
        "today_orders": len(today_orders),
        "active_products": len(products),
        "total_revenue": round(revenue, 2),
    }