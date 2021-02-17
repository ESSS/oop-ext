# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
import weakref
from typing import Union, Optional, Callable, Any, Tuple, Sequence

from oop_ext.foundation.types_ import Method
from oop_ext.foundation.weak_ref import WeakMethodRef


from ._callback import Callback, GetClassForUnboundMethod, _CallbackWrapper


def _CreateBeforeOrAfter(
    method: Callable, callback: Callable, sender_as_parameter: bool, before: bool = True
) -> "_MethodWrapper":

    wrapper = WrapForCallback(method)
    original_method = wrapper.OriginalMethod()

    extra_args = []

    if sender_as_parameter:
        try:
            im_self = original_method.__self__
        except AttributeError:
            pass
        else:
            extra_args.append(weakref.ref(im_self))

            # this is not garbage collected directly when added to the wrapper (which will create a WeakMethodRef to it)
            # because it's not a real method, so, WeakMethodRef will actually maintain a strong reference to it.
            callback = _CallbackWrapper(WeakMethodRef(callback))

    if before:
        wrapper.AppendBefore(callback, extra_args)
    else:
        wrapper.AppendAfter(callback, extra_args)

    return wrapper


def Before(
    method: Callable, callback: Callable, sender_as_parameter: bool = False
) -> "_MethodWrapper":
    """
    Registers the given callback to be executed before the given method is called, with the
    same arguments.

    The method can be eiher an unbound method or a bound method. If it is an unbound method,
    *all* instances of the class will generate callbacks when method is called. If it is a bound
    method, only the method of the instance will generate callbacks.

    Remarks:
        The function has changed its signature to accept an extra parameter (sender_as_parameter).
        Using "*args" as before made impossible to add new parameters to the function.
    """
    return _CreateBeforeOrAfter(method, callback, sender_as_parameter)


def After(
    method: Callable, callback: Callable, sender_as_parameter: bool = False
) -> "_MethodWrapper":
    """
    Registers the given callbacks to be execute after the given method is called, with the same
    arguments.

    The method can be eiher an unbound method or a bound method. If it is an unbound method,
    *all* instances of the class will generate callbacks when method is called. If it is a bound
    method, only the method of the instance will generate callbacks.

    Remarks:
        This function has changed its signature to accept an extra parameter (sender_as_parameter).
        Using "*args" as before made impossible to add new parameters to the function.
    """
    return _CreateBeforeOrAfter(method, callback, sender_as_parameter, before=False)


def Remove(method: Callable, callback: Callable) -> bool:
    """
    Removes the given callback from a method previously connected using after or before.
    Return true if the callback was removed, false otherwise.
    """
    wrapped = _GetWrapped(method)
    if wrapped:
        return wrapped.Remove(callback)
    return False


class _MethodWrapper(
    Method
):  # It needs to be a subclass of Method for interface checks.

    __slots__ = ["_before", "_after", "_method", "_name", "OriginalMethod"]

    def __init__(self, method: Union[Method, "_MethodWrapper", Callable]):
        self._before: Optional[Callback] = None
        self._after: Optional[Callback] = None
        self._method = WeakMethodRef(method)
        self._name = method.__name__

        # Maintaining the OriginalMethod() interface that clients expect.
        self.OriginalMethod = self._method

    def __repr__(self) -> str:
        return "_MethodWrapper({}): {}".format(id(self), self._name)

    def __call__(self, *args: object, **kwargs: object) -> Any:

        if self._before is not None:
            self._before(*args, **kwargs)

        m = self._method()
        if m is None:
            raise ReferenceError(
                "Error: the object that contained this method (%s) has already been garbage collected"
                % self._name
            )

        result = m(*args, **kwargs)

        if self._after is not None:
            self._after(*args, **kwargs)

        return result

    def AppendBefore(
        self, callback: Callable, extra_args: Optional[Sequence[object]] = None
    ) -> None:
        """
        Append the given callbacks in the list of callback to be executed BEFORE the method.
        """
        if extra_args is None:
            extra_args = ()

        if self._before is None:
            self._before = Callback()
        self._before.Register(callback, extra_args)

    def AppendAfter(
        self, callback: Callable, extra_args: Optional[Sequence[object]] = None
    ) -> None:
        """
        Append the given callbacks in the list of callback to be executed AFTER the method.
        """
        if extra_args is None:
            extra_args = []

        if self._after is None:
            self._after = Callback()
        self._after.Register(callback, extra_args)

    def Remove(self, callback: Callable) -> bool:
        """
        Remove the given callback from both the BEFORE and AFTER callbacks lists.
        """
        if self._before is not None and self._before.Contains(callback):
            self._before.Unregister(callback)
            return True
        if self._after is not None and self._after.Contains(callback):
            self._after.Unregister(callback)
            return True

        return False


def _GetWrapped(
    method: Union[Method, _MethodWrapper, Callable]
) -> Optional[_MethodWrapper]:
    """
    Returns true if the given method is already wrapped.
    """
    if isinstance(method, _MethodWrapper):
        return method
    try:
        return method._wrapped_instance  # type:ignore[attr-defined, union-attr]
    except AttributeError:
        return None


def WrapForCallback(method: Union[Method, _MethodWrapper, Callable]) -> _MethodWrapper:
    """Generates a wrapper for the given method, or returns the method itself
    if it is already a wrapper.
    """
    wrapped = _GetWrapped(method)
    if wrapped is not None:
        # its a wrapper already
        if not hasattr(method, "__self__"):
            return wrapped

        # Taking care for the situation where we add a callback to the class and later to the
        # instance.
        # Note that the other way around does not work at all (i.e.: if a callback is first added
        # to the instance, there's no way we'll find about that when adding it to the class
        # anyways).
        if method.__self__ is None:  # type:ignore[union-attr]
            if wrapped._method._obj is None:
                return wrapped

    wrapper = _MethodWrapper(method)
    if getattr(method, "__self__", None) is None:
        # override the class method

        # we must make it a regular call for classmethods (it MUST not be a bound
        # method nor class when doing that).
        def call(*args: object, **kwargs: object) -> Any:
            return wrapper(*args, **kwargs)

        call.__name__ = method.__name__
        call._wrapped_instance = wrapper  # type:ignore[attr-defined]

        setattr(GetClassForUnboundMethod(method), method.__name__, call)
    else:
        # override the instance method
        setattr(method.__self__, method.__name__, wrapper)  # type:ignore[union-attr]
    return wrapper
