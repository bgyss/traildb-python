# Python bindings for TrailDB

### Adding data to a trail


```python

>>> from traildb import TrailDB, TrailDBConstructor

>>> cookie = '12345678123456781234567812345678'
>>> cons = TrailDBConstructor('test.tdb', ['field1', 'field2'])
>>> cons.add(cookie, 123, ['a'])
>>> cons.add(cookie, 124, ['b', 'c'])
>>> tdb = cons.finalize()

>>> for cookie, trail in tdb.crumbs():
...     for event in trail:
...         print cookie, event

12345678123456781234567812345678 event(time=123L, field1='a', field2='')
12345678123456781234567812345678 event(time=124L, field1='b', field2='c')
```
