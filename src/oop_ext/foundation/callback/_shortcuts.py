
import weakref

from oop_ext.foundation.types_ import Method
from oop_ext.foundation.weak_ref import WeakMethodRef

from ._callback_wrapper import _CallbackWrapper
from ._fast_callback import Callback, GetClassForUnboundMethod


# ===================================================================================================
# _CreateBeforeOrAfter
# ===================================================================================================
def _CreateBeforeOrAfter(method, callback, sender_as_parameter, before=True):

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


# ===================================================================================================
# Before
# ===================================================================================================
def Before(method, callback, sender_as_parameter=False):
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


# ===================================================================================================
# After
# ===================================================================================================
def After(method, callback, sender_as_parameter=False):
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


# ===================================================================================================
# Remove
# ===================================================================================================
def Remove(method, callback):
    """
        Removes the given callback from a method previously connected using after or before.
        Return true if the callback was removed, false otherwise.
    """
    wrapped = _GetWrapped(method)
    if wrapped:
        return wrapped.Remove(callback)
    return False


# ===================================================================================================
# Implementation Details
# ===================================================================================================
class _MethodWrapper(
    Method
):  # It needs to be a subclass of Method for interface checks.

    __slots__ = ["_before", "_after", "_method", "_name", "OriginalMethod"]

    def __init__(self, method):
        self._before = None
        self._after = None
        self._method = WeakMethodRef(method)
        self._name = method.__name__

        # Maintaining the OriginalMethod() interface that clients expect.
        self.OriginalMethod = self._method

    def __repr__(self):
        return "_MethodWrapper({}): {}".format(id(self), self._name)

    def __call__(self, *args, **kwargs):

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

    def AppendBefore(self, callback, extra_args=None):
        """
            Append the given callbacks in the list of callback to be executed BEFORE the method.
        """
        if extra_args is None:
            extra_args = []

        if self._before is None:
            self._before = Callback()
        self._before.Register(callback, extra_args)

    def AppendAfter(self, callback, extra_args=None):
        """
            Append the given callbacks in the list of callback to be executed AFTER the method.
        """
        if extra_args is None:
            extra_args = []

        if self._after is None:
            self._after = Callback()
        self._after.Register(callback, extra_args)

    def Remove(self, callback):
        """
            Remove the given callback from both the BEFORE and AFTER callbacks lists.
        """
        result = False

        if self._before is not None and self._before.Contains(callback):
            self._before.Unregister(callback)
            result = True
        if self._after is not None and self._after.Contains(callback):
            self._after.Unregister(callback)
            result = True

        return result


# ===================================================================================================
# _GetWrapped
# ===================================================================================================
def _GetWrapped(method):
    """
        Returns true if the given method is already wrapped.
    """
    if isinstance(method, _MethodWrapper):
        return method
    try:
        return method._wrapped_instance
    except AttributeError:
        return None


# ===================================================================================================
# WrapForCallback
# ===================================================================================================
def WrapForCallback(method):
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
        if method.__self__ is None:
            if wrapped._method._obj is None:
                return wrapped

    wrapper = _MethodWrapper(method)
    if not hasattr(method, "__self__") or method.__self__ is None:
        # override the class method

        # we must make it a regular call for classmethods (it MUST not be a bound
        # method nor class when doing that).
        def call(*args, **kwargs):
            return wrapper(*args, **kwargs)

        call.__name__ = method.__name__
        call._wrapped_instance = wrapper

        setattr(GetClassForUnboundMethod(method), method.__name__, call)
    else:
        # override the instance method
        setattr(method.__self__, method.__name__, wrapper)
    return wrapper
