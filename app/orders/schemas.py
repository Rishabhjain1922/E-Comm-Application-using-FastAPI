from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import List
from app.products.schemas import ProductInDB

class OrderStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float

class OrderItemResponse(OrderItemBase):
    id: int
    product: ProductInDB

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    total_amount: float
    status: OrderStatus = OrderStatus.pending

class OrderCreate(OrderBase):
    items: List[OrderItemBase]

class OrderResponse(OrderBase):
    id: int
    user_id: int
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    item_count: int

    class Config:
        from_attributes = True