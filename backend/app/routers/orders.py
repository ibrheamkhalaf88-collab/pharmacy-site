"""Orders router — إنشاء عام، إدارة محمية بـ admin auth."""
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import database as db
from ..deps import require_admin
from ..models import OrderIn, OrderReplyIn, OrderStatusIn
from ..services.branch import find_nearest_branch_by_phone
from ..services.whatsapp import build_order_message, send_via_cloud_api, whatsapp_link

ORDER_STATUSES = {"pending", "confirmed", "preparing", "dispatched", "delivered", "cancelled"}

# ── Rate limit بسيط (في الذاكرة): 6 طلبات / دقيقة / IP ──
_ORDER_WINDOW = 60.0
_ORDER_MAX = 6
_order_log = defaultdict(list)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _check_order_rate_limit(request: Request) -> None:
    now = time.monotonic()
    key = _client_ip(request)
    recent = [t for t in _order_log[key] if now - t < _ORDER_WINDOW]
    if len(recent) >= _ORDER_MAX:
        raise HTTPException(
            status_code=429,
            detail="طلبات كثيرة جداً — حاول مرة أخرى بعد دقيقة",
        )
    _order_log[key] = recent + [now]


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=201)
def create_order(body: OrderIn, request: Request):
    """إنشاء طلب — السعر يُحسب من قاعدة البيانات سيرفر-سايد (لا يُصدَّق من المتصفح)."""
    _check_order_rate_limit(request)
    items = []
    for item in body.items:
        product = db.get_product(item.product_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"المنتج {item.product_id} غير موجود")
        items.append({
            "product_id": product["id"],
            "name": product["name"],
            "quantity": item.quantity,
            "price": product["price"],
            "category": product["category"],
        })

    total = round(sum(i["price"] * i["quantity"] for i in items), 2)
    branch = find_nearest_branch_by_phone(body.customer_phone)

    settings = db.get_settings()
    wa_number = settings.get("whatsapp_number") or "9705952224444"

    order_data = {
        "customer_name": body.customer_name.strip(),
        "customer_phone": body.customer_phone.strip(),
        "notes": body.notes.strip(),
        "items": items,
        "total": total,
        "item_count": len(items),
        "status": "pending",
        "branch": branch.get("branch", ""),
        "branch_name": branch.get("branch_name", ""),
        "delivery_zone": branch.get("delivery_zone", ""),
    }
    order = db.create_order(order_data)

    message = build_order_message(order, settings)
    order["whatsapp_url"] = whatsapp_link(wa_number, message)
    db.update_order(order["id"], {"whatsapp_url": order["whatsapp_url"]})

    return {
        "order": order,
        "whatsapp_url": order["whatsapp_url"],
        "message": message,
        "total": total,
    }


@router.get("")
def list_orders(status: str | None = None, _: dict = Depends(require_admin)):
    orders = db.list_orders(status)
    return {"orders": orders, "count": len(orders)}


@router.get("/stats")
def order_stats(_: dict = Depends(require_admin)):
    return db.stats()


@router.get("/{order_id}")
def get_order(order_id: int, _: dict = Depends(require_admin)):
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    return {"order": order}


@router.put("/{order_id}/status")
def update_order_status(order_id: int, body: OrderStatusIn, _: dict = Depends(require_admin)):
    if body.status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"حالة غير صالحة. الحالات: {', '.join(sorted(ORDER_STATUSES))}")
    order = db.update_order(order_id, {"status": body.status})
    if not order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    return {"order": order, "status": "updated"}


@router.post("/{order_id}/reply")
def reply_to_order(order_id: int, body: OrderReplyIn, _: dict = Depends(require_admin)):
    from datetime import datetime, timezone

    order = db.update_order(order_id, {
        "reply": body.message.strip(),
        "replied_at": datetime.now(timezone.utc).isoformat(),
    })
    if not order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    return {"order": order, "status": "replied"}


@router.post("/{order_id}/send-whatsapp")
def send_order_whatsapp(order_id: int, _: dict = Depends(require_admin)):
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    settings = db.get_settings()
    result = send_via_cloud_api(order, settings)
    if result["ok"]:
        return {"status": "sent", "data": result.get("data", {})}
    # فشل API -> أعطِ رابط wa.me كحل بديل مع خطأ واضح
    raise HTTPException(status_code=502, detail=result["error"])