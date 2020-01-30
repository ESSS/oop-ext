0.6.0 (2020-01-31)
==================

* Change back the default value of ``requires_declaration`` to ``True`` and fix an error (#22) where the cache wasn 't properly cleared.

0.5.1 (2019-12-20)
------------------

* Fixes an issue (#20) where mocked `classmethods` weren't considered a valid method during internal checks.

0.5.0 (2019-12-12)
------------------

* Add optional argument ``requires_declaration`` so users can decide whether or not ``@ImplementsInterface`` declarations are necessary.

0.4.0 (2019-12-03)
------------------

* Implementations no longer need to explicitly declare that they declare an interface with ``@ImplementsInterface``: the check is done implicitly (and cached) by `AssertImplements` and equivalent functions.

0.3.2 (2019-08-22)
------------------

* Interface and implementation methods can no longer contain mutable defaults, as this is considered
  a bad practice in general.

* ``Null`` instances are now hashable.


0.3.1 (2019-08-16)
------------------

* Fix mismatching signatures when creating "interface stubs" for instances:

  .. code-block:: python

      foo = IFoo(Foo())


0.3.0 (2019-08-08)
------------------

* Interfaces now support keyword-only arguments.

0.2.4 (2019-03-22)
------------------

* Remove ``FunctionNotRegisteredError`` exception, which has not been in use for a few years.


0.2.3 (2019-03-22)
------------------

* Fix issues of ignored exception on nested callback.


0.2.1 (2019-03-14)
------------------

* Fix issues and remove obsolete code.


0.1.8 (2019-03-12)
------------------

* First release on PyPI.
