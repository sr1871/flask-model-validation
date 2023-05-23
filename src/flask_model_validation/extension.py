from typing import Any, Self

from flask_sqlalchemy import SQLAlchemy

from flask import Flask

from .query import Query
from .models import Model
from .validation import ValidateColumn

__all__ = ["SQLAlchemyModelValidation", "db"]


class SQLAlchemyModelValidation(SQLAlchemy):
    """Extending from SQLAlchemy to add new properties."""

    instance: Self | None = None

    def __init__(
        self,
        app: Flask | None = None,
        *,
        query_class: type[Query] = Query,
        model_class: type[Model] = Model,
        **kwargs,
    ):
        """Overriding the `query_class` by default."""
        super().__init__(
            app, query_class=query_class, model_class=model_class, **kwargs
        )

    def __getattr__(self, name: str) -> Any:
        if name == "ValidateColumn":
            return ValidateColumn
        return super().__getattr__(name)

    def __new__(cls):
        """Applying singleton for this class."""
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance


def db() -> SQLAlchemyModelValidation:
    """Get the singleton for SQLAlchemyModelValidation."""
    if SQLAlchemyModelValidation.instance:
        return SQLAlchemyModelValidation.instance
    raise NotImplementedError(
        "The db through `SQLAlchemyValidation hasn't` been created"
    )
