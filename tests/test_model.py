import pytest

from flask_model_validation import SQLAlchemyModelValidation
from flask_model_validation.validation import validators as v
from flask_model_validation import exceptions as ex


@pytest.mark.usefixtures("app_ctx")
def test_model_functions(db: SQLAlchemyModelValidation):
    """GIVEN functions of the model will be used
    WHEN a new `User` model is created with the SQLAlchemyModelValidation model
    THEN the user called this functions from the model.
    """

    class User(db.Model):
        id = db.ValidateColumn("changing_id", db.Integer, primary_key=True)
        name = db.ValidateColumn("changing_name", db.String)

    db.create_all()
    # Set to False the `autoflush` to test the save options.
    db.session.autoflush = False
    user = User(name="test")
    assert user.pk is None
    assert user.force_pk is not None
    assert user.pk == user.id
    assert user.force_pk == user.id
    user.populate(name="test2")
    assert user.name == "test2"


@pytest.mark.usefixtures("app_ctx")
def test_save_model(db: SQLAlchemyModelValidation):
    """GIVEN A new user will be saved in the database
    WHEN a new `User` model is created with the SQLAlchemyModelValidation model
    THEN the user should be saved into the database invoking `save` method.
    """

    class User(db.Model):
        id = db.ValidateColumn("changing_id", db.Integer, primary_key=True)
        name = db.ValidateColumn(
            "changing_name", db.String, unique=True, check_unique=True, nullable=False
        )

    db.create_all()
    # Set to False the `autoflush` to test the save options.
    db.session.autoflush = False
    user = User(name="test")

    # User is added to the session but not flushed or commited
    user.save()
    assert user in db.session.new
    assert user.pk is None
    assert User.query.find(name="test").first() is None
    # User is flushed so it should have its own pk and be in database.
    user.save(flush=True)
    assert user.pk is not None
    assert user == User.query.find(name="test").first()
    # Rollback the data, the data should be not saved to database.
    db.session.rollback()
    assert User.query.find(name="test").first() is None
    # User should persist because it was commited.
    user.save(commit=True)
    assert user == User.query.find(name="test").first()
    db.session.rollback()
    assert user == User.query.find(name="test").first()
    user = User(name="test")
    # Testing unique and check_unique params
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    assert "name" in error.value.errors
    # Save with `fields` param only could be done on not new objects.
    user.name = "test 2"
    with pytest.raises(ValueError):
        user.save(fields=["name"])
    user.save(commit=True)
    user.name = "test 3"
    user.save(fields=["name"], commit=True)
    assert user == User.query.find(name="test 3").first()


@pytest.mark.usefixtures("app_ctx")
def test_validate_model(db: SQLAlchemyModelValidation):
    """GIVEN A new user will be saved in database
    WHEN a new `User` model is created with the
        SQLAlchemyModelValidation model
    THEN the user should be saved into the database invoking `save` method.
    """

    class User(db.Model):
        id = db.ValidateColumn(db.Integer, primary_key=True)
        name = db.ValidateColumn(db.String(6), nullable=False)
        email = db.ValidateColumn(db.String(24), validators=[v.EmailValidator()])

    db.create_all()
    # User is created with wrong email according to validator
    # and not name when is required.
    user = User(email="test")
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    # name should be added and email is not a valid email.
    assert error.value.model_class == User
    assert all([attr in error.value.errors for attr in ["name", "email"]])
    # Using populate to change the data to a not valid length data.
    user.populate(name="TestTheLength", email="test@test.com")
    assert user.validate(fields=["email"])
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    assert "name" in error.value.errors
    # Changing name for the user.
    user.name = 3
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    assert "name" in error.value.errors
    user.name = "test"
    assert user.save()


@pytest.mark.usefixtures("app_ctx")
def test_validate_lifecycle(db: SQLAlchemyModelValidation):
    """GIVEN a custom save lifecyle wants to be added
    WHEN a new `User` model is created with the SQLAlchemyModelValidation model
    THEN the user should invoke `before_validate` and
        `before_save` and `after_save`.
    """

    class User(db.Model):
        id = db.ValidateColumn(db.Integer, primary_key=True)
        email = db.ValidateColumn(
            db.String(25), validators=[v.EmailValidator()], nullable=False
        )

        def before_validate(self, fields):
            if (not fields or "email" in fields) and self.email == 1:
                self.prev = 1
                self.email = "test@test.com"

        def custom_validation(self, fields):
            if (not fields or "email" in fields) and self.email == "test2@test.com":
                return {"email": ["This email is not allowed"]}
            return {}

        def before_save(self):
            if hasattr(self, "prev"):
                self.email = str(self.prev)

        def after_save(self):
            self.email = "test@test.com"
            pass

    db.create_all()
    # Set to False the `autoflush` to test the save options.
    db.session.autoflush = False
    user = User(email="3")
    # new User should rase a ValidateError for the email validator
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    assert "email" in error.value.errors
    # Trying custom validations.
    user.email = "test2@test.com"
    with pytest.raises(ex.ValidateError) as error:
        user.save()
    assert "email" in error.value.errors
    user.email = 1
    assert user.save(commit=True)
    assert user.pk is not None
    assert user.email == "test@test.com"
    assert User.query.find(email="1").first().pk == user.pk
    assert User.query.find(email="test@test.com").first() is None


@pytest.mark.usefixtures("app_ctx")
def test_delete_model(db: SQLAlchemyModelValidation):
    """GIVEN a user that should be deleted from the database
    WHEN the `delete` method is invoked
    THEN the user should be deleted from the database.
    """

    class User(db.Model):
        id = db.ValidateColumn(db.Integer, primary_key=True)

        def after_save(self):
            self.deleted = True

    db.create_all()
    # Set to False the `autoflush` to test the save options.
    db.session.autoflush = False
    user = User()
    user.save(commit=True)
    assert User.query.find().first() is not None
    user.delete(commit=True)
    assert User.query.find().first() is None
    assert user.deleted


@pytest.mark.usefixtures("app_ctx")
def test_history_field(db: SQLAlchemyModelValidation):
    """GIVEN a user that should be deleted from the database
    WHEN the `delete` method is invoked
    THEN the user should be deleted from the database.
    """

    class User(db.Model):
        id = db.ValidateColumn(db.Integer, primary_key=True)
        name = db.ValidateColumn(db.String(24))

    db.create_all()
    # Set to False the `autoflush` to test the save options.
    db.session.autoflush = False
    user = User(name="Test")
    h = user.history_change("name")
    assert not h.was_changed
    assert h.previous_value is None
    assert h.current_value is None
    user.save(commit=True)
    user_from_db = User.query.find(name="Test").first()
    h = user_from_db.history_change("name")
    assert not h.was_changed
    assert h.previous_value is None
    assert h.current_value is None
    user.name = "Test2"
    h = user_from_db.history_change("name")
    assert h.was_changed
    assert h.previous_value == "Test"
    assert h.current_value == "Test2"
