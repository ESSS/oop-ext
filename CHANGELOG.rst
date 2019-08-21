0.3.2 (2019-08-21)
------------------

* Interface and implementation methods can no longer contain mutable defaults, as this is considered
  a bad practice in general.


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
