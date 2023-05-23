import re
from typing import Any

__all__ = ["Validator", "EmailValidator"]


class Validator:
    """Validator fo ValidateColumn class."""

    def __init__(self):
        """Init the object."""
        self.errors: list[str] = []

    def validate(self, value: Any) -> tuple[Any, list[str]]:
        """Do the validation.

        Args:
            value: Value to validate.
        Returns:
            Return the value
            Return A list of errors if it has any,
                otherwise returns an empty list.
        """
        raise NotImplementedError()


class EmailValidator(Validator):
    """Validator for email."""

    def __init__(self, regex: str | None = None):
        """Init the object.

        Args:
            regex(str): Regex to validate the email value.
        """
        self.regex = regex
        if not self.regex:
            self.regex = (
                r'^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))'
                + r"@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])"
                + r"|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
            )
        super().__init__()

    def validate(self, value: str | None) -> tuple[str | None, list[str]]:
        """Do validation.

        Args:
            value: Value to validate.
        Returns:
            Return the value.
            Return A list of errors if it has any,
                otherwise return a empty list.
        """
        errors = []
        if not isinstance(value, str) or (
            value
            and not re.search(
                self.regex, value  # pyright: ignore[reportGeneralTypeIssues]
            )
        ):
            errors.append(f"{value} is not a valid email")
        return value, errors


class RequiredValidator(Validator):
    """Validator for required."""

    def __init__(self, allow_empty: bool = False, allow_null: bool = False):
        """Init the object.

        Args:
            allow_empty(bool): If it allow empty value.
            allow_null(bool): If it allow null.
        """
        self.allow_empty = allow_empty
        self.allow_null = allow_null
        super().__init__()

    def validate(self, value: Any) -> tuple[str, list[str]]:
        """Do validation.

        Args:
            value: Value to validate.
        Returns:
            Return the value.
            Return A list of errors if it has any,
                otherwise returns a empty list.
        """
        errors = []
        if not self.allow_null and value is None:
            errors.append("Value can not be null")
        elif not self.allow_empty and not value:
            errors.append("Value can not be empty")
        return value, errors
