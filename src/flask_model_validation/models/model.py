from typing import Any

from sqlalchemy import inspect, orm
from sqlalchemy.orm.mapper import Mapper
from flask_sqlalchemy import model

from .. import extension as fmv
from .. import exceptions as ex

__all__ = ["Model"]


class Model(model.Model):
    """SQLAlchemy Model to do specific and customizable actions.

    Args:
        many_to_many_key_relation(str): This field is used to sufix of
            a many to many relationship. To use this its necessary add
            a relationship with an intermedary table and add
            two relationships, one to the intermedary table
            and one to the secondary table.

                class A:
                    b = relationship(C)
                    b_has = relationship(
                        B,
                        secondary=lambda: C.__table__,
                        viewonly=True,
                        secondaryjoin='B.id==C.b_id',
                        lazy='onload'
                    )

                class B:
                    c = relationship(C)

                class C:
                    a_id = db.ValidateColumn(db.Integer,
                                             db.ForeignKey('a.id'))
                    b_id = db.ValidateColumn(db.Integer,
                                             db.ForeignKey('b.id'))


                In this example `A` has a relationship with `B`
                through `C`. To get the objects of `B` in a direct way,
                we used the many to many relationship. The relationship
                is called `b_has`. The `has` is the value of the
                `many_to_many_key_relation ` attr, if you changed you
                have to name your b class as `b_{new_value}`.
    """

    many_to_many_key_relation = "has"

    @property
    def db(self) -> Any:
        """Gets the db from the SQLAlchemyModelValidation singleton."""
        return fmv.db().instance

    @property
    def pk(self) -> Any:
        """Returns the value of the primary key field."""
        primary_key_key = self.mapper.primary_key[0].key
        for col in self.mapper.column_attrs:
            if col.columns[0].key == primary_key_key:
                return getattr(self, col.key)

    @pk.setter
    def pk(self, value) -> None:
        """Set pk value."""

    @property
    def is_new(self) -> bool:
        """Returns if is it was not added yet to the database."""
        return bool(not self.pk)

    @property
    def force_pk(self) -> bool:
        """If pk is null, it will flush this object; Return the pk."""
        if self.pk:
            return self.pk
        self.db.session.add(self)
        self.db.session.flush([self])
        return self.pk

    @property
    def mapper(self) -> Mapper:
        """Gets the current mapper from sqlalchemy inspector."""
        mapper = inspect(self.__class__)
        if not mapper:
            raise Exception("Mapper it was not itialized")
        return mapper

    def populate(self, **kwargs) -> None:
        """Populates the object from dict data."""
        for field, value in kwargs.items():
            setattr(self, field, value)

    def before_save(self) -> None:
        """Function called before the data will be saved."""

    def after_save(self) -> None:
        """Function called after the data was saved."""

    def before_validate(self, fields: list[str] | None = None) -> None:
        """Function called before the data begins to be validated.

        Args:
            fields: fields that should be validated.
        """

    def validate(self, fields: list[str] | None = None) -> bool:
        """Validates the data.

        Args:
            fields: fields that should be validated.
                If it is None, it will validate all the fields
        Returns:
            If the data was valid.
        Raises:
            ValidateError: When at least one of the validation failed.
        """
        self.before_validate(fields)
        errors_map = {}
        for attr in self.mapper.attrs:
            if not isinstance(attr, orm.properties.ColumnProperty):
                continue
            field = getattr(self.__class__, attr.key)
            col = self.mapper.columns.get(field.key)
            if isinstance(col, fmv.ValidateColumn) and (
                not fields or field.key in fields
            ):
                errors = col.validate(self, field.key)
                if errors:
                    errors_map[field.key] = errors
        for field, custom_errors in self.custom_validation(fields).items():
            errors_map[field] = errors_map.get(field, []) + custom_errors
        if errors_map:
            raise ex.ValidateError(
                ex.MESSAGE_ERROR, errors=errors_map, model_class=self.__class__
            )

        return True

    def history_change(self, field: str) -> "HistoryField":
        """History change of specified field.

        Args:
            field: The field to get the history.
        Returns:
            A History model object.
        """
        return HistoryField(self, field)

    def custom_validation(self, fields: list[str] | None) -> dict[str, list[str]]:
        """Custom validation.

        Args:
            fields: fields that should be validated.
        Returns:
            A dict with field as key and a list of str detail errors.
        """
        return {}

    def save(
        self,
        flush: bool = False,
        commit: bool = False,
        fields: list[str] | None = None,
        validate_fields: list[str] | None = None,
    ) -> bool:
        """Saves the model in a dynamic way.

        Args:
            flush: Optional; if it's True, it will be sended to database
                without commit it yet.
            commit: Optional; if it's True, it will commit to
                the session.
            fields: Fields that wants to update, this only work
                with update, if this param is used in create action,
                will be raise an ValueError.
            validate_fields: Fields that wants to validate, if it NULL,
                `validate_fields` will take the `fields` param.
        Returns:
            bool: If the data was saved.
        Raises:
            ValueError: If fields is used in a new object.
        """
        self.validate(validate_fields if validate_fields else fields)
        self.before_save()
        if fields:
            if self.is_new:
                raise ValueError(
                    "`fields` param in `save' only can be used in update, \
                                  not in new object"
                )
            query = self.__class__.query
            fields_to_update = {field: getattr(self, field) for field in fields}
            query.find(pk=self.pk).update(fields_to_update)
        else:
            self.db.session.add(self)
        if commit:
            self.db.session.commit()
        elif flush:
            self.db.session.flush([self])
        self.after_save()
        return True

    def after_delete(self) -> None:
        """Function called after the data was deleted."""

    def delete(self, commit: bool = False) -> bool:
        """Delete the model from database.

        This doesn't delete the object from python.

        Args:
            commit: Optional; if its True, it will commit to the session.
        Returns:
            bool: If the data was deleted.
        """
        self.db.session.delete(self)
        if commit:
            self.db.session.commit()
        self.after_delete()
        return True


class HistoryField:
    """Class used for history from a specific field."""

    def __init__(self, model: Model, field: str):
        """Init Object.

        Args:
            model: Model from which to obtain the field.
            field: The field name from which to obtain the history.
        """
        history = orm.attributes.get_history(model, field)
        self.history = history
        if (
            history.unchanged
            or model.is_new
            or (not history.deleted and not history.added)
        ):
            self.was_changed = False
            self.previous_value = None
            self.current_value = None
        else:
            self.was_changed = True
            self.previous_value = history.deleted[0] if history.deleted else None
            self.current_value = history.added[0] if history.added else None

    def __repr__(self):
        """Tranform to str representation."""
        return str(self.history)
