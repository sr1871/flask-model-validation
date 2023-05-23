from datetime import datetime
from typing import Any

import sqlalchemy as sa
import slugify

from ..validation import ValidateColumn
from ..models import Model
from .. import extension as ex

__all__ = [
    "IdMixin",
    "TimestampMixin",
    "SlugMixin",
    "CatalogModelMixin",
    "CatalogModelMixin",
]


class IdMixin:
    """Mixin used to add id.

    Args:
        id(int): Database primary key.
    """

    id = ValidateColumn(sa.Integer, primary_key=True)

    @property
    def pk(self) -> Any:
        """Returns the primary key field."""
        return self.id


class TimestampMixin:
    """Mixin used to add created and updated attributes.

    Args:
        created(DateTime): Default; now();
            Time when the row was created.
        updated_at(DateTime): Default now(); Optional;
            Time when the row was updated.
    """

    created = ValidateColumn(
        "created_at", sa.DateTime, nullable=False, default=datetime.utcnow
    )
    updated = ValidateColumn("updated_at", sa.DateTime, onupdate=datetime.utcnow)


class SlugMixin(Model):
    """Mixin used to add slug field and generate it.

    Args:
        slug(string): Unique; Unique slug for slug.
    """

    slug = ValidateColumn(sa.String(24), unique=True, nullable=False)
    field_to_slugfy: str | None = None

    @property
    def field_to_slugfy_value(self):
        """Value of the field to slugfy."""
        if not self.field_to_slugfy:
            raise NotImplementedError("You must to specify `field_to_slugfy`")
        return getattr(self, self.field_to_slugfy)

    def before_validate(self, fields: list[str] | None = None) -> None:
        """Overriden for avoid empty slug throw an error."""
        if not self.slug:  # pyright: ignore[reportGeneralTypeIssues]
            self.generate_slug()
        super().before_validate(fields)

    def generate_slug(self) -> None:
        """Generate the slug and assigned."""
        if (
            self.is_new
            or self.history_change(self.field_to_slugfy).was_changed  # pyright: ignore
        ):
            self.slug = slugify.slugify(self.field_to_slugfy_value)
            self.truncate_slug()
            slug_used = self.query.find(slug=self.slug).first()
            if slug_used and slug_used.pk != self.pk:
                additional_data = 1
                tmp_slug = self.slug
                while slug_used and slug_used.pk != self.pk:
                    self.slug = f"{tmp_slug}-{additional_data}"
                    if (
                        len(self.slug)
                        > self.mapper.columns.get("slug").type.length  # pyright: ignore
                    ):
                        self.slug = (
                            str(tmp_slug[: -(len(str(additional_data)) + 1)])
                            + "-"
                            + str(additional_data)
                        )
                    slug_used = self.query.find(slug=self.slug).first()
                    additional_data += 1

    def truncate_slug(self) -> None:
        """Make the slug according the length of the db length."""
        allowed_length = self.mapper.columns.get("slug").type.length  # pyright: ignore
        while len(self.slug) > allowed_length:  # pyright: ignore
            self.slug = "-".join(self.slug.split("-")[:-1])


class CatalogModelMixin(IdMixin, SlugMixin, TimestampMixin):
    """Mixin used for all catalog Model.

    That include a table that contain: `name`, `slug`,
    `created_at`, `updated_at`

    Args:
        **IdMixin field added into the model.
        name: The name of the row in the catalog.
        **SlugMixin field added into the model.
        **Timestamps fields added into the model.
    """

    name = ValidateColumn(sa.String(24), nullable=False)
    is_active = ValidateColumn(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.sql.expression.true(),
    )

    # Define the field to slugfy
    field_to_slugfy = "name"


class DefineCatalogMixin(CatalogModelMixin):
    """Define allowed options for a catalog.

    class SomeCatalog(DefineCatalogMixin):
        If define the catalog class with other name it must be
        specified the class name in `catalog_class_name`= attr

        class CatalogMap:
            ALLOWED_1: 'allowed_one'

    then it is possible get the element like

    SomeCatalog.catalog().ALLOWED_1 and it will be the ORM object.

     Args:
        **CatalogModelMixin
        catalog_class_name: Name of the class used for the catalog;
            Default will be `CatalogMap`
        catalog_field: The name of the field used for search
            in the catalog; Default `slug`
    """

    class CatalogMap:
        """Define the allowed catalog."""

    class _CatalogObj:
        def __init__(self, model):
            """Pass the parent to allow use query inside the catalog."""
            self.model = model
            self.cache = {}

        def __getattr__(self, attr):
            """Get attr magic method."""
            catalog_class = getattr(self.model, self.model.catalog_class_name)
            key = getattr(catalog_class, attr, None)
            if not key:
                raise AttributeError(f"{key} does not exist in the catalog")
            return self.get_element(key)

        def get_element(self, key: str) -> Any:
            """Get element from the database."""
            if key in self.cache:
                return self.cache[key]
            query = getattr(self.model, "query", None)
            if not query:
                raise NotImplementedError("The class must extend from db.Model")
            element = query.find(**{self.model.catalog_field: key}).first()
            if not element:
                raise AttributeError(f"Element with key {key} does not exist.")
            ex.db().session.expunge(element)
            self.cache[key] = element
            return element

        def key(self, key: str):
            """Get element from str key."""
            return self.get_element(key)

    @classmethod
    def catalog(cls):
        """Init the catalog."""
        if not cls._catalog:
            cls._catalog = cls._CatalogObj(cls)
        return cls._catalog

    catalog_class_name = "CatalogMap"
    catalog_field = "slug"
    # Obj for can call the element from the Catalog.
    _catalog: _CatalogObj | None = None
