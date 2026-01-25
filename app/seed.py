from app.extensions import db
from app.models import User, Category, Product

def seed(app):
    with app.app_context():
        if not User.query.filter_by(email="admin@ecom.com").first():
            admin = User(full_name="Admin", email="admin@ecom.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)

        if Category.query.count() == 0:
            c1 = Category(name="Phones")
            c2 = Category(name="Laptops")
            db.session.add_all([c1, c2])
            db.session.flush()

            db.session.add_all([
                Product(name="iPhone X", description="Used", price=199, stock=10, category_id=c1.id),
                Product(name="ThinkPad", description="Business laptop", price=399, stock=5, category_id=c2.id),
            ])

        db.session.commit()
