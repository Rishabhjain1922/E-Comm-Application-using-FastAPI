# 🛒 E-commerce Backend System Using FastAPI

## 📌 Project Overview

This project is a RESTful backend API developed using **FastAPI** for an e-commerce platform. It offers a secure, scalable, and modular backend for managing users, products, orders, shopping carts, and authentication. It supports both admin-side product control and customer-side browsing and purchasing.

## 🎯 Objectives

- Admin-side CRUD operations for product management  
- User authentication (signup, login, forgot/reset password)  
- Product browsing, search, and filter functionality  
- Shopping cart operations and order management  
- Role-Based Access Control (RBAC) using JWT  

## 🛠️ Tech Stack

- **FastAPI** – Web framework  
- **SQLite** – Lightweight relational database  
- **SQLAlchemy** – ORM for database interaction  
- **Pydantic** – Data validation and parsing  
- **JWT (via PyJWT)** – Secure token-based authentication  

## 🧾 Features

### 🔐 Authentication
- Signup & Signin  
- Forgot/Reset password via secure token  
- JWT-based authentication  
- RBAC support (admin and user roles)

### 📦 Product Management (Admin Only)
- Add, update, delete, and list products  
- Pagination, filtering, and detailed product views

### 🛍️ Product APIs (Public)
- List products with filters (category, price, sort)  
- Search by keyword  
- View individual product details

### 🛒 Cart
- Add, remove, and update items in the cart  
- View cart contents

### 💳 Checkout
- Mock checkout with order creation  
- Confirmation upon successful payment simulation

### 📜 Orders
- View order history and detailed past orders (for users)

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

## 🚀 Getting Started

### Step 1: Clone the Repository

```bash
git clone https://github.com/Rishabhjain1922/E-Comm-Application-using-FastAPI.git
cd E-Comm-Application-using-FastAPI
```

### Step 2: Create and Activate Virtual Environment

#### For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create `.env` File

Create a `.env` file in the root directory with the following content:

```env
DATABASE_URL=sqlite:///./ecommerce.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 5: Run the Application

```bash
uvicorn app.main:app --reload
```

Now open your browser and go to [http://localhost:8000/docs](http://localhost:8000/docs)

## 🧪 Testing

Use Postman or Swagger UI to test API endpoints.  
Test coverage includes:

- User authentication (signup/login/reset)  
- Product CRUD operations  
- Cart operations  
- Checkout & order flows  

## 🔐 Security Highlights

- Passwords hashed using `bcrypt`  
- Input validation using `Pydantic`  
- JWT-based authentication and RBAC  
- Secure password reset with time-limited tokens  

## 📄 API Documentation

Interactive API docs available at:  
[http://localhost:8000/docs](http://localhost:8000/docs)

## 🧰 Developer Tools

- Auto-formatting: `black`  
- Linting: `flake8`  
- Migrations: `alembic`  

## 📤 Deployment Guidelines

- Use `.env` for environment configuration  
- Use `Uvicorn` or `Gunicorn` in production  
- Replace SQLite with PostgreSQL for production use  
- Set up HTTPS, proper logging, and error handling  

## 📚 Deliverables

- ✅ Fully functional FastAPI backend  
- ✅ Postman collection for testing  
- ✅ Swagger API documentation  
- ✅ Seed data scripts  
- ✅ Complete README with setup guide  

## 🤝 Contributing

- Fork the repository  
- Create a new branch: `feature/your-feature-name`  
- Commit your changes  
- Push to your branch  
- Open a Pull Request  
