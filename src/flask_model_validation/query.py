import operator as op
from typing import Any

from flask_sqlalchemy import query
from sqlalchemy import Column

__all__ = ["Query"]


class Query(query.Query):
    """override filter to do it dynamic."""

    FORMATS: dict[str, tuple] = {
        "contains": ("like", "%{}%"),
        "icontains": ("ilike", "%{}%"),
        "startswith": ("like", "{}%"),
        "istartswith": ("ilike", "{}%"),
        "endswith": ("like", "%{}"),
        "iendswith": ("ilike", "%{}"),
    }
    NOT = "not_"

    def __init__(self, *args, **kwargs):
        """Init object.

        Create a dict for custom joins.
        """
        super().__init__(*args, **kwargs)
        self._map_joins = {}

    def find(self, *args, **kwargs):
        """Find use operators like others python ORM.

        It include, __ne, __ge, __gt, __lt, __le, __in, __contains.
        This let make a query like Model.find(id__ne=4)

        It is possible to search through relationship with `__`
        Foo.query.find(bar__name='name') joins the two classes
        with a EXISTS statement and search where bar name is `name`.

        Args:
            args: expressions for `or_` and `and_`
            kwargs: Dict with key field in model,
                and value as value to filter in db.
        Returns:
            Filter classic query in SQLAlchemy.
        """
        return self.filter(*self.make_criterion(*args, **kwargs))

    def cjoin(self, **kwargs: str):
        """Create a join where it's possible to search in `find`.

        This only will work if exists a relationship between two tables.
        The key should be the alias, and the value the name of the
        relationship in main model.

            Foo:
                others = relationship(Other ...)
                ...
            Foo.query.cjoin(other='others').find(other__name='foo')

        It is possible to do many joins at the same time.

            Foo:
                others = relationship(Other ...)
                action = relationship(Action ...)
            Foo.query.cjoin(other='others, alias_action='action'])
                .find(other__name='foo', alias_action__id__ne=3)

        It is possible to do a nested join from a relationship.
        For that is necessary pass in the value
        `{alias_selected}__relationship_name` for example

            Foo:
                others = relationship(Other ...)
                action = relationship(Action ...)

            Other:
                animals = relationship(Animal ...)
                flower = relationship(Flower ...)

            Foo.query.cjoin(
                other='others',
                animal='others__animals',
                color='animal__color',
                alias_actions='action'
            ).find(
                other__name='foo',
                alias_action__id__ne=3,
                color__name='red'
            ).all()


        To join with `color` it set the prefix `animals` in value of
        Color alias. This is because Color has the relationship with Animal,
        and `animal` is the alias that was choosen for animal alias
        `animal='others__animals'`. For that reason we need to do the
        relationship with `Animal` mandatory if wants to use `Color`,
        for animal relationship it does it through `others`,
        an alias for `others` is `other`.
        It is important added in right order.

        For example if want to use
            `animal='others__animals'`

        it is necessary add first

            (..., `other='others', animal='others__animals'`, ..)

        It is not possible add first in args `animal` and then `other`.

        To set left join begin the value with a `-`

            Foo.query.cjoin(other='-others').find(other__name='foo')

        Will produce a `Foo LEFT join OTHER`

        To use `find`, please refear to `find`

        Returns:
            Join classic query in SQLAlchemy.
        """
        class_ = self._entity_from_pre_ent_zero().class_
        query = self
        for alias, relationship in kwargs.items():
            model_class = class_
            isouter = False
            # This means the join should be left join.
            if relationship.startswith("-"):
                isouter = True
                relationship = relationship[1:]
            if "__" in relationship:
                model_class, relationship = relationship.split("__")
                model_class = self._map_joins[model_class]
            join_class = model_class.__mapper__.relationships.get(
                relationship
            ).mapper.class_
            self._map_joins[alias] = join_class
            query = query.join(
                join_class, getattr(model_class, relationship), isouter=isouter
            )

        return query

    def _args_to_columns(self, *args) -> list[Column]:
        """Converts a list of `str` to a list of sqlachmey operators.

        To be used with a relationship, is needed to use `cjoin`
        This convert for example `id` in Foo.id if the query object
        belong to `Foo` class.

        Also is posible to use with relationship `bar__id`,
        this will be converted into Bar.id.

        This is used in `custom_columns` and `custom_entities`

        This also could contain directly `Foo.name` orm
        sqlalchemy functions. In that case, it would
        not do anything to that columns.
        """
        columns = []
        for column in args:
            try:
                # Checks if the column value is a sequence (func, field_name)
                func, column = column
            except (ValueError, NotImplementedError):
                # NotImplementedError is for can pass `Foo.id`
                func = None
            # Doc: Means it comes from a alias used in join:
            if isinstance(column, str) and "__" in column:
                model_class, relationship = column.split("__")
                column = getattr(self._map_joins[model_class], relationship)
            columns.append(column if not func else func(column))
        return columns

    def add_join_columns(self, *args):
        """Add custom columns.

        This can work as `add_columns` (`Foo.name`
        or `sql.fun.count(Foo.name)`) or with aliases
        used in `cjoin`. To do this pass as `{alias_model}__field`.

            Foo.query.cjoin(Bar='bars').add_join_columns('bar__name')

        To use aliases with function is needed passing as sequence,
        instead pass the value inside the function

            Foo.query.cjoin(Bar='bars')
                .add_custom_columns((sql.func.count, 'bar__name'))
        """
        return self.add_columns(*self._args_to_columns(*args))

    def join_entities(self, *args):
        """Select the columns that wants to return..

        This can work as `with_entities` (`Foo.name`
        or `sql.fun.count(Foo.name)`) or with aliases
        used in `cjoin`. To do this pass as `{alias_model}__field`.

            Foo.query.cjoin(Bar='bars').custom_entities('bar__name')

        To use aliases with functions is needed passing as sequence,
        instead pass the value insidethe function

            Foo.query.cjoin(Bar='bars')
                .custom_entities((sql.func.count, 'bar__name'))
        """
        return self.with_entities(*self._args_to_columns(*args))

    def make_criterion(self, *args, **kwargs):
        """`Find` use operators like others python ORM.

        It include, __ne, __ge, __gt, __lt, __le, __in,
            __contains, __icontains, __startswith, __istartswith,
            __endswith, __iendswith, __has.
        `This let make a query like Model.find(id__ne=4)`

        It is also possible to add a negative condition adding the
        prefix `not_` to the operator. For example `__not_contains`
        This let make a query like `Model.find(name__not_in=[1,2])`

        Args:
            args: Expressions for or_, and_.
            kwargs: Dict with key field in model,
                and value as value to filter in db.
        Returns:
            A list of criterions.
        """
        model_class = self._entity_from_pre_ent_zero().class_
        criterion = []
        for expression in args:
            criterion.append(expression(self))
        for key, value in kwargs.items():
            # If value is a func, means that is an expression,
            # We only add the result of it.
            condition = (
                self.get_condition(model_class, key, value)
                if not callable(value)
                else value(self)
            )
            criterion.append(condition)
        return criterion

    def get_condition(self, model_class: Any, key: Any, value: Any) -> Any:
        """Get condition for `find` query.

        Args:
            model_class: The model class.
            key: Name of the field.
            value: Value to field query.
        Returns:
            A condition to add in filter super()
        """
        if "__" in key:
            key_split = key.split("__")
            key_string = key_split[0]
            operator_key = "__".join(key_split[1:])
            # Check if is a field of a join class.
            if key_string in self._map_joins:
                return self.get_condition(
                    self._map_joins[key_string], operator_key, value
                )
            # Return a invert operator if starts with `not_``
            if operator_key.startswith(self.NOT):
                key = f"{key_string}__{operator_key.split(self.NOT)[1]}"
                return op.invert(self.get_condition(model_class, key, value))
            key = getattr(model_class, key_string)
            if operator_key in ["ne", "ge", "gt", "lt", "le"]:
                return getattr(op, operator_key)(key, value)
            if operator_key == "in":
                return key.in_(value if isinstance(value, list) else [value])
            if operator_key in self.FORMATS:
                format_tmp = self.FORMATS[operator_key]
                return getattr(key, format_tmp[0])(format_tmp[1].format(value))
            if operator_key == "has":
                key_string = (
                    f"{key_string}" + f"_{model_class.many_to_many_key_relation}"
                )
                key = getattr(model_class, key_string)
            relationship = model_class.__mapper__.relationships.get(key_string)
            if relationship:
                return self._get_condition_relationship(
                    key, operator_key, relationship.mapper.class_, value
                )
        return op.eq(getattr(model_class, key), value)

    def _get_condition_relationship(
        self, key: Any, operator_key: str, submodel_class: Any, value: Any
    ) -> Any:
        """Gets the condition in relationships.

        Args:
            key: Column in model table to get information.
            operator_key: In this case will be has,
                otherwise it take as a field of submodel.
            submodel_class: Submodel in model.
            value: The Value for the final attribute.
        Returns:
            Query data.
        """
        query_action = "has"
        filter_data = {}
        if operator_key == "is_empty":
            return ~key.any() if value else key.any()
        if operator_key == "has":
            prefix = "__in"
            operator_key = submodel_class.__mapper__.primary_key[0].name
            query_action = "any"
            operator_key += prefix
        filter_data[operator_key] = value
        return_data = getattr(key, query_action)(
            *submodel_class.query.make_criterion(**filter_data)
        )
        return return_data
