# Mixins
Sometimes, there are some columns that are added in many models. Instead of adding one by one you can added by mixins. There are some **preloaded mixing**

## Table of contents

- [IdMixin](#idmixin)
- [TimestampMixin](#timestampmixin)
- [SlugMixin](#slugmixin)
- [CatalogModelMixin](#catalogmodelmixin)
- [DefineCatalogMixin](#defincatalogmixin)
- [Back to features content](../README.md#features)

## IdMixin

It will add an `id` column as primary key

```python
from flask_model_validation.models import mixins

class Foo(db.Model, mixins.IdMixin):
    ...
```

Instead of

```python
class Foo(db.Model):
    id = db.ValidateColumn(db.Integer, primary_key=True)
    ...
```

## TimestampMixin

It will add the `created` and `updated` columns as `timestamp`, also it will be automatically add the **system timestamp** when the element is saved the first time, and update the `updated` column with the **system timestamp** when the model is updated.

```python
from flask_model_validation.models import mixins

class Foo(db.Model, mixins.TimestampMixin):
    ...
```
Instead of

```python
class Foo(db.Model):
    created = db.ValidateColumn('created_at', sa.DateTime,
                                nullable=False, default=datetime.utcnow)
    updated = db.ValidateColumn('updated_at', sa.DateTime, onupdate=datetime.utcnow)
    ...
```

## SlugMixin

It will add the `slug` column. You need to set the `field_to_slugfy` to the name of the column yo want to slugfy. This will create a slug from that field and update the slug when that field is updated.

```python
from flask_model_validation.models import mixins

class Foo(db.Model, mixins.SlugMixin):
    title = db.ValidateColumn(db.String(24), nullable=False)

    field_to_slugfy='title'
```

## CatalogModelMixin
It will add the `IdMixin`, `TimestampMixin` and `SlugMixin` as one. Also, it will add `name` and `is_active` columns.

```python
from flask_model_validation.models import mixins

class Foo(db.Model, mixins.CatalogModelMixin):
    ...
```

Instead of

```python
from flask_model_validation.models import mixins

class Foo(mixins.IdMixin, mixins.SlugMixin, mixins.TimestampMixin):
    name = db.ValidateColumn(db.String(24), nullable=False)
    is_active = db.ValidateColumn(db.Boolean, nullable=False, default=True)

    field_to_slugfy = 'name'
```

### DefinCatalogMixin

This mixin is a bit different from the others. It implements the same columns as `CatalogModelMixin` but you can define the rows in the catalog via the `slug` field. This should be done through an inner class called `CatalogMap` and define the rows as attributes of that class.

For example

```python
class Status(db.Model, mixins.DefineCatalogMixin):
    class CatalogMap:
        ON_STOCK ='on-stock'
        SOLD_OUT = 'sold-out'
        REQUESTED = 'requested'
```

And you can get the object for that row like this.

```python
Status.catalog().ON_STOCK
```

This will save the object in memory, so the next time you call it, it will return the same object instead hitting the database again. This is useful when you have a table as catalog and the rows don't change too often.

**Important:** This mixin doesn't created the rows for the catalog, you still need to create them via `status.save()` or insert them into the database manually.

---
[Back to features content](../README.md#features)
