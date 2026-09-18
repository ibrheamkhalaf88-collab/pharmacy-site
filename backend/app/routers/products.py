"""Products router — قراءة عامة، كتابة محمية بـ admin auth."""
from fastapi import APIRouter, Depends, HTTPException

from .. import database as db
from ..deps import require_admin
from ..models import ProductImageIn, ProductIn

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(category: str | None = None):
    products = db.list_products(category)
    categories = sorted({p["category"] for p in db.list_products()})
    return {"products": products, "count": len(products), "categories": categories}


@router.get("/{product_id}")
def get_product(product_id: int):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"product": product}


@router.post("", status_code=201)
def add_product(body: ProductIn, _: dict = Depends(require_admin)):
    data = {
        "name": body.name.strip(),
        "category": body.category.strip() or "أخرى",
        "desc": body.desc.strip(),
        "price": round(body.price, 2),
        "icon": body.icon.strip() or "medical",
        "image": body.image.strip(),
        "active": True,
    }
    return {"product": db.create_product(data), "status": "created"}


@router.put("/{product_id}")
def edit_product(product_id: int, body: ProductIn, _: dict = Depends(require_admin)):
    data = {
        "name": body.name.strip(),
        "category": body.category.strip() or "أخرى",
        "desc": body.desc.strip(),
        "price": round(body.price, 2),
        "icon": body.icon.strip() or "medical",
        "image": body.image.strip(),
    }
    updated = db.update_product(product_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"product": updated, "status": "updated"}


@router.delete("/{product_id}")
def delete_product(product_id: int, _: dict = Depends(require_admin)):
    if not db.delete_product(product_id):
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"status": "deleted", "product_id": product_id}


@router.post("/{product_id}/image")
def set_product_image(product_id: int, body: ProductImageIn, _: dict = Depends(require_admin)):
    image = body.image.strip()
    if not image:
        raise HTTPException(status_code=400, detail="رابط الصورة مطلوب")
    updated = db.update_product(product_id, {"image": image})
    if not updated:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return {"product": updated, "status": "updated"}