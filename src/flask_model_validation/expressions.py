from collections.abc import Callable

from sqlalchemy.sql import elements as sqlelements
import sqlalchemy

from .query import Query

__all__ = ["or_", "and_", "_"]


def conditional_expression(
    expression: Callable, *args, **kwargs
) -> Callable[[Query], sqlelements.BinaryExpression]:
    """Logic for conditionals (`or` and `and`)."""

    def _internal_expression(query: Query):
        if not isinstance(query, Query):
            raise ValueError("The query object must be a object" "of `CustomQuery`")
        criterion = query.make_criterion(**kwargs)
        for subexpression in args:
            criterion.append(subexpression(query))
        return expression(*criterion)

    return _internal_expression


def or_(*args, **kwargs):
    """Concatenates two or more condition with `or` operator for `find` query.

    Conditional should be used as

        `Model.query.find(or_(name='foo', lastname='bar'))`

    Also it could be used as nested condition

        `Model.query.find(or_(and_(name='foo', age='19'),
                          and_(name='bar', age='25')))`

    If you want to use the same keyword for the same expression,
    use `_` function.

        `Model.query.find(or_(_(name='Foo'), _(name='Bar')))`
    """
    return conditional_expression(sqlalchemy.or_, *args, **kwargs)


def and_(*args, **kwargs):
    """Concatenates two or more condition with `or` operator for `find` query.

    Conditional should be used as

        `Model.query.find(and_(name='foo', lastname='bar'))`

    Also it could be used as nested condition

        `Model.query.find(or_(and_(name='foo', age='19'),
                          and_(name='bar', age='25')))`
    """
    return conditional_expression(sqlalchemy.and_, *args, **kwargs)


def _(**kwargs):
    """Used for add multiple values for the same keyword.

        `Model.query.find(or_(_(name='Foo'), _(name='Bar')))`

    It only allowed one keyword for function. if you add more than one
    it only take the first one

        `_(name='Foo', lastname='Bar')` it only take `name=Foo`
    """

    def _internal_expression(query: Query):
        c = query.make_criterion(**kwargs)
        return c[0]

    return _internal_expression
