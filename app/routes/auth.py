from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
# from run.extensions import db
from app.extensions import db

from app.models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@bp.post("/register")
def register():
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not full_name or not email or not password:
        return jsonify({"message": "full_name, email, password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    user = User(full_name=full_name, email=email, role="customer")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered successfully"}), 201

@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({
        "access_token": token,
        "user": {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}
    })

@bp.post("/logout")
@jwt_required()
def logout():
    # JWT stateless example: frontend just delete token
    return jsonify({"message": "Logged out Success"}), 200
