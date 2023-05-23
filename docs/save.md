# Saving the model

## Table of contents
- [Basic usage](#basic-usage)
- [Saving Lifecycle](#saving-lifecycle)
- [Back to features content](../README.md#features)

## Basic usage
For save the model is as simple as calling `save()` method.

```python
foo = Foo(name='test')
foo.save()
```

This will add the object into the session, **but it doesn't flush it or commit it.**

According to [SQLAlchemy.Session.flush()](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.flush) The flush method performs pending transactions but if an error occurs, all transactions will be rolled back.

To flush the object you can pass the `flush=True` as a parameter.

```python
foo = Foo(name='test')
foo.save(flush=True)
```

**Important:** This only flush the current object.

It is important to mention that according the [SQLAlchemy.Session.commit()](https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.commit), transactions will not persist into the disk until a `commit()` is called. To do that, you can use `commit=True`.

```python
foo = Foo(name='test')
foo.save(commit=True)
```

**Important:** Unlike `flush`, to call `commit` will send all added transactions to be persisted into the disk, even if they doesn't set `flush=True`. So one `commit=True` can commit all the previous models that used `save()`

For more information about `flush` and `commit`, please check the [SQLAlchemy tutorial](https://docs.sqlalchemy.org/en/14/orm/tutorial.html).


## Saving lifecycle
When `save` is called, some other functions are called.
- First`before_validate` logic is executed.
- Then `validate` logic is executed.
- Then `custom_validation` is executed.
- Then `before_save` is executed.
- Then `save` logic is executed.
- Then `after_save` logic is executed.

So, for example if you want to add some logic before validating, you can override the `before_validate` method

```python
class Foo(db.Model):
    ...

    def before_validate(self, fields: list[str] | None = None) -> None:
        super().before_validate(fields)
        ...
```

You can override any of the previous methods.

It is also possible to define which fields you want to validate.

```python
foo = Foo(name='test')
foo.save(validate_fields=['name'])
```

This will only validate the name field.

It is also possible to define which fields you want to save, but this is only possible on an object that was previously saved, i.e., only in updates.

```python
foo = Foo(name='test', email='test@test.com')
foo.save(commit=True)
foo.populate(name='new test', email='Invalid test')
foo.save(fields=['name']) # This only validates and updates the name into the database.
```

---
[Back to features content](../README.md#features)
