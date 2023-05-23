import pytest

from flask_model_validation import SQLAlchemyModelValidation
from flask_model_validation.models import mixins


@pytest.mark.usefixtures("app_ctx")
def test_id_mixin(db: SQLAlchemyModelValidation):
    """GIVEN A new `User` model needs to have the id as primary key
    WHEN a new `User` model is created with the SQLAlchemyModelValidation model
    THEN `IdMixin` should be used and generate the id as primary key.
    """

    class User(db.Model, mixins.IdMixin):
        pass

    db.create_all()
    user = User()
    user.save(commit=True)
    assert hasattr(user, "id")
    assert user.pk == user.id


@pytest.mark.usefixtures("app_ctx")
def test_timpestamp_mixin(db: SQLAlchemyModelValidation):
    """GIVEN A new `User` model needs to have created and updated attribute
    WHEN a new `User` model is created with the SQLAlchemyModelValidation model
    THEN `TimestampMixin` should be used and generate the fields.
    """

    class User(db.Model, mixins.IdMixin, mixins.TimestampMixin):
        name = db.ValidateColumn(db.String(12))

    db.create_all()
    user = User(name="Test")
    user.save(commit=True)
    assert hasattr(user, "created")
    assert user.created is not None
    created_time = user.created
    assert user.updated is None
    user.name = "Test 2"
    user.save(commit=True)
    assert created_time == user.created
    assert user.updated is not None
    assert user.updated > user.created


@pytest.mark.usefixtures("app_ctx")
def test_slug_mixin(db: SQLAlchemyModelValidation):
    """GIVEN A new `Status` will be used with slug
    WHEN a new `Catalog` model is created with the
        SQLAlchemyModelValidation model
    THEN `SlugMixin` should be used and generate the necessary fields.
    """

    class Status(db.Model, mixins.IdMixin, mixins.SlugMixin):
        name = db.ValidateColumn(db.String(20))
        slug = db.ValidateColumn(db.String(8), unique=True, nullable=False)

    db.create_all()
    status = Status(name="On Stock Virtual")
    with pytest.raises(NotImplementedError):
        status.save()
    Status.field_to_slugfy = "name"
    assert status.slug is None
    status.save(commit=True)
    assert status.slug == "on-stock"
    # Saving another with the same name and slug should be different.
    status_1 = Status(name="On Stock")
    status_1.save(commit=True)
    assert status_1.slug == "on-sto-1"
    status_2 = Status(name="On Stock")
    status_2.save(commit=True)
    assert status_2.slug == "on-sto-2"


@pytest.mark.usefixtures("app_ctx")
def test_catalog_mixin(db: SQLAlchemyModelValidation):
    """GIVEN A new `Status` model will be used as a Catalog
    WHEN a new `Catalog` model is created with the
        SQLAlchemyModelValidation model
    THEN `CatalogModelMixin` should be used and generate the necessary fields.
    """

    class Status(db.Model, mixins.CatalogModelMixin):
        pass

    db.create_all()
    status = Status(name="On Stock")
    status.save(commit=True)
    assert status.pk is not None
    assert status.pk == status.id
    assert status.created is not None
    assert status.is_active is True
    assert status.slug == "on-stock"


@pytest.mark.usefixtures("app_ctx")
def test_define_catalog_mixin(db: SQLAlchemyModelValidation):
    """GIVEN We want use the id of the define catalog
    WHEN A table was created with defined data
    THEN `DefineCatalogModel Mixin` should be used to get the data.
    """

    class Status(db.Model, mixins.DefineCatalogMixin):
        class CatalogMap:
            ON_STOCK = "on-stock"
            SOLD_OUT = "sold-out"
            REQUESTED = "requested"
            NOT_ADDED_TO_DATABASE = "not-added-to-database"

    db.create_all()
    for name in ["On Stock", "Sold Out", "Requested"]:
        status = Status(name=name)
        status.save(commit=True)

    on_stock = Status.catalog().ON_STOCK
    assert on_stock.name == "On Stock"
    # It will be the same memory direction if it was saved in cache.
    assert id(on_stock) == id(Status.catalog().ON_STOCK)
    assert Status.catalog().SOLD_OUT.name == "Sold Out"
    with pytest.raises(AttributeError):
        Status.catalog().NOT_IN_CATALOG
    # This element was added into the catalog but not into database.
    with pytest.raises(AttributeError):
        Status.catalog().NOT_ADDED_TO_DATABASE

    # Testing a not db.Model class
    class StatusNotModel(mixins.DefineCatalogMixin):
        class CatalogMap:
            ON_STOCK = "on-stock"
            SOLD_OUT = "sold-out"
            REQUESTED = "requested"

    with pytest.raises(NotImplementedError):
        StatusNotModel.catalog().ON_STOCK
