from collections.abc import Generator

import pytest
from flask import Flask
from flask.ctx import AppContext

from flask_model_validation import SQLAlchemyModelValidation


@pytest.fixture
def app() -> Flask:
    """Creates and returns the Flask app for tests."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    return app


@pytest.fixture
def app_ctx(app: Flask) -> Generator[AppContext, None, None]:
    """Creates a enviroment with app context for allow to use the app."""
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def db(app: Flask) -> SQLAlchemyModelValidation:
    """Creates and returns the database model for tests."""
    db = SQLAlchemyModelValidation()
    db.init_app(app)
    return db
