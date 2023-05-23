import sqlalchemy as sa

from .validators import Validator
from ..models import Model

__all__ = ["ValidateColumn"]


class ValidateColumn(sa.Column):
    """Validate column with custom validation before."""

    inherit_cache = True

    def __init__(
        self,
        *args,
        validators: list[Validator] | None = None,
        check_unique: bool = False,
        **kwargs,
    ) -> None:
        """Init the object.

        Args:
            validators: List of validators to apply.
            check_unique: Optional; It will check in DB if the value is unique
                in validate method for this column if column has unique
                and this param as True.
        """
        self.validators = validators if validators else []
        self.check_unique = check_unique
        super().__init__(*args, **kwargs)

    def validate(self, model: Model, key: str | None = None) -> list[str]:
        """Validate Column.

        Args:
            model: Model to validate.
            key: Key used in model for the field, if it not specified,
                it will take the key self.
        Returns:
            A list with the errors if it has,
                otherwise return empty list.
        """
        if not key:
            key = self.key
        errors = []
        value = getattr(model, key)
        if not value and not self.nullable and self.foreign_keys:
            for key_obj, relationship in model.mapper.relationships.items():
                if relationship.local_columns == {self}:
                    if getattr(model, key_obj):
                        value = getattr(model, key_obj).pk
                    break

        for validator in self.validators:
            value, tmp_errors = validator.validate(value)
            errors += tmp_errors
        if (
            not self.nullable
            and value is None
            and not self.default
            and not self.primary_key
        ):
            errors.append("Can not be null or empty.")
        if value and not isinstance(value, self.type.python_type):
            errors.append(
                "Incorrect field type, it must be {}".format(
                    self.type.python_type.__name__
                )
            )
        elif (
            hasattr(self.type, "length")
            and value
            and self.type.length  # pyright: ignore[reportGeneralTypeIssues]
            and len(value) > self.type.length  # pyright: ignore
        ):
            errors.append(
                f"Value exceeeds allowed length ({len(value)}),"
                f"field has to be {self.type.length} or less"  # type: ignore
            )
        if value and self.unique and self.check_unique:
            if model.is_new or model.history_change(key).was_changed:
                if model.__class__.query.filter_by(**{key: value}).first():
                    errors.append("Field has to be unique;" f"{value} is already used.")
        setattr(model, key, value)
        return errors
