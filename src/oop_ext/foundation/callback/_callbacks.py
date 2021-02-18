# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
from typing import Callable, Any, List, Tuple, TypeVar, cast

from ._callback import Callback, _UnregisterContext
from ._shortcuts import After, Before, Remove


T = TypeVar("T", bound=Callable)


class Callbacks:
    """
    Holds created callbacks, making it easy to disconnect later.

    This class provides two methods of operation:

    * :meth:`Before` and :meth:`After`:

        This provides connection support for arbitrary functions
        and methods, similar to mocking them.

    * :meth:`Register`:

        Registers a function into a :class:`Callback`, making the callback
        call the registered function when it gets itself called.

    In both modes, :meth:`RemoveAll` can be used to unregister all callbacks.

    The class can also be used in context-manager form, in which case all callbacks
    are unregistered when the context-manager ends.

    .. note::
        This class keeps a strong reference to the callback and the sender, thus
        they won't be garbage-collected while still connected.
    """

    def __init__(self) -> None:
        self._function_callbacks: List[Tuple[Callable, Callable]] = []
        self._contexts: List[_UnregisterContext] = []

    def Before(
        self, sender: T, callback: Callable, *, sender_as_parameter: bool = False
    ) -> T:
        """
        Registers a callback to be executed before an arbitrary function.

        Example::

            class C:
                def foo(self, x): ...

            def callback(x): ...


            Before(C.foo, callback)

        The call above will result in ``callback`` to be called for *every instance* of ``C``.
        """
        sender = cast(
            T, Before(sender, callback, sender_as_parameter=sender_as_parameter)
        )
        self._function_callbacks.append((sender, callback))
        return sender

    def After(
        self, sender: T, callback: Callable, *, sender_as_parameter: bool = False
    ) -> T:
        """
        Same as :meth:`Before`, but will call the callback after the ``sender`` function has
        been called.
        """
        sender = cast(
            T, After(sender, callback, sender_as_parameter=sender_as_parameter)
        )
        self._function_callbacks.append((sender, callback))
        return sender

    def RemoveAll(self) -> None:
        """
        Remove all registered functions, either from :meth:`Before`, :meth:`After`, or
        :meth:`Register`.
        """
        for sender, callback in self._function_callbacks:
            Remove(sender, callback)
        self._function_callbacks.clear()
        for context in self._contexts:
            context.Unregister()
        self._contexts.clear()

    def __enter__(self) -> "Callbacks":
        """Context manager support: when the context ends, unregister all callbacks."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager support: when the context ends, unregister all callbacks."""
        self.RemoveAll()

    def Register(self, callback: Callback, func: Callable) -> None:
        """
        Registers the given function into the given callback.

        This will automatically unregister the function from the given callback when
        :meth:`Callbacks.RemoveAll` is called or the context manager ends in the context manager form.
        """
        self._contexts.append(callback.Register(func))
