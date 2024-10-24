Callbacks
=========

.. automodule:: oop_ext.foundation.callback._callback
    :noindex:


Type Checking
-------------

.. versionadded:: 1.1.0

``oop-ext`` also provides type-checked variants, ``Callback0``, ``Callback1``, ``Callback2``, etc,
which explicitly declare the number of arguments and types of the parameters supported by
the callback.

Example:

.. code-block:: python

    class Point:
        def __init__(self, x: float, y: float) -> None:
            self._x = x
            self._y = y
            self.on_changed = Callback2[float, float]()

        def update(self, x: float, y: float) -> None:
            self._x = x
            self._y = y
            self.on_changed(x, y)


    def on_point_changed(x: float, y: float) -> None:
        print(f"point changed: ({x}, {y})")


    p = Point(0.0, 0.0)
    p.on_changed.Register(on_point_changed)
    p.update(100.0, 2.5)


In the example above, both the calls ``self.on_changed`` and ``on_changed.Register`` are properly
type checked for number of arguments and types.

The method specialized signatures are only seen by the type checker, so using one of the specialized
variants should have nearly zero runtime cost (only the cost of an empty subclass).

.. versionadded:: 2.2.0

``PriorityCallback`` has the same support, with ``PriorityCallback0``, ``PriorityCallback1``, ``PriorityCallback2``, etc.

.. note::
    The separate callback classes are needed for now, but once we require Python 3.11
    (`pep-0646 <https://www.python.org/dev/peps/pep-0646>`__, we should be able to
    implement the generic variants into ``Callback`` and ``PriorityCallback`` themselves.
