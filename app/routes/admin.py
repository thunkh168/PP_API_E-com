from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import admin_required
from app.extensions import db
from app.models import User, Category, Product, Order

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# ---------- Customers / Users ----------
@bp.get("/users")
@jwt_required()
@admin_required
def list_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([{
        "id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()
    } for u in users])

@bp.post("/users")
@jwt_required()
@admin_required
def create_user():
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "customer")

    if not full_name or not email or not password:
        return jsonify({"message": "full_name, email, password required"}), 400
    if role not in ["customer", "admin"]:
        return jsonify({"message": "role must be customer/admin"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    u = User(full_name=full_name, email=email, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify({"message": "User created", "id": u.id}), 201

@bp.put("/users/<int:user_id>")
@jwt_required()
@admin_required
def update_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json() or {}
    if "full_name" in data:
        u.full_name = data["full_name"].strip()
    if "role" in data:
        if data["role"] not in ["customer", "admin"]:
            return jsonify({"message": "role must be customer/admin"}), 400
        u.role = data["role"]
    if "password" in data and data["password"]:
        u.set_password(data["password"])

    db.session.commit()
    return jsonify({"message": "User updated"}), 200

@bp.delete("/users/<int:user_id>")
@jwt_required()
@admin_required
def delete_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"message": "User not found"}), 404
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200

# ---------- Category CRUD ----------
@bp.post("/categories")
@jwt_required()
@admin_required
def create_category():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"message": "name required"}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category exists"}), 409
    c = Category(name=name)
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Category created", "id": c.id}), 201

@bp.delete("/categories/<int:cat_id>")
@jwt_required()
@admin_required
def delete_category(cat_id):
    c = Category.query.get(cat_id)
    if not c:
        return jsonify({"message": "Category not found"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Category deleted"}), 200

# ---------- Product CRUD ----------
@bp.post("/products")
@jwt_required()
@admin_required
def create_product():
    data = request.get_json() or {}
    required = ["name", "price", "stock", "category_id"]
    if any(k not in data for k in required):
        return jsonify({"message": "name, price, stock, category_id required"}), 400

    p = Product(
        name=data["name"].strip(),
        description=(data.get("description") or "").strip(),
        price=float(data["price"]),
        stock=int(data["stock"]),
        image_url=(data.get("image_url") or "").strip(),
        category_id=int(data["category_id"])
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"message": "Product created", "id": p.id}), 201

@bp.put("/products/<int:pid>")
@jwt_required()
@admin_required
def update_product(pid):
    p = Product.query.get(pid)
    if not p:
        return jsonify({"message": "Product not found"}), 404
    data = request.get_json() or {}

    for field in ["name", "description", "image_url"]:
        if field in data:
            setattr(p, field, (data[field] or "").strip())
    if "price" in data:
        p.price = float(data["price"])
    if "stock" in data:
        p.stock = int(data["stock"])
    if "category_id" in data:
        p.category_id = int(data["category_id"])

    db.session.commit()
    return jsonify({"message": "Product updated"}), 200

@bp.delete("/products/<int:pid>")
@jwt_required()
@admin_required
def delete_product(pid):
    p = Product.query.get(pid)
    if not p:
        return jsonify({"message": "Product not found"}), 404
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200

# ---------- Order management ----------
@bp.get("/orders")
@jwt_required()
@admin_required
def all_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    return jsonify([{
        "id": o.id,
        "order_code": o.order_code,
        "customer_id": o.user_id,
        "status": o.status,
        "total": o.total,
        "created_at": o.created_at.isoformat()
    } for o in orders])

@bp.put("/orders/<int:oid>/status")
@jwt_required()
@admin_required
def update_order_status(oid):
    o = Order.query.get(oid)
    if not o:
        return jsonify({"message": "Order not found"}), 404
    data = request.get_json() or {}
    status = data.get("status", "").strip()
    allowed = ["pending", "paid", "shipped", "delivered", "canceled"]
    if status not in allowed:
        return jsonify({"message": f"status must be one of {allowed}"}), 400
    o.status = status
    db.session.commit()
    return jsonify({"message": "Order status updated"}), 200



