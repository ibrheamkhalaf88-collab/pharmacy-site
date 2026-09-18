"""WhatsApp service — بناء رسالة الطلب + إرسال تلقائي عبر WhatsApp Cloud API."""
from urllib.parse import quote

import httpx


def build_order_message(order: dict, settings: dict) -> str:
    pharmacy_name = settings.get("name") or "صيدلية السلاق"
    lines = [f"🚨 {pharmacy_name}", ""]

    branch = order.get("branch") or ""
    branch_name = order.get("branch_name") or ""
    zone = order.get("delivery_zone") or ""
    if branch_name or zone:
        lines.append(f"📍 الفرع: {branch_name or branch or 'الفرع الرئيسي'}")
        if zone:
            lines.append(f"🗺️ التوصيل لـ: {zone}")
        lines.append("")

    lines.append("📋 الطلب:")
    for i in order.get("items", []):
        lines.append(f"• {i.get('name', '')} × {i.get('quantity', 1)} — {float(i.get('price', 0)):.2f} شيكل")
    lines.append("")
    lines.append(f"المجموع: {float(order.get('total', 0)):.2f} شيكل")
    if order.get("customer_name"):
        lines.append(f"الاسم: {order['customer_name']}")
    if order.get("customer_phone"):
        lines.append(f"الهاتف: {order['customer_phone']}")
    if order.get("notes"):
        lines.append(f"ملاحظات: {order['notes']}")
    return "\n".join(lines)


def whatsapp_link(number: str, message: str) -> str:
    return f"https://wa.me/{number}?text={quote(message, safe='')}"


def send_via_cloud_api(order: dict, settings: dict) -> dict:
    """إرسال الطلب مباشرة عبر WhatsApp Cloud API لو مُعد، وإلا يرجع خطأ."""
    token = (settings.get("whatsapp_api_token") or "").strip()
    phone_id = (settings.get("whatsapp_phone_id") or "").strip()
    base_url = (settings.get("whatsapp_base_url") or "https://graph.facebook.com/v17.0").strip().rstrip("/")
    number = (order.get("customer_phone") or "").strip()

    if not (token and phone_id and number):
        return {"ok": False, "error": "token/phone_id/customer_phone غير مكتمل"}

    message = build_order_message(order, settings)
    url = f"{base_url}/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {"body": message},
    }
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=15.0)
        if resp.status_code == 200:
            return {"ok": True, "data": resp.json()}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"network error: {exc}"}