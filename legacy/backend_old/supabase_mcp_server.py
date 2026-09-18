"""
صيدلية السلاق — Supabase MCP Server
يتعامل مع Supabase عبر REST API مباشرة (بدون supabase-py).
كل الأدوات متاحة عبر stdio MCP protocol.

الأدوات المتاحة:
  - health: فحص الاتصال
  - list_products: جلب المنتجات (بدعم filter بالفئة)
  - get_product: جلب منتج بالـ ID
  - create_product: إضافة منتج
  - update_product: تحديث منتج
  - delete_product: حذف منتج
  - list_orders: جلب الطلبات (بدعم filter بالحالة)
  - get_order: جلب طلب بالـ ID
  - create_order: إنشاء طلب
  - update_order_status: تحديث حالة الطلب
  - add_order_reply: إضافة رد على الطلب
  - get_settings: جلب الإعدادات
  - update_settings: تحديث الإعدادات
  - get_pharmacy_info: معلومات الصيدلية السريعة
  - migrate_json: نقل البيانات من JSON إلى Supabase
"""
import json
import sys
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ── Environment ──
ENV_PATH = Path(__file__).parent.parent / ".env"
if ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(str(ENV_PATH))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

HEADERS = {
    "Authorization": f"Bearer {SERVICE_KEY}",
    "apikey": SERVICE_KEY,
    "Content-Type": "application/json",
}
BASE = f"{SUPABASE_URL}/rest/v1"


def _req(method: str, path: str, body: dict = None, params: dict = None) -> dict:
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    data = json.dumps(body).encode("utf-8") if body else None
    req = Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "data": json.loads(raw) if raw else None, "status": resp.status}
    except HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            detail = json.loads(raw)
        except Exception:
            detail = raw
        return {"ok": False, "error": detail, "status": e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Tools ──

def tool_health() -> dict:
    if not SUPABASE_URL or not SERVICE_KEY:
        return {"ok": False, "error": "Supabase not configured"}
    r = _req("GET", "/products", params={"select": "*", "limit": "1"})
    return {"ok": r.get("ok", False), "connected": r.get("ok", False)}


def tool_list_products(category: str = None, limit: int = 100, offset: int = 0) -> dict:
    params = {"select": "*"}
    if category and category != "all":
        params["category"] = f"eq.{category}"
    r = _req("GET", "/products", params=params)
    if r.get("ok"):
        data = r["data"] or []
        return {"products": data, "count": len(data), "total": len(data)}
    return {"error": r.get("error"), "products": []}


def tool_get_product(product_id: int) -> dict:
    r = _req("GET", f"/products?id=eq.{product_id}&select=*")
    data = r.get("data") or []
    return {"product": data[0] if data else None}


def tool_create_product(name: str, category: str, desc: str, price: float, icon: str = "medical", image: str = None) -> dict:
    r = _req("POST", "/products", body={"name": name, "category": category, "desc": desc, "price": price, "icon": icon, "image": image or ""})
    return {"product": r.get("data"), "status": "created" if r.get("ok") else "error"}


def tool_update_product(product_id: int, name: str = None, category: str = None, desc: str = None, price: float = None, icon: str = None, image: str = None) -> dict:
    updates = {}
    if name is not None: updates["name"] = name
    if category is not None: updates["category"] = category
    if desc is not None: updates["desc"] = desc
    if price is not None: updates["price"] = price
    if icon is not None: updates["icon"] = icon
    if image is not None: updates["image"] = image
    if not updates:
        return {"error": "No values to update"}
    r = _req("PATCH", f"/products?id=eq.{product_id}", body=updates)
    return {"product": r.get("data"), "status": "updated" if r.get("ok") else "error"}


def tool_delete_product(product_id: int) -> dict:
    r = _req("DELETE", f"/products?id=eq.{product_id}")
    return {"status": "deleted" if r.get("ok") else "error", "deleted_id": product_id}


def tool_list_orders(status: str = None, limit: int = 100, offset: int = 0) -> dict:
    params = {"select": "*"}
    if status and status != "all":
        params["status"] = f"eq.{status}"
    r = _req("GET", "/orders", params=params)
    if r.get("ok"):
        data = r["data"] or []
        return {"orders": data, "count": len(data), "total": len(data)}
    return {"error": r.get("error"), "orders": []}


def tool_get_order(order_id: int) -> dict:
    r = _req("GET", f"/orders?id=eq.{order_id}&select=*")
    data = r.get("data") or []
    return {"order": data[0] if data else None}


def tool_create_order(customer_name: str, customer_phone: str, items: list, notes: str = None) -> dict:
    total = 0.0
    order_items = []
    for item in items:
        pid = item.get("product_id")
        qty = item.get("quantity", 1)
        prod_r = _req("GET", f"/products?id=eq.{pid}&select=*")
        prod = (prod_r.get("data") or [{}])[0]
        item_total = float(prod.get("price", 0)) * qty
        total += item_total
        order_items.append({"product_id": pid, "name": prod.get("name", ""), "quantity": qty, "price": prod.get("price", 0), "category": prod.get("category", "")})
    r = _req("POST", "/orders", body={
        "customer_name": customer_name or "", "customer_phone": customer_phone or "",
        "items": order_items, "total": round(total, 2), "item_count": len(order_items),
        "notes": notes or "", "status": "pending", "whatsapp_url": ""})
    return {"order": r.get("data"), "status": "created" if r.get("ok") else "error", "total": round(total, 2)}


def tool_update_order_status(order_id: int, status: str) -> dict:
    valid = ["pending", "confirmed", "preparing", "dispatched", "delivered", "cancelled"]
    if status not in valid:
        return {"error": f"Invalid status. Valid: {', '.join(valid)}"}
    r = _req("PATCH", f"/orders?id=eq.{order_id}", body={"status": status})
    return {"order": r.get("data"), "status": "updated" if r.get("ok") else "error"}


def tool_add_order_reply(order_id: int, message: str) -> dict:
    r = _req("PATCH", f"/orders?id=eq.{order_id}", body={"reply": message})
    return {"order": r.get("data"), "status": "replied" if r.get("ok") else "error"}


def tool_get_settings() -> dict:
    r = _req("GET", "/settings?select=*")
    data = r.get("data") or []
    return {"settings": data[0] if data else {}}


def tool_update_settings(settings: dict) -> dict:
    allowed = ["name", "address", "phone", "whatsapp_number", "hours", "whatsapp_api_token", "whatsapp_phone_id", "whatsapp_base_url"]
    filtered = {k: v for k, v in settings.items() if k in allowed}
    r = _req("PATCH", "/settings?id=eq.1", body=filtered)
    return {"settings": r.get("data"), "status": "updated" if r.get("ok") else "error"}


def tool_get_pharmacy_info() -> dict:
    r = _req("GET", "/settings?select=name,address,phone,whatsapp_number,hours")
    data = r.get("data") or []
    return {"info": data[0] if data else {}}


def tool_migrate_json() -> dict:
    """Migrate products.json, orders.json, settings.json to Supabase"""
    base = Path(__file__).parent.parent
    results = {}
    # Products
    try:
        products = json.loads((base / "products.json").read_text(encoding="utf-8"))
        _req("DELETE", "/products")
        n = 0
        for p in products:
            pr = _req("POST", "/products", body={"name": p.get("name", ""), "category": p.get("category", "أخرى"), "desc": p.get("desc", ""), "price": float(p.get("price", 0)), "icon": p.get("icon", "medical"), "image": p.get("image", "")})
            if pr.get("ok"): n += 1
        results["products"] = f"{n}/{len(products)}"
    except Exception as e:
        results["products"] = f"error: {e}"
    # Orders
    try:
        orders = json.loads((base / "orders.json").read_text(encoding="utf-8"))
        _req("DELETE", "/orders")
        n = 0
        for o in orders:
            items = o.get("items", [])
            total = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in items)
            ords = _req("POST", "/orders", body={"customer_name": o.get("customer_name", ""), "customer_phone": o.get("customer_phone", ""), "items": items, "total": round(total, 2), "item_count": len(items), "status": o.get("status", "pending"), "notes": o.get("notes", ""), "reply": o.get("reply", ""), "whatsapp_url": o.get("whatsapp_url", "")})
            if ords.get("ok"): n += 1
        results["orders"] = f"{n}/{len(orders)}"
    except Exception as e:
        results["orders"] = f"error: {e}"
    # Settings
    try:
        settings = json.loads((base / "settings.json").read_text(encoding="utf-8"))
        _req("DELETE", "/settings")
        if settings:
            s = settings[0]
            st = _req("POST", "/settings", body={"name": s.get("name", "صيدلية السلاق"), "address": s.get("address", ""), "phone": s.get("phone", ""), "whatsapp_number": s.get("whatsapp_number", "9705952224444"), "hours": s.get("hours", "7 صباحا - 11 مساء")})
            results["settings"] = "1 row" if st.get("ok") else "error"
        else:
            results["settings"] = "no data"
    except Exception as e:
        results["settings"] = f"error: {e}"
    return {"migration": "done", "details": results}


# ── Registry ──
TOOL_REGISTRY = {
    "health": tool_health,
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
    "migrate_json": tool_migrate_json,
}


def handle_request(request: dict) -> dict:
    tool_name = request.get("tool")
    if not tool_name:
        return {"error": "No tool specified"}
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool '{tool_name}'. Available: {list(TOOL_REGISTRY.keys())}"}
    params = request.get("params", {})
    try:
        result = TOOL_REGISTRY[tool_name](**params)
        return result
    except TypeError as e:
        return {"error": f"Bad params: {e}"}
    except Exception as e:
        return {"error": str(e)}


def run_mcp_server():
    print("🔌 Supabase MCP Server (REST) ready...", file=sys.stderr, flush=True)
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