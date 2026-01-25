from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import CartItem, Product

bp = Blueprint("cart", __name__, url_prefix="/api/cart")

@bp.get("")
@jwt_required()
def get_cart():
    user_id = int(get_jwt_identity())
    items = CartItem.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": i.id,
        "qty": i.qty,
        "product": {"id": i.product.id, "name": i.product.name, "price": i.product.price, "image_url": i.product.image_url}
    } for i in items])

@bp.post("/add")
@jwt_required()
def add_to_cart():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    product_id = int(data.get("product_id", 0))
    qty = int(data.get("qty", 1))

    if product_id <= 0 or qty <= 0:
        return jsonify({"message": "product_id and qty must be valid"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if item:
        item.qty += qty
    else:
        item = CartItem(user_id=user_id, product_id=product_id, qty=qty)
        db.session.add(item)

    db.session.commit()
    return jsonify({"message": "Added to cart"}), 200

@bp.delete("/remove/<int:item_id>")
@jwt_required()
def remove_item(item_id):
    user_id = int(get_jwt_identity())
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"message": "Cart item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Removed"}), 200

@bp.delete("/clear")
@jwt_required()
def clear_cart():
    user_id = int(get_jwt_identity())
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"message": "Cart cleared"}), 200
