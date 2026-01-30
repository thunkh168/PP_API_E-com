from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import CartItem, Order, OrderItem
from datetime import datetime
import random

bp = Blueprint("orders", __name__, url_prefix="/api/orders")

def gen_order_code():
    # example: ORD-20260125-123456
    return f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100000, 999999)}"
@bp.get("/list")
@jwt_required()
def my_orders():
    user_id = int(get_jwt_identity())
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).all()
    return jsonify([{
        "id": o.id,
        "order_code": o.order_code,
        "status": o.status,
        "total": o.total,
        "created_at": o.created_at.isoformat(),
        "items": [{
            "product_id": it.product_id,
            "name": it.name_snapshot,
            "price": it.price_snapshot,
            "qty": it.qty
        } for it in o.items]
    } for o in orders])

@bp.get("<int:order_id>")
@jwt_required()
def get_my_order(order_id):
    user_id = int(get_jwt_identity())
    o = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not o:
        return jsonify({"message": "Order not found"}), 404

    return jsonify({
        "id": o.id,
        "order_code": o.order_code,
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

@bp.post("/checkout")
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return jsonify({"message": "Cart is empty"}), 400

    total = 0.0
    for ci in cart_items:
        total += ci.product.price * ci.qty

    order = Order(user_id=user_id, order_code=gen_order_code(), status="pending", total=total)
    db.session.add(order)
    db.session.flush()  # get order.id

    for ci in cart_items:
        item = OrderItem(
            order_id=order.id,
            product_id=ci.product.id,
            name_snapshot=ci.product.name,
            price_snapshot=ci.product.price,
            qty=ci.qty
        )
        db.session.add(item)

    # clear cart
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    return jsonify({"message": "Order created", "order_code": order.order_code}), 201

@bp.put("/cancel/<string:order_code>")
@jwt_required()
def cancel_order(order_code):
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(order_code=order_code, user_id=user_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404

    if order.status != "pending":
        return jsonify({"message": "Only pending orders can be canceled"}), 400

    order.status = "canceled"
    db.session.commit()
    return jsonify({"message": "Order canceled", "order_code": order.order_code}), 200


@bp.delete("<int:order_id>")
@jwt_required()
def delete_my_order(order_id):
    user_id = int(get_jwt_identity())
    o = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not o:
        return jsonify({"message": "Order not found"}), 404

    if o.status not in ["pending", "canceled"]:
        return jsonify({"message": "Cannot delete shipped/paid orders"}), 400

    # delete items first
    OrderItem.query.filter_by(order_id=o.id).delete()
    db.session.delete(o)
    db.session.commit()
    return jsonify({"message": "Order deleted"}), 200

@bp.get("/track/<string:order_code>")
@jwt_required()
def track_order(order_code):
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(order_code=order_code, user_id=user_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404

    return jsonify({
        "order_code": order.order_code,
        "status": order.status,
        "total": order.total,
        "created_at": order.created_at.isoformat()
    })
