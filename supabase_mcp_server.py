"""
MCP Server للتكامل مع Supabase.
يوفر أدوات للـ Hermes Agent للتعامل مع قاعدة البيانات: قراءة المنتجات، إدارة الطلبات، الإعدادات.
يعتمد على supabase-py ويعمل كـ stdio MCP server.
"""
import json
import sys
import os
from pathlib import Path
from typing import Any

# ── تحميل البيئة ──
ENV_PATH = Path(__file__).parent.parent / ".env"
if ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(str(ENV_PATH))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

# ── تحميل Supabase client ──
try:
    from supabase import create_client, Client
    _client: Client | None = None
    _service_client: Client | None = None

    def get_client(use_service: bool = False) -> Client:
        """Get Supabase client (anon or service role)"""
        global _client, _service_client
        if use_service:
            if _service_client is None and SUPABASE_SERVICE_ROLE_KEY:
                _service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            return _service_client
        if _client is None:
            _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return _client

    def is_configured() -> bool:
        return bool(SUPABASE_URL and SUPABASE_ANON_KEY)

    def check_connection() -> dict[str, Any]:
        """Test Supabase connection"""
        if not is_configured():
            return {"ok": False, "error": "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"}
        try:
            client = get_client()
            # Try a simple select to verify connection
            response = client.table("products").select("count").limit(1).execute()
            return {"ok": True, "table_count": response.count if hasattr(response, 'count') else 'unknown'}
        except Exception as e:
            return {"ok": False, "error": str(e)}

except ImportError:
    get_client = None
    is_configured = lambda: False
    check_connection = lambda: {"ok": False, "error": "supabase-py not installed. Run: pip install supabase"}


# ═══════════════════════════════════════════════════════════════
# MCP Server Tools
# ═══════════════════════════════════════════════════════════════

def tool_list_products(category: str = None, limit: int = 100, offset: int = 0) -> dict:
    """جلب قائمة المنتجات من Supabase"""
    if not is_configured():
        return {"error": "Supabase not configured", "products": []}
    try:
        client = get_client()
        query = client.table("products").select("*").order("id", ascending=True).range(offset, offset + limit - 1)
        if category and category != "all":
            query = query.eq("category", category)
        response = query.execute()
        products = response.data if response.data else []
        return {"products": products, "count": len(products), "total": response.count if hasattr(response, 'count') else len(products)}
    except Exception as e:
        return {"error": str(e), "products": []}


def tool_get_product(product_id: int) -> dict:
    """جلب منتج محدد بالـ ID"""
    if not is_configured():
        return {"error": "Supabase not configured", "product": None}
    try:
        client = get_client()
        response = client.table("products").select("*").eq("id", product_id).single().execute()
        return {"product": response.data if response.data else None}
    except Exception as e:
        return {"error": str(e), "product": None}


def tool_create_product(name: str, category: str, desc: str, price: float, icon: str = "medical", image: str = None) -> dict:
    """إضافة منتج جديد"""
    if not is_configured():
        return {"error": "Supabase not configured", "product": None, "status": "error"}
    try:
        client = get_client(use_service=True)  # Service role for write operations
        response = client.table("products").insert({
            "name": name,
            "category": category,
            "desc": desc,
            "price": price,
            "icon": icon,
            "image": image,
        }).execute()
        product = response.data[0] if response.data else None
        return {"product": product, "status": "created" if product else "error"}
    except Exception as e:
        return {"error": str(e), "product": None, "status": "error"}


def tool_update_product(product_id: int, name: str = None, category: str = None,
                       desc: str = None, price: float = None, icon: str = None,
                       image: str = None) -> dict:
    """تحديث منتج موجود"""
    if not is_configured():
        return {"error": "Supabase not configured", "product": None, "status": "error"}
    try:
        client = get_client(use_service=True)
        updates = {}
        if name is not None: updates["name"] = name
        if category is not None: updates["category"] = category
        if desc is not None: updates["desc"] = desc
        if price is not None: updates["price"] = price
        if icon is not None: updates["icon"] = icon
        if image is not None: updates["image"] = image
        if not updates:
            return {"error": "لا توجد قيم للتحديث", "product": None, "status": "error"}
        response = client.table("products").update(updates).eq("id", product_id).execute()
        product = response.data[0] if response.data else None
        return {"product": product, "status": "updated" if product else "not_found"}
    except Exception as e:
        return {"error": str(e), "product": None, "status": "error"}


def tool_delete_product(product_id: int) -> dict:
    """حذف منتج"""
    if not is_configured():
        return {"error": "Supabase not configured", "status": "error"}
    try:
        client = get_client(use_service=True)
        response = client.table("products").delete().eq("id", product_id).execute()
        return {"status": "deleted", "deleted_id": product_id}
    except Exception as e:
        return {"error": str(e), "status": "error"}


def tool_list_orders(status: str = None, limit: int = 100, offset: int = 0) -> dict:
    """جلب قائمة الطلبات"""
    if not is_configured():
        return {"error": "Supabase not configured", "orders": []}
    try:
        client = get_client()
        query = client.table("orders").select("*").order("created_at", ascending=False).range(offset, offset + limit - 1)
        if status and status != "all":
            query = query.eq("status", status)
        response = query.execute()
        orders = response.data if response.data else []
        return {"orders": orders, "count": len(orders), "total": response.count if hasattr(response, 'count') else len(orders)}
    except Exception as e:
        return {"error": str(e), "orders": []}


def tool_get_order(order_id: int) -> dict:
    """جلب طلب محدد"""
    if not is_configured():
        return {"error": "Supabase not configured", "order": None}
    try:
        client = get_client()
        response = client.table("orders").select("*").eq("id", order_id).single().execute()
        return {"order": response.data if response.data else None}
    except Exception as e:
        return {"error": str(e), "order": None}


def tool_create_order(customer_name: str, customer_phone: str, items: list,
                      notes: str = None) -> dict:
    """إنشاء طلب جديد (يدوي من MCP — عادةً الـ API هو اللي يخلق الطلب)

    items: list of dicts with product_id and quantity
    مثال: [{"product_id": 1, "quantity": 2}, {"product_id": 5, "quantity": 1}]
    """
    if not is_configured():
        return {"error": "Supabase not configured", "order": None, "status": "error"}
    try:
        client = get_client(use_service=True)
        # Fetch products to compute total
        product_ids = [item.get("product_id") for item in items if item.get("product_id")]
        products_response = client.table("products").select("*").in_("id", product_ids).execute()
        products = {p["id"]: p for p in (products_response.data or [])}
        order_items_data = []
        total = 0.0
        for item in items:
            pid = item.get("product_id")
            qty = item.get("quantity", 1)
            product = products.get(pid)
            if not product:
                continue
            item_total = product["price"] * qty
            total += item_total
            order_items_data.append({
                "product_id": pid,
                "name": product["name"],
                "quantity": qty,
                "price": product["price"],
                "category": product["category"],
            })
        response = client.table("orders").insert({
            "customer_name": customer_name or "",
            "customer_phone": customer_phone or "",
            "items": order_items_data,
            "total": round(total, 2),
            "item_count": len(order_items_data),
            "notes": notes or "",
            "status": "pending",
        }).execute()
        order = response.data[0] if response.data else None
        return {"order": order, "status": "created" if order else "error", "total": round(total, 2)}
    except Exception as e:
        return {"error": str(e), "order": None, "status": "error"}


def tool_update_order_status(order_id: int, status: str) -> dict:
    """تحديث حالة الطلب"""
    valid_statuses = ["pending", "confirmed", "preparing", "dispatched", "delivered", "cancelled"]
    if status not in valid_statuses:
        return {"error": f"حالة غير صالحة. الحالات: {', '.join(valid_statuses)}", "order": None}
    if not is_configured():
        return {"error": "Supabase not configured", "order": None}
    try:
        client = get_client(use_service=True)
        response = client.table("orders").update({"status": status}).eq("id", order_id).execute()
        order = response.data[0] if response.data else None
        return {"order": order, "status": "updated" if order else "not_found"}
    except Exception as e:
        return {"error": str(e), "order": None}


def tool_add_order_reply(order_id: int, message: str) -> dict:
    """إضافة رد على طلب"""
    if not is_configured():
        return {"error": "Supabase not configured", "order": None}
    try:
        from datetime import datetime, timezone
        client = get_client(use_service=True)
        response = client.table("orders").update({
            "reply": message,
            "replied_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", order_id).execute()
        order = response.data[0] if response.data else None
        return {"order": order, "status": "replied" if order else "not_found"}
    except Exception as e:
        return {"error": str(e), "order": None}


def tool_get_settings() -> dict:
    """جلب إعدادات الصيدلية"""
    if not is_configured():
        return {"error": "Supabase not configured", "settings": None}
    try:
        client = get_client()
        response = client.table("settings").select("*").single().execute()
        return {"settings": response.data if response.data else {}}
    except Exception as e:
        return {"error": str(e), "settings": None}


def tool_update_settings(settings: dict) -> dict:
    """تحديث إعدادات الصيدلية"""
    if not is_configured():
        return {"error": "Supabase not configured", "settings": None, "status": "error"}
    try:
        client = get_client(use_service=True)
        allowed = ["name", "address", "phone", "whatsapp_number", "hours",
                   "whatsapp_api_token", "whatsapp_phone_id", "whatsapp_base_url"]
        filtered = {k: v for k, v in settings.items() if k in allowed}
        # Update all settings rows (should be just one)
        response = client.table("settings").update(filtered).execute()
        updated = response.data[0] if response.data else None
        return {"settings": updated, "status": "updated" if updated else "error"}
    except Exception as e:
        return {"error": str(e), "settings": None, "status": "error"}


def tool_get_pharmacy_info() -> dict:
    """جلب معلومات الصيدلية (name, address, phone, whatsapp_number) بسرعة"""
    if not is_configured():
        return {"error": "Supabase not configured", "info": None}
    try:
        client = get_client()
        response = client.table("settings").select("name, address, phone, whatsapp_number, hours").single().execute()
        return {"info": response.data if response.data else {}}
    except Exception as e:
        return {"error": str(e), "info": None}


def tool_health() -> dict:
    """فحص صحة الاتصال بـ Supabase"""
    if not is_configured():
        return {"ok": False, "error": "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"}
    try:
        result = check_connection()
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# MCP Server Entry Point (stdio-based)
# ═══════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    "list_products": tool_list_products,
    "get_product": tool_get_product,
    "create_product": tool_create_product,
    "update_product": tool_update_product,
    "delete_product": tool_delete_product,
    "list_orders": tool_list_orders,
    "get_order": tool_get_order,
    "create_order": tool_create_order,
    "update_order_status": tool_update_order_status,
    "add_order_reply": tool_add_order_reply,
    "get_settings": tool_get_settings,
    "update_settings": tool_update_settings,
    "get_pharmacy_info": tool_get_pharmacy_info,
    "health": tool_health,
}


def handle_request(request: dict) -> dict:
    """Handle a single MCP tool call request"""
    tool_name = request.get("tool")
    if not tool_name:
        return {"error": "لا يوجد أداة محددة (tool)"}
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"الأداة '{tool_name}' غير موجودة. المتاحة: {list(TOOL_REGISTRY.keys())}"}
    params = request.get("params", {})
    try:
        result = TOOL_REGISTRY[tool_name](**params)
        return result
    except TypeError as e:
        return {"error": f"خطأ في المعاملات: {e}. المعاملات المتاحة: {list(TOOL_REGISTRY[tool_name].__code__.co_varnames[:TOOL_REGISTRY[tool_name].__code__.co_argcount])}"}
    except Exception as e:
        return {"error": f"خطأ غير متوقع: {e}"}


def run_mcp_server():
    """تشغيل MCP server عبر stdio"""
    import sys
    print("🔌 Supabase MCP Server جاهز...", file=sys.stderr, flush=True)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response, ensure_ascii=False), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}), flush=True)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    run_mcp_server()
