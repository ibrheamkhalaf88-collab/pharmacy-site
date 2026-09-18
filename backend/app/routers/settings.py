"""Settings router — محمي بالكامل بـ admin auth."""
from fastapi import APIRouter, Depends

from .. import database as db
from ..deps import require_admin
from ..models import SettingsIn

ALLOWED_FIELDS = {
    "name", "address", "phone", "whatsapp_number", "hours",
    "whatsapp_api_token", "whatsapp_phone_id", "whatsapp_base_url",
}

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_pharmacy_settings(_: dict = Depends(require_admin)):
    return {"settings": db.get_settings()}


@router.put("")
def update_pharmacy_settings(body: SettingsIn, _: dict = Depends(require_admin)):
    patch = body.model_dump(exclude_none=True)
    patch = {k: v for k, v in patch.items() if k in ALLOWED_FIELDS}
    return {"settings": db.update_settings(patch), "status": "updated"}