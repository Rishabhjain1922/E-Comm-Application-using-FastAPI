from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_last_logged_in_user, verify_admin, verify_user
from app.auth.models import UserRole, User
from app.products.models import Product
from app.products.schemas import ProductCreate, ProductUpdate, ProductInDB
from app.exception import ProductNotFoundError

router = APIRouter(prefix="/products", tags=["products"])

# Admin-only endpoints
@router.post("/admin", response_model=ProductInDB)
async def create_product(
        product: ProductCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_admin)  # Requires last logged-in admin
):
    # Create product with creator info
    product_data = product.model_dump()
    product_data["created_by"] = current_user.id

    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/admin", response_model=list[ProductInDB])
async def read_admin_products(
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_admin)  # Requires last logged-in admin
):
    # Show only products created by this admin
    return db.query(Product).filter(
        Product.created_by == current_user.id
    ).all()

@router.get("/admin/{product_id}", response_model=ProductInDB)
async def read_admin_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_admin)  # Requires last logged-in admin
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.created_by == current_user.id
    ).first()

    if not product:
        raise ProductNotFoundError()
    return product

@router.put("/admin/{product_id}", response_model=ProductInDB)
async def update_product(
        product_id: int,
        product: ProductUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_admin)  # Requires last logged-in admin
):
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.created_by == current_user.id
    ).first()

    if not db_product:
        raise ProductNotFoundError()

    # Update only provided fields
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/admin/{product_id}", status_code=204)
async def delete_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_admin)  # Requires last logged-in admin
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.created_by == current_user.id
    ).first()

    if not product:
        raise ProductNotFoundError()

    db.delete(product)
    db.commit()
    return None

# User-only endpoints
@router.get("", response_model=list[ProductInDB])
async def read_products(
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_user)  # Requires last logged-in user
):
    query = db.query(Product)
    return query.all()

@router.get("/search", response_model=list[ProductInDB])
async def search_products(
        keyword: str = Query(..., min_length=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_user)  # Requires last logged-in user
):
    return db.query(Product).filter(
        (Product.name.ilike(f"%{keyword}%")) |
        (Product.description.ilike(f"%{keyword}%")) |
        (Product.category.ilike(f"%{keyword}%"))
    ).all()

@router.get("/{product_id}", response_model=ProductInDB)
async def read_product(
        product_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(verify_user)  # Requires last logged-in user
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError()
    return product