==========
Interfaces
==========

``oop-ext`` introduces the concept of interfaces, common in other languages.

An interface is a class which defines methods and attributes, defining a specific behavior,
so implementations can declare that they work with an specific interface without worrying about
implementations details.

Interfaces are declared by subclassing :class:`oop_ext.interface.Interface`:

.. code-block:: python


    from oop_ext.interface import Interface


    class IDataSaver(Interface):
        """
        Interface for classes capable of saving a dict containing
        builtin types into persistent storage.
        """

        def save(self, data: dict[Any, Any]) -> None:
            """Saves the given list of strings in persistent storage."""


(By convention, interfaces start with the letter ``I``).

We can write a function which gets some data and saves it to persistent storage, without hard coding
it to any specific implementation:

.. code-block:: python


    def run_simulation(params: SimulationParameters, saver: IDataSaver) -> None:
        data = calculate(params)
        saver.save(data)


``run_simulation`` computes some simulation data, and uses a generic ``saver`` to persist it
somewhere.

We can now have multiple implementations of ``IDataSaver``, for example:


.. code-block:: python

    from oop_ext.interface import ImplementsInterface


    @ImplementsInterface(IDataSaver)
    class JSONSaver:
        def __init__(self, path: Path) -> None:
            self.path = path

        def save(self, data: dict[Any, Any]) -> None:
            with self.path.open("w", encoding="UTF-8") as f:
                json.dump(f, data)

And use it like this:

.. code-block:: python

    run_simulation(params, JSONSaver(Path("out.json")))

What about duck typing?
-----------------------

In Python declaring interfaces is not really necessary due to *duck typing*, however interfaces
bring to the table **runtime validation**.

If later on we add a new method to our ``IDataSaver`` interface, we will get errors at during
*import time* about implementations which don't implement the new method, making it easy to spot
the problems early. Interfaces also verify parameters, type annotations, and default values, making
it easy to keep implementations and interfaces in sync.

Static Type Checking
--------------------

.. versionadded:: 1.1.0

The interfaces implementation has been implemented many years ago, before type checking in Python
became a thing.

The static type checking approach is to use `Protocols <https://www.python.org/dev/peps/pep-0544/>`__,
which has the same benefits and flexibility of interfaces, but without the runtime cost. At ESSS
however migrating the entire code base, which makes extensive use of interfaces, is a lengthy process
so we need an intermediate solution to fill the gaps.

To bridge the gap between the runtime-based approach of interfaces, and the static
type checking provided by static type checkers, one just needs to subclass from both
`Interface` and ``TypeCheckingSupport``:

.. code-block:: python

    from oop_ext.interface import Interface, TypeCheckingSupport


    class IDataSaver(Interface, TypeCheckingSupport):
        """
        Interface for classes capable of saving a dict containing
        builtin types into persistent storage.
        """

        def save(self, data: dict[Any, Any]) -> None:
            """Saves the given list of strings in persistent storage."""

The ``TypeCheckingSupport`` class hides from the user the details necessary to make type checkers
understand ``Interface`` subclasses.

Note that subclassing from ``TypeCheckingSupport`` has zero runtime cost, existing only
for the benefits of the type checkers.

.. note::

    Due to how ``Protocol`` works in Python, every ``Interface`` subclass **also** needs to subclass
    ``TypeCheckingSupport``.
