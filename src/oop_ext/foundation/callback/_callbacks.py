from typing import Callable, Any, List, Tuple

from ._fast_callback import Callback, _UnregisterContext
from ._shortcuts import After, Before, Remove


class Callbacks:
    """
    Holds created callbacks, making it easy to disconnect later.

    Note: keeps a strong reference to the callback and the sender, thus, they won't be garbage-
    collected while still connected in this case.
    """

    def __init__(self) -> None:
        self._function_callbacks: List[Tuple[Callable, Callable]] = []
        self._contexts: List[_UnregisterContext] = []

    def Before(self, sender, *callbacks, **kwargs):
        sender = Before(sender, *callbacks, **kwargs)
        for callback in callbacks:
            self._function_callbacks.append((sender, callback))
        return sender

    def After(self, sender, *callbacks, **kwargs):
        sender = After(sender, *callbacks, **kwargs)
        for callback in callbacks:
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

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager support: when the context ends, unregister all callbacks."""
        self.RemoveAll()
        return False

    def Register(self, callback: Callback, func: Callable[..., Any]) -> None:
        """
        Registers the given function into the given callback.

        This will automatically unregister the function from the given callback when
        RemoveAll() is called or the context manager ends in the context manager form.
        """
        self._contexts.append(callback.Register(func))
