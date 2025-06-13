from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.auth.models import User
from app.cart.models import CartItem
from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_user
from app.orders.models import Order, OrderItem
from app.orders.schemas import (
    OrderResponse,
    OrderListResponse
)
from app.exception import (
    EmptyCartError,
    InsufficientStockError
)
from app.products.models import Product

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/checkout", response_model=OrderResponse)
async def checkout(
        db: Session = Depends(get_db),
         current_user: User = Depends(verify_user)  # Use active user
):
    logger.info(f"Checkout request from user: {current_user.email}")

    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()

    if not cart_items:
        raise EmptyCartError()

    total_amount = 0
    order_items = []

    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product.stock < item.quantity:
            raise InsufficientStockError(
                detail=f"Not enough stock for {product.name}"
            )

        total_amount += product.price * item.quantity
        order_items.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price_at_purchase": product.price
        })

    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status="completed"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            **item_data
        )
        db.add(order_item)

        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]

    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()

    logger.info(f"Order {order.id} created successfully for user {current_user.email}")
    return order

@router.get("", response_model=list[OrderListResponse])
async def view_order_history(
        db: Session = Depends(get_db),
         current_user: User = Depends(verify_user)
):
    logger.info(f"Order history request from user: {current_user.email}")
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).all()

    logger.info(f"Found {len(orders)} orders for user {current_user.email}")
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def view_order_details(
        order_id: int,
        db: Session = Depends(get_db),
         current_user: User = Depends(verify_user)
):
    logger.info(f"Order details request for order {order_id} from user: {current_user.email}")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order