from flask_sqlalchemy.model import Model

MESSAGE_ERROR = "There were some errors."

__all__ = ["ValidateError", "MESSAGE_ERROR"]


class ValidateError(Exception):
    """Exception for validation."""

    def __init__(
        self,
        *args,
        errors: dict[str, list[str]],
        model_class: type[Model] | None = None,
    ) -> None:
        """Init object.

        Args:
            errors: Errors in a dict, where the key is the field
                and the value is a validation list error.
            model_class: model Class that has the validation errors.
        """
        self.errors = errors
        self.model_class = model_class
        super().__init__(*args)

    def __str__(self) -> str:
        message = super().__str__() + "\n"
        for attr, errors in self.errors.items():
            message += f"{attr}: {errors}"
        return message
