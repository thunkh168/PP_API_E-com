import os
from sqlite3 import IntegrityError
from uuid import uuid4

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from app.utils.decorators import admin_required
from app.extensions import db
from app.models import User, Category, Product, Order

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# ---------- Product CRUD ----------
@bp.post("/products")
@jwt_required()
@admin_required
def create_product():
    # Accept BOTH JSON and form-data
    if request.is_json:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        price = data.get("price")
        stock = data.get("stock")
        category_id = data.get("category_id")
        image_url = (data.get("image_url") or "").strip()
        image_file = None
    else:
        # multipart/form-data
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        price = request.form.get("price")
        stock = request.form.get("stock")
        category_id = request.form.get("category_id")
        image_file = request.files.get("image")  # <-- use key "image"
        image_url = ""

    # validate required fields
    if not name or price is None or stock is None or category_id is None:
        return jsonify({"message": "name, price, stock, category_id required"}), 400

    # handle file upload if provided
    if image_file:
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(image_file.filename)
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        new_name = f"{uuid4().hex}{ext}"
        save_path = os.path.join(upload_dir, new_name)

        image_file.save(save_path)
        image_url = f"/static/uploads/{new_name}"

    p = Product(
        name=name,
        description=description,
        price=float(price),
        stock=int(stock),
        image_url=image_url,
        category_id=int(category_id)
    )
    db.session.add(p)
    db.session.commit()

    return jsonify({"message": "Product created", "id": p.id, "image_url": p.image_url}), 201

@bp.put("/products/<int:pid>")
@jwt_required()
@admin_required
def update_product(pid):
    p = Product.query.get(pid)
    if not p:
        return jsonify({"message": "Product not found"}), 404

    # Accept JSON OR multipart/form-data
    if request.is_json:
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        description = data.get("description")
        image_url = data.get("image_url")
        price = data.get("price")
        stock = data.get("stock")
        category_id = data.get("category_id")
        image_file = None
    else:
        name = request.form.get("name")
        description = request.form.get("description")
        image_url = request.form.get("image_url")
        price = request.form.get("price")
        stock = request.form.get("stock")
        category_id = request.form.get("category_id")
        image_file = request.files.get("image")

    # optional fields update
    if name is not None:
        p.name = name.strip()
    if description is not None:
        p.description = (description or "").strip()
    if price is not None:
        p.price = float(price)
    if stock is not None:
        p.stock = int(stock)
    if category_id is not None:
        p.category_id = int(category_id)

    # file upload (same folder as create)
    if image_file:
        import os
        from uuid import uuid4
        from werkzeug.utils import secure_filename
        from flask import current_app

        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(image_file.filename)
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        new_name = f"{uuid4().hex}{ext}"
        save_path = os.path.join(upload_dir, new_name)

        image_file.save(save_path)
        p.image_url = f"/static/uploads/{new_name}"
    elif image_url is not None:
        p.image_url = (image_url or "").strip()

    db.session.commit()
    return jsonify({"message": "Product updated", "id": p.id, "image_url": p.image_url}), 200

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
@bp.get("/categories")
@jwt_required()
@admin_required
def list_categories():
    cats = Category.query.order_by(Category.id.desc()).all()
    return jsonify([{
        "id": c.id,
        "name": c.name
    } for c in cats]), 200
@bp.get("/categories/<int:cat_id>")
@jwt_required()
@admin_required
def get_category(cat_id):
    c = Category.query.get(cat_id)
    if not c:
        return jsonify({"message": "Category not found"}), 404

    return jsonify({
        "id": c.id,
        "name": c.name
    }), 200
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

@bp.put("/categories/<int:cat_id>")
@jwt_required()
@admin_required
def update_category(cat_id):
    c = Category.query.get(cat_id)
    if not c:
        return jsonify({"message": "Category not found"}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        return jsonify({"message": "name required"}), 400

    # prevent duplicate category name
    exists = Category.query.filter(Category.name == name, Category.id != cat_id).first()
    if exists:
        return jsonify({"message": "Category exists"}), 409

    c.name = name
    db.session.commit()

    return jsonify({"message": "Category updated", "id": c.id, "name": c.name}), 200

@bp.delete("/categories/<int:cat_id>")
@jwt_required()
@admin_required
def delete_category(cat_id):
    c = Category.query.get(cat_id)
    if not c:
        return jsonify({"message": "Category not found"}), 404

    # prevent delete if category has products
    if c.products and len(c.products) > 0:
        return jsonify({
            "message": "Cannot delete category because it has products",
            "product_count": len(c.products)
        }), 400

    try:
        db.session.delete(c)
        db.session.commit()
        return jsonify({"message": "Category deleted"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Cannot delete category (used by other records)"}), 400

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

@bp.get("/orders/<int:oid>")
@jwt_required()
@admin_required
def admin_get_order(oid):
    o = Order.query.get(oid)
    if not o:
        return jsonify({"message": "Order not found"}), 404

    return jsonify({
        "id": o.id,
        "order_code": o.order_code,
        "customer_id": o.user_id,
        "status": o.status,
        "total": o.total,
        "created_at": o.created_at.isoformat(),
        "items": [{
            "product_id": it.product_id,
            "name": it.name_snapshot,
            "price": it.price_snapshot,
            "qty": it.qty
        } for it in o.items]
    }), 200

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



