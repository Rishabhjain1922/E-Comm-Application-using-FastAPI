from pydantic import BaseModel, Field
from typing import List
from app.products.schemas import ProductInDB

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItemResponse(CartItemBase):
    id: int
    product: ProductInDB

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    total_price: float

    class Config:
        from_attributes = True