import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_user
from app.cart.models import CartItem
from app.cart.schemas import CartItemCreate, CartItemUpdate, CartResponse
from app.exception import ProductNotFoundError, InsufficientStockError
from app.products.models import Product

# Initialize logger
logger = logging.getLogger("app.cart")

router = APIRouter(prefix="/cart", tags=["cart"])

@router.post("", response_model=CartResponse)
async def add_to_cart(
        item: CartItemCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    """Add item to cart with proper inventory validation"""
    try:
        logger.info(f"User {current_user.id} adding to cart: {item.product_id}, qty: {item.quantity}")

        # Get product and validate
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            logger.warning(f"Product not found: {item.product_id}")
            raise ProductNotFoundError()

        # Check stock availability
        if product.stock < item.quantity:
            logger.warning(
                f"Insufficient stock for product {product.id}: "
                f"requested {item.quantity}, available {product.stock}"
            )
            raise InsufficientStockError()

        # Find existing cart item
        existing_item = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == item.product_id
        ).first()

        # Update or create cart item
        if existing_item:
            logger.info(f"Updating existing cart item: {existing_item.id}")
            existing_item.quantity += item.quantity
        else:
            logger.info("Creating new cart item")
            existing_item = CartItem(
                user_id=current_user.id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(existing_item)

        db.commit()
        logger.info(f"Cart updated for user {current_user.id}")

        return await view_cart(db, current_user)

    except (ProductNotFoundError, InsufficientStockError):
        # Known exceptions, already logged
        raise
    except Exception as e:
        logger.exception(f"Failed to add to cart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while adding to cart"
        )

@router.get("", response_model=CartResponse)
async def view_cart(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    """Retrieve user's cart contents"""
    try:
        logger.info(f"Viewing cart for user {current_user.id}")

        cart_items = db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).all()

        # Calculate totals
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        total_items = len(cart_items)

        logger.info(f"Cart retrieved: {total_items} items, total: ${total_price:.2f}")

        return CartResponse(
            items=cart_items,
            total_items=total_items,
            total_price=total_price
        )

    except Exception as e:
        logger.exception(f"Failed to retrieve cart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving cart"
        )

@router.put("/{product_id}", response_model=CartResponse)
async def update_cart_item(
        product_id: int,
        item: CartItemUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    """Update cart item quantity with validation"""
    try:
        logger.info(
            f"User {current_user.id} updating product {product_id} "
            f"to quantity {item.quantity}"
        )

        # Get cart item
        cart_item = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == product_id
        ).first()

        if not cart_item:
            logger.warning(f"Cart item not found for product {product_id}")
            raise ProductNotFoundError()

        # Get product and validate stock
        product = db.query(Product).filter(Product.id == product_id).first()
        if product.stock < item.quantity:
            logger.warning(
                f"Insufficient stock for update: requested {item.quantity}, "
                f"available {product.stock} for product {product_id}"
            )
            raise InsufficientStockError()

        # Update quantity
        cart_item.quantity = item.quantity
        db.commit()

        logger.info(f"Cart item updated: product {product_id}, new qty {item.quantity}")

        return await view_cart(db, current_user)

    except (ProductNotFoundError, InsufficientStockError):
        raise
    except Exception as e:
        logger.exception(f"Failed to update cart item: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating cart item"
        )

@router.delete("/{product_id}", response_model=CartResponse)
async def remove_from_cart(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)
):
    """Remove item from cart"""
    try:
        logger.info(f"User {current_user.id} removing product {product_id} from cart")

        # Delete cart item
        result = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == product_id
        ).delete()

        if not result:
            logger.warning(f"Item not in cart: product {product_id}")
            raise ProductNotFoundError()

        db.commit()
        logger.info(f"Product {product_id} removed from cart")

        return await view_cart(db, current_user)

    except ProductNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Failed to remove from cart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while removing from cart"
        )