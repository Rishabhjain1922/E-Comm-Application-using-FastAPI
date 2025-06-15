import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.core.database import Base, engine
from app.products.routes import router as products_router
from app.cart.routes import router as cart_router
from app.orders.routes import router as orders_router
from app.utils.logging import setup_logging
from app.core.error_handlers import register_error_handlers
import logging

# Initialize logging first
try:
    test_dir = Path("logs")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "access_test.log"
    with open(test_file, "w") as f:
        f.write("File system access test successful\n")
    print(f"File system test successful: {test_file}")
except Exception as e:
    print(f"File system access failed: {str(e)}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app")
log_path = Path("logs").absolute()
logger.info(f"Log directory: {log_path}")
logger.info(f"Directory exists: {log_path.exists()}")
logger.info(f"Directory writable: {os.access(log_path, os.W_OK)}")

# Test file creation
test_file = log_path / "test.log"
try:
    with open(test_file, "w") as f:
        f.write("Test file content\n")
    logger.info(f"Test file created: {test_file}")
except Exception as e:
    logger.error(f"File creation failed: {str(e)}")
try:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.exception("Failed to create database tables")
    raise

app = FastAPI(
    title="E-Commerce API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth")
app.include_router(products_router, prefix="/products")
app.include_router(cart_router, prefix="/cart")
app.include_router(orders_router, prefix="/orders")
logger.info("Routers registered")

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "E-commerce API is running"}

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

@app.get("/test-logging")
def test_logging():
    logger.info("This is a test INFO message")
    logger.warning("This is a test WARNING message")
    logger.error("This is a test ERROR message")
    try:
        1 / 0
    except Exception as e:
        logger.exception("This is a test EXCEPTION")

    return {"message": "Check your logs for test messages"}