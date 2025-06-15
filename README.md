# 🛒 E-commerce Backend System Using FastAPI

## 📌 Project Overview

This project is a **backend RESTful API** built with **FastAPI** for an e-commerce platform. It provides a secure, maintainable, and modular backend system for managing users, products, orders, carts, and authentication functionalities. The system is designed for admin product management and customer-side browsing and ordering functionalities.

---

## 🎯 Objectives

- Implement **Admin CRUD operations** for product management.
- Provide **User authentication** (signup, signin, forgot/reset password).
- Enable **Product browsing**, filtering, and search.
- Add **Shopping cart**, checkout, and order history features.
- Enforce **RBAC (Role-Based Access Control)** using JWT.

---

## 📦 Tech Stack

- **FastAPI** - Web framework
- ** SQLite** - Database
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **JWT (via PyJWT)** - Authentication

---

## 🧾 Features

### 🔐 Authentication
- Signup, Signin
- Forgot/Reset password via secure token
- JWT-based authentication
- RBAC: `admin` and `user` roles

### 📦 Product Management (Admin Only)
- Add, Update, Delete, List products
- Pagination, filtering, and detailed views

### 🛍️ Product APIs (Public)
- Product listing with filters (category, price, sort)
- Search by keyword
- Detail view of a single product

### 🛒 Cart
- Add/Remove/Update items in cart
- View cart

### 💳 Checkout
- Dummy checkout (mocked payment)
- Order creation on successful checkout

### 📜 Orders
- View order history and detailed past orders (for users only)


## 🧱 Database Schema Overview

### Users
- `id`, `name`, `email`, `hashed_password`, `role (admin/user)`

### Products
- `id`, `name`, `description`, `price`, `stock`, `category`, `image_url`

### Cart
- `id`, `user_id`, `product_id`, `quantity`

### PasswordResetTokens
- `id`, `user_id`, `token`, `expiration_time`, `used`

### Orders
- `id`, `user_id`, `total_amount`, `status`, `created_at`

### OrderItems
- `id`, `order_id`, `product_id`, `quantity`, `price_at_purchase`

---

## 🚀 Getting Started

```bash
### Step 1️⃣: Clone the Repository
git clone https://github.com/Rishabhjain1922/E-Comm-Application-using-FastAPI/tree/main
cd fastapi-ecommerce-backend
Step 2️⃣: Create a Virtual Environment

# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
Step 3️⃣: Install Dependencies

pip install -r requirements.txt
Step 4️⃣: Set Environment Variables
Create a .env file in the root directory and add:

env

DATABASE_URL=sqlite:///./ecommerce.db  # or your PostgreSQL connection string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

Step 5️⃣: Run the Application

uvicorn app.main:app --reload
Now open http://localhost:8000/docs for interactive Swagger documentation.
```bash
---
🧪 Testing
Use Postman or Swagger UI for manual API testing.

Includes authentication, product CRUD, cart, checkout, and order tests.

🔐 Security Highlights
Passwords hashed using bcrypt

Input validation via Pydantic

Role-based access control (RBAC)

Secure password reset with tokens

📄 API Documentation
Available via Swagger UI:
http://localhost:8000/docs
🧰 Developer Tools
Auto-formatting: black

Linting: flake8

Migrations: alembic

📤 Deployment Guidelines
Use .env for sensitive configs

Use Gunicorn or Uvicorn in production

Connect to a production-grade database (e.g., PostgreSQL)

Set up HTTPS, logging, and proper exception handling

📚 Deliverables
✅ Fully functional FastAPI backend

✅ Postman collection for testing

✅ Swagger API docs

✅ Seed data scripts

✅ Complete README with setup instructions

🤝 Contributing
Fork the repo

Create a new branch (feature/your-feature)

Commit your changes

Push to the branch

Create a Pull Request

