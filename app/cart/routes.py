from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_user
from app.cart.models import CartItem
from app.cart.schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse
)
from app.exception import (
    ProductNotFoundError,
    InsufficientStockError
)
from app.products.models import Product

router = APIRouter(prefix="/cart", tags=["cart"])

@router.post("", response_model=CartResponse)
async def add_to_cart(
        item: CartItemCreate,
        db: Session = Depends(get_db),
       current_user: User = Depends(verify_user)
):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise ProductNotFoundError()

    if product.stock < item.quantity:
        raise InsufficientStockError()

    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item.product_id
    ).first()

    if existing_item:
        existing_item.quantity += item.quantity
    else:
        existing_item = CartItem(
            user_id=current_user.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(existing_item)

    db.commit()
    return await view_cart(db, current_user)

@router.get("", response_model=CartResponse)
async def view_cart(
        db: Session = Depends(get_db),
       current_user: User = Depends(verify_user)
):
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    total_price = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    return CartResponse(
        items=cart_items,
        total_items=len(cart_items),
        total_price=total_price
    )

@router.put("/{product_id}", response_model=CartResponse)
async def update_cart_item(
        product_id: int,
        item: CartItemUpdate,
        db: Session = Depends(get_db),
       current_user: User = Depends(verify_user)
):
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).first()

    if not cart_item:
        raise ProductNotFoundError()

    product = db.query(Product).filter(Product.id == product_id).first()
    if product.stock < item.quantity:
        raise InsufficientStockError()

    cart_item.quantity = item.quantity
    db.commit()
    return await view_cart(db, current_user)

@router.delete("/{product_id}", response_model=CartResponse)
async def remove_from_cart(
        product_id: int,
        db: Session = Depends(get_db),
       current_user: User = Depends(verify_user)
):
    db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id
    ).delete()
    db.commit()
    return await view_cart(db, current_user)