from flask import Blueprint, request, jsonify
from app.models import Product, Category

bp = Blueprint("products", __name__, url_prefix="/api")

@bp.get("/products")
def product_list():
    category_id = request.args.get("category_id")
    q = Product.query
    if category_id:
        q = q.filter_by(category_id=int(category_id))

    products = q.order_by(Product.id.desc()).all()
    base_url = request.url_root.rstrip("/")

    def build_image_url(img):
        if not img:
            return ""
        if img.startswith("http://") or img.startswith("https://"):
            return img              # external image
        return f"{base_url}{img}"   # local uploaded image

    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image": build_image_url(p.image_url),
        "category": None if not p.category else {
            "id": p.category.id,
            "name": p.category.name
        }
    } for p in products])
