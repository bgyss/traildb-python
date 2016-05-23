# Python bindings for TrailDB

### Quick start

First install the [TrailDB library](https://github.com/traildb/traildb). Then

    $ python setup.py install

For detailed instructions, see [Getting Started guide](http://traildb.io/docs/getting_started/).

### Example

See [TrailDB tutorial](http://traildb.io/docs/tutorial) for more information.

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
