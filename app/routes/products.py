from flask import Blueprint, request, jsonify
from app.models import Product, Category

bp = Blueprint("products", __name__, url_prefix="/api")

@bp.get("/categories")
def categories():
    cats = Category.query.order_by(Category.name.asc()).all()
    return jsonify([{"id": c.id, "name": c.name} for c in cats])

# @bp.get("/products")
# def product_list():
#     # optional query: ?category_id=1
#     category_id = request.args.get("category_id")
#     q = Product.query
#     if category_id:
#         q = q.filter_by(category_id=int(category_id))
#     products = q.order_by(Product.id.desc()).all()
#
#     return jsonify([{
#         "id": p.id,
#         "name": p.name,
#         "description": p.description,
#         "price": p.price,
#         "stock": p.stock,
#         "image_url": p.image_url,
#         "category": {"id": p.category.id,
#         "name": p.category.name}
#     } for p in products])
@bp.get("/products")
def product_list():
    category_id = request.args.get("category_id")
    q = Product.query
    if category_id:
        q = q.filter_by(category_id=int(category_id))

    products = q.order_by(Product.id.desc()).all()

    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image_url": p.image_url,
        "category": None if not p.category else {
            "id": p.category.id,
            "name": p.category.name
        }
    } for p in products])

