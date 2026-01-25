from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from .routes.auth import bp as auth_bp
    from .routes.products import bp as products_bp
    from .routes.cart import bp as cart_bp
    from .routes.orders import bp as orders_bp
    from .routes.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)

    @app.get("/")
    def home():
        return """
        <!doctype html>
        <html>
        <head>
          <title>E-Commerce API</title>
          <style>
            body { font-family: Arial; padding: 30px; }
            code { background: #f2f2f2; padding: 2px 6px; border-radius: 6px; }
            .box { border: 1px solid #ddd; padding: 16px; border-radius: 10px; max-width: 800px; }
          </style>
        </head>
        <body>
          <h1>E-Commerce API is Running</h1>
          <div class="box">
            <p>Try these endpoints:</p>
            <ul>
              <li><code>/health</code></li>
              <li><code>/api/products</code></li>
              <li><code>/api/categories</code></li>
              <li><code>/api/auth/register</code></li>
              <li><code>/api/auth/login</code></li>
            </ul>
            <p>Admin endpoints start with: <code>/api/admin/...</code></p>
          </div>
        </body>
        </html>
        """
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
