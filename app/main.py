from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.core.database import Base, engine  # Import your engine here
from app.products.routes import router as products_router
from app.cart.routes import router as cart_router
from app.orders.routes import router as orders_router

Base.metadata.create_all(bind=engine)
app = FastAPI(swagger_ui_init_oauth={
    "usePkceWithAuthorizationCodeGrant": False,
    "clientId": None
})
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth")
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)

@app.get("/")
def read_root():
    return {"message": "E-commerce API is running"}