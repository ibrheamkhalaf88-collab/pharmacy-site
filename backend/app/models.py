"""Pydantic models — التحقق من البيانات للـ API."""
from typing import Optional

from pydantic import BaseModel, Field


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="أخرى", max_length=40)
    desc: str = Field(default="", max_length=500)
    price: float = Field(gt=0)
    icon: str = Field(default="medical", max_length=40)
    image: str = ""  # http(s) link أو فارغ


class ProductImageIn(BaseModel):
    image: str


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=99)


class OrderIn(BaseModel):
    customer_name: str = Field(default="", max_length=80)
    customer_phone: str = Field(default="", max_length=30)
    notes: str = Field(default="", max_length=300)
    items: list[CartItemIn] = Field(min_length=1)


class OrderStatusIn(BaseModel):
    status: str


class OrderReplyIn(BaseModel):
    message: str = Field(min_length=1, max_length=800)


class SettingsIn(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    hours: Optional[str] = None
    whatsapp_api_token: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None
    whatsapp_base_url: Optional[str] = None


class LoginIn(BaseModel):
    password: str