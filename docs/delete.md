# Deleting the model

You can delete the model calling `delete()`.

```python
foo = Foo(name='test')
foo.save(commit=True)
foo.delete(commit=True)
```
Like the `save()` function, the transaction has been added to the session, but it will not persist until `commit` is called. You can do that by setting `commit=True`. For more information, see **Saving the model** section.

You can also add some logic after delete the object overriding the `after_delete` method.

```python
class Foo(db.Model):
    ...

    def after_delete(self) -> None:
        super().after_delete()
        ...
```

---
[Back to features content](../README.md#features)
