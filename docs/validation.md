# Validation

## Table of contents
- [ValidateColumn](#validatecolumn)
- [Validators](#validators)
- [Back to features content](../README.md#features)

## ValidateColumn
You can use a `ValidateColumn` instead the classic `Column` in `Flask-SQLAlchemy`

```python
class Foo(db.Model):
    id = db.ValidateColumn(db.Integer, primary_key=True)
    name = db.ValidateColumn(db.String(8), nullable=False)
```

What will the `ValidateColumn` do? It will validate the basic structure before save it.

For example.

```python
foo = Foo(name="Bar")
foo.save() # For more info on the `save` method see 'saving' section of this document.
```
It will validate that the `name` in `foo`
- Is **type:string**
- **Is not null**
- **The value length is 8 or less**

```python
foo = Foo(name="123456789")
foo = Foo(name=12345)
foo = Foo()
foo.save()
```
In the examples above, all will fail validation, the first for exceeding the length, the second for value type and the third for having the `name=None` when `nullable=False`. This examples throw an exception of type `flask_model_validation.exceptions.ValidationError`

## Validators

You can add additional validation on each column with validators.

```python
from flask_model_validation import validators as v

class Foo(db.Model):
    id = db.ValidateColumn(db.Integer, primary_key=True)
    name = db.ValidateColumn(db.String(8), nullable=False, validators=[v.RequiredValidator()])
    email = db.ValidateColumn(db.String(15), nullable=False, validators=[v.EmailValidator()])
```

Each **validator** add an additional validation layer to the column where it was added. `name` will validate that the value is not empty (`name=''`) and `email` will validate that the value is an email of type `name@domain.com`.

```python
foo = Foo(name='', email='email') # Fail on name and email
foo = Foo(name='Bar', email='example@test.com') # Pass validation
```

You can created your own **validators** inheriting from the `flask_model_validation.validators.Validator` class. You just need to implement

```python
def validate(self, value: Any) ->tuple[Any, list[str]]:
    """Do the validation.
    Args:
        value: Value to validate.
    Returns:
        Return the value
        Return A list of errors if it has any, otherwise return an empty list.
    """
```

There are **preloaded validators**.
- `EmailValidator(regex: str | None = None))`
- `RequiredValidator(allow_empty: bool = False, allow_null: bool = False)`

---
[Back to features content](../README.md#features)
