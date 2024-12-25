from flask import Flask
from .routes import routes  # Import the routes blueprint

def create_app():
    """
    Factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.register_blueprint(routes)  # Register the routes blueprint
    return app
