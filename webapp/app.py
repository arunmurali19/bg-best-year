"""Flask application factory."""

from flask import Flask
from webapp.config import Config
from webapp import database


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    database.init_app(app)

    from webapp.routes.vote import vote_bp
    from webapp.routes.bracket import bracket_bp
    from webapp.routes.admin import admin_bp

    app.register_blueprint(vote_bp)
    app.register_blueprint(bracket_bp)
    app.register_blueprint(admin_bp)

    return app
