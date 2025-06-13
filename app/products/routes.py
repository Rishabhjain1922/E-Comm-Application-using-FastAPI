from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.products.models import Product
from app.products.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductInDB,
    ProductFilters
)
from app.exception import ProductNotFoundError

router = APIRouter(prefix="/products", tags=["products"])

# Admin-only endpoints
@router.post("/admin", response_model=ProductInDB, dependencies=[Depends(get_current_admin)])
async def create_product(
        product: ProductCreate,
        db: Session = Depends(get_db)
):
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product



@router.get("/admin", response_model=list[ProductInDB], dependencies=[Depends(get_current_admin)])
async def read_admin_products(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    return db.query(Product).offset(skip).limit(limit).all()

@router.get("/admin/{product_id}", response_model=ProductInDB, dependencies=[Depends(get_current_admin)])
async def read_admin_product(
        product_id: int,
        db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError()
    return product

@router.put("/admin/{product_id}", response_model=ProductInDB, dependencies=[Depends(get_current_admin)])
async def update_product(
        product_id: int,
        product: ProductUpdate,
        db: Session = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise ProductNotFoundError()

    for key, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/admin/{product_id}", status_code=204, dependencies=[Depends(get_current_admin)])
async def delete_product(
        product_id: int,
        db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError()

    db.delete(product)
    db.commit()
    return None

# Public endpoints
@router.get("", response_model=list[ProductInDB])
async def read_products(
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    query = db.query(Product)

    if category:
        query = query.filter(Product.category == category)
    if min_price:
        query = query.filter(Product.price >= min_price)
    if max_price:
        query = query.filter(Product.price <= max_price)

    return query.offset(skip).limit(limit).all()

@router.get("/search", response_model=list[ProductInDB])
async def search_products(
        keyword: str = Query(..., min_length=1),
        db: Session = Depends(get_db)
):
    return db.query(Product).filter(
        (Product.name.ilike(f"%{keyword}%")) |
        (Product.description.ilike(f"%{keyword}%")) |
        (Product.category.ilike(f"%{keyword}%"))
    ).all()

@router.get("/{product_id}", response_model=ProductInDB)
async def read_product(
        product_id: int,
        db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ProductNotFoundError()
    return product