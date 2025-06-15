import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import asc, desc
from app.core.database import get_db
from app.core.dependencies import  require_admin, require_user
from app.auth.models import UserRole, User
from app.products.models import Product
from app.products.schemas import ProductCreate, ProductUpdate, ProductInDB
from app.exception import ProductNotFoundError, DatabaseError, InvalidInputError

# Create logger for this module
logger = logging.getLogger("app.products")

router = APIRouter(prefix="/products", tags=["products"])

# Admin-only endpoints
@router.post("/admin", response_model=ProductInDB)
async def create_product(
        product: ProductCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # Requires last logged-in admin
):
    try:
        logger.info(f"Admin {current_user.id} creating product: {product.name}")

        # Create product with creator info
        product_data = product.model_dump()
        product_data["created_by"] = current_user.id

        db_product = Product(**product_data)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        logger.info(f"Product created: ID={db_product.id}, Name={db_product.name}")
        return db_product

    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}", exc_info=True)
        raise DatabaseError(detail="Failed to create product")

@router.get("/admin", response_model=list[ProductInDB])
async def read_admin_products(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # Requires last logged-in admin
):
    try:
        logger.info(f"Admin {current_user.id} listing their products")

        products = db.query(Product).filter(
            Product.created_by == current_user.id
        ).all()

        logger.info(f"Found {len(products)} products for admin {current_user.id}")
        return products

    except Exception as e:
        logger.error(f"Failed to list admin products: {str(e)}", exc_info=True)
        raise DatabaseError(detail="Failed to retrieve products")

@router.get("/admin/{product_id}", response_model=ProductInDB)
async def read_admin_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # Requires last logged-in admin
):
    try:
        logger.info(f"Admin {current_user.id} accessing product ID={product_id}")

        product = db.query(Product).filter(
            Product.id == product_id,
            Product.created_by == current_user.id
        ).first()

        if not product:
            logger.warning(f"Product not found: ID={product_id} for admin {current_user.id}")
            raise ProductNotFoundError()

        logger.info(f"Product found: ID={product.id}, Name={product.name}")
        return product

    except ProductNotFoundError:
        raise  # Re-raise custom exceptions
    except Exception as e:
        logger.error(f"Failed to retrieve admin product: {str(e)}", exc_info=True)
        raise DatabaseError(detail="Failed to retrieve product")

@router.put("/admin/{product_id}", response_model=ProductInDB)
async def update_product(
        product_id: int,
        product: ProductUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # Requires last logged-in admin
):
    try:
        logger.info(f"Admin {current_user.id} updating product ID={product_id}")

        db_product = db.query(Product).filter(
            Product.id == product_id,
            Product.created_by == current_user.id
        ).first()

        if not db_product:
            logger.warning(f"Product not found for update: ID={product_id}")
            raise ProductNotFoundError()

        # Log changes
        changes = []
        update_data = product.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            old_value = getattr(db_product, key, None)
            changes.append(f"{key}: {old_value} → {value}")
            setattr(db_product, key, value)

        logger.info(f"Updating product ID={product_id} with changes: {', '.join(changes)}")

        db.commit()
        db.refresh(db_product)

        logger.info(f"Product updated successfully: ID={db_product.id}")
        return db_product

    except ProductNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to update product: {str(e)}", exc_info=True)
        db.rollback()
        raise DatabaseError(detail="Failed to update product")

@router.delete("/admin/{product_id}", status_code=204)
async def delete_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # Requires last logged-in admin
):
    try:
        logger.info(f"Admin {current_user.id} deleting product ID={product_id}")

        product = db.query(Product).filter(
            Product.id == product_id,
            Product.created_by == current_user.id
        ).first()

        if not product:
            logger.warning(f"Product not found for deletion: ID={product_id}")
            raise ProductNotFoundError()

        logger.info(f"Deleting product: ID={product.id}, Name={product.name}")
        db.delete(product)
        db.commit()

        logger.info(f"Product deleted successfully: ID={product_id}")
        return None

    except ProductNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product: {str(e)}", exc_info=True)
        db.rollback()
        raise DatabaseError(detail="Failed to delete product")

# User-only endpoints
@router.get("", response_model=list[ProductInDB])
async def read_products(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user),
        category: Optional[str] = Query(None, description="Filter by product category"),
        min_price: Optional[float] = Query(None, description="Minimum price filter"),
        max_price: Optional[float] = Query(None, description="Maximum price filter"),
        sort_by: Optional[str] = Query(None, description="Sort by field (name, price, created_at)"),
        sort_order: Optional[str] = Query("asc", description="Sort order (asc or desc)"),
):
    try:
        logger.info(f"User {current_user.id} browsing products. Filters: "
                    f"category={category}, min_price={min_price}, max_price={max_price}, "
                    f"sort_by={sort_by}, sort_order={sort_order}")

        query = db.query(Product)

        # Apply category filter
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))

        # Apply price range filter
        if min_price is not None:
            if min_price < 0:
                logger.warning(f"Invalid min_price: {min_price}")
                raise InvalidInputError(detail="min_price cannot be negative")
            query = query.filter(Product.price >= min_price)

        if max_price is not None:
            if max_price < 0:
                logger.warning(f"Invalid max_price: {max_price}")
                raise InvalidInputError(detail="max_price cannot be negative")
            if min_price is not None and max_price < min_price:
                logger.warning(f"Invalid price range: min={min_price}, max={max_price}")
                raise InvalidInputError(detail="max_price must be greater than min_price")
            query = query.filter(Product.price <= max_price)

        # Apply sorting
        sort_mapping = {
            "name": Product.name,
            "price": Product.price,
            "created_at": Product.created_at
        }

        if sort_by:
            if sort_by not in sort_mapping:
                logger.warning(f"Invalid sort_by parameter: {sort_by}")
                raise InvalidInputError(detail=f"Invalid sort field. Valid options: {', '.join(sort_mapping.keys())}")

            sort_field = sort_mapping[sort_by]
            if sort_order.lower() not in ("asc", "desc"):
                logger.warning(f"Invalid sort_order: {sort_order}")
                raise InvalidInputError(detail="sort_order must be 'asc' or 'desc'")

            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))
        else:
            # Default sorting by creation date
            query = query.order_by(desc(Product.created_at))

        products = query.all()
        logger.info(f"Returning {len(products)} products to user {current_user.id}")
        return products

    except (InvalidInputError, ProductNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve products: {str(e)}", exc_info=True)
        raise DatabaseError(detail="Failed to retrieve products")


@router.get("/search", response_model=list[ProductInDB])
async def search_products(
        keyword: str = Query(..., min_length=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)  # Requires last logged-in user
):
    try:
        logger.info(f"User {current_user.id} searching for: '{keyword}'")

        if len(keyword) < 2:
            logger.warning(f"Search keyword too short: '{keyword}'")
            raise InvalidInputError(detail="Search keyword must be at least 2 characters")

        results = db.query(Product).filter(
            (Product.name.ilike(f"%{keyword}%")) |
            (Product.description.ilike(f"%{keyword}%")) |
            (Product.category.ilike(f"%{keyword}%"))
        ).all()

        logger.info(f"Found {len(results)} products matching '{keyword}'")
        return results

    except InvalidInputError:
        raise
    except Exception as e:
        logger.error(f"Search failed for '{keyword}': {str(e)}", exc_info=True)
        raise DatabaseError(detail="Search operation failed")

@router.get("/{product_id}", response_model=ProductInDB)
async def read_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user)  # Requires last logged-in user
):
    try:
        logger.info(f"User {current_user.id} viewing product ID={product_id}")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.warning(f"Product not found: ID={product_id}")
            raise ProductNotFoundError()

        logger.info(f"Returning product: ID={product_id}, Name={product.name}")
        return product

    except ProductNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve product ID={product_id}: {str(e)}", exc_info=True)
        raise DatabaseError(detail="Failed to retrieve product")