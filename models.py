"""Py ADA هو models للـ Pharmacy API — بيانات المنتجات والطلبات."""

from pydantic import BaseModel, Field
from typing import Optional

# ── المنتج ──
class Product(BaseModel):
    id: int
    name: str
    category: str
    desc: str
    price: float
    icon: str
    image: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    category: str
    desc: str
    price: float
    icon: str = "medical"
    image: Optional[str] = None
    # id is auto-assigned by backend, not required from client

# ── السلة ──
class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, default=1)

class Cart(BaseModel):
    items: list[CartItem] = []

# ── الطلب ──
class OrderRequest(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: list[CartItem]
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    status: str = "received"
    message: str
    whatsapp_url: str
    total: float
    item_count: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    items: list[dict] = []
    created_at: str = ""
