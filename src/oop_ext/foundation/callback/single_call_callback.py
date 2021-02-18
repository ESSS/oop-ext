# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
from typing import Dict, Tuple, Callable

from ._callback import Callback


class SingleCallCallback:
    """
    Callback-like implementation used for a callback to which __call__ is called only once (and
    subsequent calls will always trigger the same callback).

    The callback parameter is pre-registered and kept as a weak-reference.
    """

    def __init__(self, callback_parameter: object) -> None:
        """
        :param object callback_parameter:
            A weak-reference is kept to this object (because the usual use-case is making a call
            passing the object that contains this callback).
        """
        from oop_ext.foundation.weak_ref import GetWeakRef

        if callback_parameter is None:
            self._callback_parameter = None
        else:
            self._callback_parameter = GetWeakRef(callback_parameter)
        self._done_callbacks = Callback()
        self._done = False

        self._args: Tuple[object, ...] = ()
        self._kwargs: Dict[str, object] = {}

    def __call__(self, *args: object, **kwargs: object) -> None:
        if self._done:
            raise AssertionError("This callback can only be called once.")

        # Keep the args passed to call it later on...
        self._args = args
        self._kwargs = kwargs

        if self._callback_parameter is not None:
            callback_parameter = self._callback_parameter()
            if callback_parameter is None:
                raise ReferenceError("Callback parameter is already garbage collected.")
        else:
            callback_parameter = None

        # We can dispose of it (as of now, callbacks should be called directly).
        self._done = True
        if callback_parameter is not None:
            self._done_callbacks(callback_parameter, *args, **kwargs)
        else:
            self._done_callbacks(*args, **kwargs)

    def Unregister(self, fn: Callable) -> None:
        self._done_callbacks.Unregister(fn)

    def UnregisterAll(self) -> None:
        self._done_callbacks.UnregisterAll()

    def Register(self, fn: Callable) -> None:
        if self._callback_parameter is not None:
            callback_parameter = self._callback_parameter()
            if callback_parameter is None:
                raise ReferenceError("Callback parameter is already garbage collected.")
        else:
            callback_parameter = None

        contains = self._done_callbacks.Contains(fn)

        self._done_callbacks.Register(fn)
        if self._done and not contains:
            if callback_parameter is not None:
                fn(callback_parameter, *self._args, **self._kwargs)
            else:
                fn(*self._args, **self._kwargs)

    def AllowCallingAgain(self) -> None:
        """
        This callback is usually called only once, afterwards, any registry will call it directly
        (and the callback cannot be called anymore).

        By calling this method, we allow calling this callback again (and stop directly notifying
        clients just registered until it's called again).
        """
        self._done = False
