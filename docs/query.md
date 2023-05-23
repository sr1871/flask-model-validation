
## Query to the database

## Table of contents
- [Basic usage](#basic-usage)
- [Operators](#operators)
- [Join and query with relationships](#join-and-query-with-relationships)
- [Query via secondary table](#query-via-secondary-table)
- [Back to features content](../README.md#features)

## Basic usage

This extension makes easier to query to database. You can query via `find` with a `kwargs` parameter.

```python
foo = Foo.query.find(name='Bar').first()
# SELECT * FROM `foo` where `foo`.`name` = 'Bar' LIMIT 1
```

If you add multiple parameters it will added as conjunction `and`.

```python
foo = Foo.query.find(name='Bar', email='test@test.com').first()
# SELECT * FROM `foo` where `foo`.`name` = 'Bar' AND `foo`.`email` = 'test@test.com' LIMIT 1
```

## Operators

The `find` function allowed multiples concatenated operators with `__` as the parameter suffix. `{fieldname}__{operator}`

```python
foo = Foo.query.find(id__gt=5).all()
# SELECT * FROM `foo` where `foo`.`id` > 5
```
some of the operators allowed are.
### Any type
- `ne` (not equal)
- `in`
- `not_` (you can concatenate this to negate the value, for example `not_in`, `not_contains`, etc.

### Strings
- `contains`
- `icontains` (insensitive case)
- `startswith`
- `istartswith` (insensitive case)
- `endswith`
- `iendswith` (insensitive case)

### Numbers
- `gt` (greater than)
- `ge` (greater equals than)
- `lt` (less than)
- `le` (less equals than)

### Secondary relationship
- `has`

## Join and query with relationships
If you have a relationship defined in your model is possible to query via `{relationship_name}__{relationship_field}`

```python
class Foo(db.Model):
    ...
    bar_id = db.ValidateColumn(db.Integer, db.ForeignKey('bar.id'))

    bar = db.relationship('Bar', back_populates='foos')

# You can query through the relationship
Foo.query.find(bar__id=1).all()
# SELECT * FROM `foo` INNER JOIN `bar` ON `foo`.`bar_id` = `bar`.`id`  WHERE `bar`.`id` = 1
```

You can also query through a relation from another relation using the `cjoin` function. You must add all  relationships as `kwargs` parameter. If the relationship depends on another relationship, you must specify the relationship with `{relationship_parent}__` as a prefix. `Foo.query.cjoin(bar='bar', test='bar__test')`

```python
class Foo(db.Model):
    ...
    bar_id = db.ValidateColumn(db.Integer, db.ForeignKey('bar.id'))

    bar = db.relationship('Bar', back_populates='foos')

class Bar(db,Model):
    ...
    test_id = db.ValidateColumn(db.Integer, db.ForeignKey('bar.id'))

    foos = db.relationship('Foo', back_populates='bar')
    test = db.relationship('Test', back_populates='bars')

class Test(db.Model):
    ...

    bars = db.relationship('Bar', back_populates='test')


# You can query through the relationship
Foo.query.cjoin(bar='bar', test='bar__query').find(test__id=1).all()
"""
SELECT * FROM `foo`
    INNER JOIN `bar` ON `foo`.`bar_id` = `bar`.`id`
    INNER JOIN `test` ON `bar`.`test_id`= `test`.`id`
    WHERE `test`.`id` = 1
"""
```

It is also possible to do a `LEFT JOIN` instead of an `INNER JOIN` adding a `-` before of each value in the `kwargs` parameter.

```python
Foo.query.cjoin(bar='-bar', test='-bar__query').find(test__id=1).all()
"""
SELECT * FROM `foo`
    LEFT JOIN `bar` ON `foo`.`bar_id` = `bar`.`id`
    LEFT JOIN `test` ON `bar`.`test_id`= `test`.`id`
    WHERE `test`.`id` = 1
"""
```

## Query via secondary table
If you have an intermediary table, it is possible to query to the table if you define a relationships with `_has` as suffix and define the way to join them.

```python

class Foo(db.Model):
    ...
    bars = relationship('FooBar', back_populates='foo')
    bars_has = relationship('Bar', secondary=lambda:FooBar.__table__, viewonly=True
                            secondaryjoin='Bar.id==FooBar.bar_id')

class Bar(db.Model):
    ...
    foos = relationship('FooBar', back_populates='bar')

class FooBar(db.Model):
    id = ...
    bar_id = db.ValidateColumn(db.Integer, db.ForeignKey('bar.id'))
    foo_id = db.ValidateColumn(db.Integer, db.ForeignKey('foo.id'))

    bar = db.relationship('Bar', back_populates='foos')
    foo = db.relationship('Foo', back_populates='bars')


# Then query
Foo.find(bars__has=[1,5]).all()
"""
SELECT * FROM `foo`
    INNER JOIN `foo_bar` ON `foo`.`id` = `foo_bar`.`foo_id`
    INER JOIN `bar` ON `foo_bar`.`bar_id`= `bar`.`id`
    WHERE `bar`.`id` IN [1, 5]
"""
```

---
[Back to features content](../README.md#features)
