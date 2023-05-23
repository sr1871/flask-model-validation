
# Extra model features

## Table of contents
- [pk: attr](#pk)
- [force_pk: attr](#force_pk)
- [is_new: attr](#is_new)
- [populate: function](#populatekwargs)
- [history_change: function](#history_changefieldstr)
- [Back to features content](../README.md#features)

## `pk`
Returns the pk value of the model.

```python
foo = Foo()
foo.pk # Returns `None`
foo.save(commit=True) # Saved with id=1
foo.pk # Returns `1`
```

## `force_pk`
It will flush the model into the database if it doesn't already have a pk. Returns the pk value of the model.

```python
foo = Foo()
foo.pk # Returns `None`
foo.force_pk # Similar to do `foo.save(flush=True)`; Returns `1`
```

## `is_new`
Returns if an object is new or was already added into database.
```python
foo = Foo()
foo.is_new # Returns `True`
foo.save(commit=True)
foo.is_new # Returns `False`
```

## `populate(**kwargs)`
Populate the object from kwargs.

```python
foo = Foo()
print(foo.name) # Prints `None`
foo.populate(name='test', email='test@test.com')
print(foo.name) # Prints `test`
```

## `history_change(field:str)`
It will return a `HistoryField` object.
This function is useful when you want to know if a filed has been modified.`HistoryField` have a few attributes that can help you to figure this out.

```python
foo = Foo(name='Bar')
h_name = foo.history_change('name')
print(h_name.was_changed) # Prints `False`
print(h_name.previous_value) # Prints `None`
print(h_name.current_value) # Prints `None`
foo.save(commit=True)
foo.name = 'Bar 2'
h_name = foo.history_change('name')
print(h_name.was_changed) # Prints `True`
print(h_name.previous_value) # Prints `'Bar'`
print(h_name.current_value) # Prints `'Bar 2'`
```

---
[Back to features content](../README.md#features)
