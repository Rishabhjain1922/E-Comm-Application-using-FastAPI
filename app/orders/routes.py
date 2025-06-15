from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.auth.models import User
from app.cart.models import CartItem
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_user
from app.orders.models import Order, OrderItem
from app.orders.schemas import OrderResponse, OrderListResponse
from app.exception import (
    EmptyCartError,
    InsufficientStockError,
    OrderCreationError,
    DatabaseError
)
from app.products.models import Product

# Get logger from the app namespace
logger = logging.getLogger("app.orders")
router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/checkout", response_model=OrderResponse)
async def checkout(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    logger.info(f"Checkout initiated for user: {current_user.email}")

    try:
        # Fetch cart items
        cart_items = db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).all()

        if not cart_items:
            logger.warning(f"Empty cart for user: {current_user.email}")
            raise EmptyCartError()

        logger.info(f"Processing {len(cart_items)} cart items for user: {current_user.email}")
        total_amount = 0
        order_items = []
        products_to_update = {}

        # Process each cart item
        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                logger.error(f"Product {item.product_id} not found in cart for user {current_user.email}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Product ID {item.product_id} not found"
                )

            # Check stock availability
            if product.stock < item.quantity:
                logger.warning(
                    f"Insufficient stock for product {product.id}: "
                    f"requested {item.quantity}, available {product.stock}"
                )
                raise InsufficientStockError(
                    detail=f"Not enough stock for {product.name}"
                )

            # Calculate total and prepare order items
            total_amount += product.price * item.quantity
            order_items.append({
                "product_id": product.id,
                "quantity": item.quantity,
                "price_at_purchase": product.price
            })

            # Track products for stock update
            products_to_update[product.id] = {
                "product": product,
                "quantity": item.quantity
            }

        # Create order within a transaction
        try:
            # Start transaction
            order = Order(
                user_id=current_user.id,
                total_amount=total_amount,
                status="completed"
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            logger.info(f"Order {order.id} created successfully")
        except Exception as e:
            db.rollback()
            logger.error(f"Order creation failed: {str(e)}")
            raise OrderCreationError("Failed to create order") from e

        # Create order items and update stock
        try:
            for item_data in order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                db.add(order_item)

                # Update product stock
                product_info = products_to_update[item_data["product_id"]]
                product_info["product"].stock -= product_info["quantity"]

            # Clear cart
            db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
            db.commit()

            logger.info(
                f"Order {order.id} processed successfully with {len(order_items)} items. "
                f"Total: {total_amount}"
            )
        except Exception as e:
            db.rollback()
            logger.critical(
                f"Order processing failed for order {order.id}. "
                f"Partial order created but not completed: {str(e)}"
            )
            raise DatabaseError("Order processing failed") from e

        return order

    except Exception as e:
        logger.exception(f"Checkout failed for user {current_user.email}: {str(e)}")
        raise

@router.get("", response_model=list[OrderListResponse])
async def view_order_history(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    logger.info(f"Order history requested for user: {current_user.email}")

    try:
        orders = db.query(Order).filter(
            Order.user_id == current_user.id
        ).order_by(Order.created_at.desc()).all()

        # Build response with item_count
        response = []
        for order in orders:
            response.append(OrderListResponse(
                id=order.id,
                total_amount=order.total_amount,
                status=order.status,
                created_at=order.created_at,
                item_count=len(order.items)
            ))

        logger.info(f"Returning {len(orders)} orders for user {current_user.email}")
        return response

    except Exception as e:
        logger.error(f"Failed to fetch order history for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve order history"
        )

@router.get("/{order_id}", response_model=OrderResponse)
async def view_order_details(
        order_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    logger.info(f"Order details requested for order {order_id} by user {current_user.email}")

    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()

        if not order:
            logger.warning(
                f"Order not found: {order_id} for user {current_user.email}. "
                "Either doesn't exist or doesn't belong to user"
            )
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        logger.info(f"Returning order details for order {order_id}")
        return order

    except HTTPException:
        # Re-raise HTTPExceptions as they are intentional
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve order {order_id} for user {current_user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve order details"
        )