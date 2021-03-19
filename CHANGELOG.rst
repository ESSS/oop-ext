2.1.0 (2021-03-19)
------------------

* #48: New type-checker friendly ``proxy = GetProxy(I, obj)`` function as an alternative to ``proxy = I(obj)``. The
  latter is not accepted by type checkers in general because interfaces are protocols, which can't be instantiated.

  Also fixed a type-checking error with ``AsssertImplements``::

      Only concrete class can be given where "Type[Interface]" is expected

  This happens due to `python/mypy#5374 <https://github.com/python/mypy/issues/5374>`__.


2.0.0 (2021-03-10)
------------------

* #47: Interfaces no longer check type annotations at all.

  It was supported initially, but in practice
  this feature has shown up to be an impediment to adopting type annotations incrementally, as it
  discourages adding type annotations to improve existing interfaces, or annotating
  existing implementations without having to update the interface (and all other implementations
  by consequence).

  It was decided to let the static type checker correctly deal with matching type annotations, as
  it can do so more accurately than ``oop-ext`` did before.

1.2.0 (2021-03-09)
------------------

* #43: Fix support for type annotated ``Attribute`` and ``ReadOnlyAttribute``:

  .. code-block:: python

      class IFoo(Interface):
          value: int = Attribute(int)

1.1.2 (2021-02-23)
------------------

* #41: Fix regression introduced in ``1.1.0`` where installing a callback using
  ``callback.After`` or ``callback.Before`` would make a method no longer compliant with
  the signature required by its interface.

1.1.1 (2021-02-23)
------------------

* #38: Reintroduce ``extra_args`` argument to ``Callback._GetKey``, so subclasses can make use
  of it.

* #36: Fix regression introduced in ``1.1.0`` where ``Abstract`` and ``Implements`` decorators
  could no longer be used in interfaces implementations.

1.1.0 (2021-02-19)
------------------

* #25: ``oop-ext`` now includes inline type annotations and exposes them to user programs.

  If you are running a type checker such as mypy on your tests, you may start noticing type errors indicating incorrect usage.
  If you run into an error that you believe to be incorrect, please let us know in an issue.

  The types were developed against ``mypy`` version 0.800.

* #26: New type-checked ``Callback`` variants, ``Callback0``, ``Callback1``, ``Callback2``, etc, providing
  type checking for all operations(calling, ``Register``, etc) at nearly zero runtime cost.

  Example:

  .. code-block:: python

      from oop_ext.foundation.callback import Callback2


      def changed(x: int, v: float) -> None:
          ...


      on_changed = Callback2[int, float]()
      on_changed(10, 5.25)


* Fixed ``Callbacks.Before`` and ``Callbacks.After`` signatures: previously their signature conveyed
  that they supported multiple callbacks, but it was a mistake which would break callers because
  every parameter after the 2nd would be considered the ``sender_as_parameter`` parameter, which
  was forwarded to ``After`` and ``Before`` functions of the ``_shortcuts.py``
  module.

1.0.0 (2020-10-01)
------------------

* ``Callbacks`` can be used as context manager, which provides a ``Register(callback, function)``,
  which automatically unregisters all functions when the context manager ends.

* ``Callback.Register(function)`` now returns an object with a ``Unregister()`` method, which
  can be used to undo the register call.

0.6.0 (2020-01-31)
==================

* Change back the default value of ``requires_declaration`` to ``True`` and fix an error (#22) where the cache wasn't properly cleared.

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
