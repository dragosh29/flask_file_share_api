import os

from flask import Flask
from app.extensions import db


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BASE_UPLOAD_DIR'] = 'artefacts'

    db.init_app(app)
    os.makedirs(app.config['BASE_UPLOAD_DIR'], exist_ok=True)

    with app.app_context():
        from app.models import Artefact
        db.create_all()

        from app.routes import main
        app.register_blueprint(main)

    return app
