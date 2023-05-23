import pytest

import flask_model_validation.exceptions as ex
from flask_model_validation import SQLAlchemyModelValidation
from flask_model_validation.validation import validators


def test_email_validator():
    """GIVEN `EmailValidator` is used
    WHEN a new user is created
    THEN a valid user should be approved
    """
    validator = validators.EmailValidator()
    _, errors = validator.validate("test@test.com")
    assert errors == []
    _, errors = validator.validate("test@com")
    assert errors != []


def test_required_validator():
    """GIVEN `EmailValidator` is used
    WHEN a new user is created
    THEN a valid user should be approved
    """
    validator = validators.RequiredValidator()
    _, errors = validator.validate("")
    assert errors != []
    _, errors = validator.validate(None)
    assert errors != []
    _, errors = validator.validate("test")
    assert errors == []


@pytest.mark.usefixtures("app_ctx")
def test_custom_validator(db: SQLAlchemyModelValidation):
    """GIVEN a field add a customValidator
    WHEN a custom validator is created
    THEN the validation should be executed
    """

    class NotGreaterThanTenValidator(validators.Validator):
        def validate(self, value):
            errors = []
            if value > 10:
                errors.append("Value should be less than 10")
            return value, errors

    class User(db.Model):
        id = db.ValidateColumn(db.Integer, primary_key=True)
        age = db.ValidateColumn(db.Integer, validators=[NotGreaterThanTenValidator()])

    db.create_all()
    user = User(age=12)
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    assert error.value.model_class == User
    assert (
        str(error.value)
        == f"{ex.MESSAGE_ERROR}\nage: {['Value should be less than 10']}"
    )
