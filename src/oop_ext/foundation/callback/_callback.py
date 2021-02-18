# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
"""
Callbacks provide an interface to register other callbacks, that will be *called back* when the
``Callback`` object is called.

A ``Callback`` is similar to holding a pointer to a function, except it supports multiple functions.

Example:

.. code-block::

    class Data:

        def __init__(self, x: int) -> None:
            self._x = x
            self.on_changed = Callback()

        @property
        def x(self) -> int:
            return self._x

        @x.setter
        def x(self, x: int) -> None:
            self._x = x
            self.on_changed(x)

In the code above, ``Data`` contains a ``x`` property, which triggers a ``on_changed`` callback
whenever ``x`` changes.

We can be notified whenever ``x`` changes by registering a function in the callback:

.. code-block::

    def on_x(x: int) -> None:
        print(f"x changed to {x}")

    data = Data(10)
    data.on_changed.Register(on_x)
    data.x = 20

The code above will print ``x changed to 20``, because changing ``data.x`` triggers all functions
registered in ``data.on_changed``.

An important feature is that the functions connected to the callback are *weakly referenced*, so
methods connected to a callback won't keep the method instance alive due to the connection.

We can unregister functions using :meth:`Unregister <Callback.Unregister>`, check if a function
is registered with :meth:`Contains <Callback.Contains>`, and unregister all connected functions
with :meth:`UnregisterAll <Callback.UnregisterAll>`.
"""
import functools
import inspect
import logging
import types
import weakref
from typing import Callable, Any, Tuple, Hashable, Sequence, Union, cast, Optional

import attr

from oop_ext.foundation.compat import GetClassForUnboundMethod
from oop_ext.foundation.is_frozen import IsDevelopment
from oop_ext.foundation.odict import odict
from oop_ext.foundation.types_ import Method
from oop_ext.foundation.weak_ref import WeakMethodProxy

log = logging.getLogger(__name__)


class Callback:
    """
    Object that provides a way for others to connect in it and later call it to call
    those connected.

    Callbacks are stored as weakrefs to objects connected.

    **Determining kind of callable (Python 3)**

    Many parts of callback implementation rely on identifying the kind of callable: is it a
    free function? is it a function bound to an object?

    Below there is a table to help understand how different objects are classified:

    .. code-block::

                            |has__self__|has__call__|has__call__self__|isbuiltin|isfunction|ismethod
        --------------------|-----------|-----------|-----------------|---------|----------|--------
        free function       |False      |True       |True             |False    |True      |False
        bound method        |True       |True       |True             |False    |False     |True
        class method        |True       |True       |True             |False    |False     |True
        bound class method  |True       |True       |True             |False    |False     |True
        function object     |False      |True       |True             |False    |False     |False
        builtin function    |True       |True       |True             |True     |False     |False
        object              |True       |True       |True             |True     |False     |False
        custom object       |False      |False      |False            |False    |False     |False
        string              |False      |False      |False            |False    |False     |False

    where rows are:

    .. code-block:: python

        def free_fn(foo):
            # `free function`
            pass


        class Foo:
            def bound_fn(self, foo):
                pass


        class Bar:
            @classmethod
            def class_fn(cls, foo):
                pass


        class ObjectFn:
            def __call__(self, foo):
                pass


        foo = Foo()  # foo is `custom object`, foo.bound_fn is `bound method`
        bar = Bar()  # Bar.class_fn is `class method`, bar.class_fn is `bound class method`

        object_fn = ObjectFn()  # `function object`

        obj = object()  # `object`
        string = "foo"  # `string`
        builtin_fn = string.split  # `builtin function`

    And where columns are:

    * isbuiltin: inspect.isbuiltin
    * isfunction: inspect.isfunction
    * ismethod: inspect.ismethod
    * has__self__: hasattr(obj, '__self__')
    * has__call__: hasattr(obj, '__call__')
    * has__call__self__: hasattr(obj.__call__, '__self__') if hasattr(obj, '__call__') else False

    .. note::
        After an internal refactoring, ``__slots__`` has been added, so, it cannot have
        weakrefs to it (but as it stores weakrefs internally, that shouldn't be a problem).
        If weakrefs are really needed, ``__weakref__`` should be added to the slots.
    """

    __slots__ = ["_callbacks", "_handle_errors", "__weakref__"]

    INFO_POS_FUNC_OBJ = 0
    INFO_POS_FUNC_FUNC = 1
    INFO_POS_FUNC_CLASS = 2

    # Can be set to True to debug (should be removed after all applications
    # properly test the new behavior).
    DEBUG_NEW_WEAKREFS = False

    def __init__(self) -> None:
        # callbacks is no longer lazily created: This makes the creation a bit slower, but
        # everything else is faster (as having to check for hasattr each time is slow).
        self._callbacks = odict()

    def _GetKey(self, func: Union["_CallbackWrapper", Method, Callable]) -> Hashable:
        """
        :param object func:
            The function for which we want the key.

        :rtype: object
        :returns:
            Returns the key to be used to access the object.

        .. note:: The key is guaranteed to be unique among the living objects, but if the object
        is garbage collected, a new function may end up having the same key.
        """
        if func.__class__ == _CallbackWrapper:
            func = cast(_CallbackWrapper, func)
            func = func.OriginalMethod()

        try:
            if func.__self__ is not None:  # type:ignore[union-attr]
                # bound method
                return (
                    id(func.__self__),  # type:ignore[union-attr]
                    id(func.__func__),  # type:ignore[union-attr]
                    id(func.__self__.__class__),  # type:ignore[union-attr]
                )
            else:
                return (
                    id(func.__func__),  # type:ignore[union-attr]
                    id(GetClassForUnboundMethod(func)),
                )

        except AttributeError:
            # not a method -- a callable: create a strong reference (the CallbackWrapper
            # is depending on this behaviour... is it correct?)
            return id(func)

    def _GetInfo(
        self, func: Union[None, WeakMethodProxy, Method, Callable]
    ) -> Tuple[Any, Any, Any]:
        """
        :rtype: tuple(func_obj, func_func, func_class)
        :returns:
            Returns a tuple with the information needed to call a method later on (close to the
            WeakMethodRef, but a bit more specialized -- and faster for this context).
        """
        # Note: if it's a _CallbackWrapper, we want to register it and not the 'original method'
        # at this point, but if it's a WeakMethodProxy, register the original method (we'll make a
        # weak reference later anyways).
        if func.__class__ == WeakMethodProxy:
            func = cast(WeakMethodProxy, func)
            func = func.GetWrappedFunction()

        if _IsCallableObject(func):
            if self.DEBUG_NEW_WEAKREFS:
                obj_str = "{}".format(func.__class__)
                print("Changed behavior for: %s" % obj_str)

                def on_die(r: Any) -> None:
                    # I.e.: the hint here is that a reference may die before expected
                    print("Reference died: {}".format(obj_str))

                return (weakref.ref(func, on_die), None, None)
            return (weakref.ref(func), None, None)

        try:
            if (
                func.__self__ is not None  # type:ignore[union-attr]
                and func.__func__ is not None  # type:ignore[union-attr]
            ):
                # bound method
                return (
                    weakref.ref(func.__self__),  # type:ignore[union-attr]
                    func.__func__,  # type:ignore[union-attr]
                    func.__self__.__class__,  # type:ignore[union-attr]
                )
            else:
                # unbound method
                return (
                    None,
                    func.__func__,  # type:ignore[union-attr]
                    GetClassForUnboundMethod(func),
                )
        except AttributeError:
            # not a method -- a callable: create a strong reference (CallbackWrapper
            # is depending on this behaviour... is it correct?)
            return (None, func, None)

    def __call__(self, *args: object, **kwargs: object) -> None:  # @DontTrace
        """
        Calls every registered function with the given args and kwargs.
        """
        callbacks = self._callbacks
        if not callbacks:
            return

        to_call = []

        for cb_id, info_and_extra_args in list(callbacks.items()):  # iterate in a copy
            info = info_and_extra_args[0]
            func_obj = info[self.INFO_POS_FUNC_OBJ]
            if func_obj is not None:
                # Ok, we have a self.
                func_obj = func_obj()
                if func_obj is None:
                    # self is dead
                    del callbacks[cb_id]
                else:
                    func_func = info[self.INFO_POS_FUNC_FUNC]
                    if func_func is None:
                        to_call.append((func_obj, info_and_extra_args[1]))
                    else:
                        to_call.append(
                            (
                                types.MethodType(func_func, func_obj),
                                info_and_extra_args[1],
                            )
                        )
            else:
                func_func = info[self.INFO_POS_FUNC_FUNC]
                if func_func.__class__ == _CallbackWrapper:
                    # The instance of the _CallbackWrapper already died! (func_obj is None)
                    original_method = func_func.OriginalMethod()
                    if original_method is None:
                        del callbacks[cb_id]
                        continue

                # No self: either classmethod or just callable
                to_call.append((func_func, info_and_extra_args[1]))

        to_call = self._FilterToCall(to_call, args, kwargs)

        # Iterate over callbacks running and checking for exceptions...
        for func, extra_args in to_call:
            func(*extra_args + args, **kwargs)

    def _FilterToCall(self, to_call: Any, args: Any, kwargs: Any) -> Any:
        """
        Provides a chance for subclasses to filter the function/extra arguments to call.

        :param list(tuple(method,tuple)) to_call:
            list(function_to_call, extra_arguments)

        :param args:
            Arguments being passed to the call.

        :param kwargs:
            Keyword arguments being passed to the call.

        :return list(tuple(method,tuple):
            Return the filtered list with the function/extra arguments to call.
        """
        return to_call

    _EXTRA_ARGS_CONSTANT: Tuple[object, ...] = tuple()

    def Register(
        self,
        func: Callable[..., Any],
        extra_args: Sequence[object] = _EXTRA_ARGS_CONSTANT,
    ) -> "_UnregisterContext":
        """
        Registers a function in the callback.

        :param func:
            Method or function that will be called later.

        :param extra_args:
            Arguments that will be passed automatically to the passed function
            when the callback is called.

        :return:
            A context which can be used to unregister this call.

            The context object provides this low level functionality, if you are registering
            many callbacks at once and plan to unregister them all at the same time, consider
            using `Callbacks` instead.
        """
        if IsDevelopment() and hasattr(func, "im_class"):
            msg = (
                "%r object has inconsistent internal attributes and is not compatible with Callback.\n"
                "im_class = %r\n"
                "(If using a MagicMock, remember to pass spec=lambda:None)."
            )
            raise RuntimeError(msg % (func, getattr(func, "im_class")))
        if extra_args is not self._EXTRA_ARGS_CONSTANT:
            extra_args = tuple(extra_args)

        key = self._GetKey(func)
        callbacks = self._callbacks
        callbacks.pop(key, None)  # Remove if it exists
        callbacks[key] = (self._GetInfo(func), extra_args)
        return _UnregisterContext(self, key)

    def Contains(
        self,
        func: Callable[..., Any],
        extra_args: Sequence[object] = _EXTRA_ARGS_CONSTANT,
    ) -> bool:
        """
        :param object func:
            The function that may be contained in this callback.

        :rtype: bool
        :returns:
            True if the function is already registered within the callbacks and False
            otherwise.
        """
        key = self._GetKey(func)

        callbacks = self._callbacks

        info_and_extra_args = callbacks.get(key)
        if info_and_extra_args is None:
            return False

        real_func: Optional[Callable] = func

        if real_func.__class__ == WeakMethodProxy:
            real_func = cast(WeakMethodProxy, real_func)
            real_func = real_func.GetWrappedFunction()

        # We must check if it's actually the same, because it may be that the ids we've gotten for
        # this object were actually from a garbage-collected function that was previously registered.

        info = info_and_extra_args[0]
        func_obj = info[self.INFO_POS_FUNC_OBJ]
        func_func = info[self.INFO_POS_FUNC_FUNC]
        if func_obj is not None:
            # Ok, we have a self.
            func_obj = func_obj()
            if func_obj is None:
                # self is dead
                del callbacks[key]
                return False
            else:
                return real_func is func_obj or (
                    func_func is not None
                    and real_func == types.MethodType(func_func, func_obj)
                )
        else:
            if type(func_func) is _CallbackWrapper:
                # The instance of the _CallbackWrapper already died! (func_obj is None)
                original_method = func_func.OriginalMethod()
                if original_method is None:
                    del callbacks[key]
                    return False
                return original_method == real_func

            if func_func == real_func:
                return True
            try:
                f = real_func.__func__  # type:ignore[union-attr]
            except AttributeError:
                return False
            else:
                return f == func_func

    def Unregister(
        self,
        func: Callable[..., Any],
        extra_args: Sequence[object] = _EXTRA_ARGS_CONSTANT,
    ) -> None:
        """
        Unregister a function previously registered with Register.

        :param object func:
            The function to be unregistered.
        """
        key = self._GetKey(func)
        self._UnregisterByKey(key)

    def _UnregisterByKey(self, key: Hashable) -> None:
        """Unregisters a function registered with Register() by providing the internal key."""
        try:
            # As there can only be 1 instance with the same id alive, it should be OK just
            # deleting it directly (because if there was a dead reference pointing to it it will
            # be already dead anyways)
            del self._callbacks[key]
        except (KeyError, AttributeError):
            # Even when unregistering some function that isn't registered we shouldn't trigger an
            # exception, just do nothing
            pass

    def UnregisterAll(self) -> None:
        """
        Unregisters all functions
        """
        self._callbacks.clear()

    def __len__(self) -> int:
        return len(self._callbacks)


def _IsCallableObject(func: object) -> bool:
    return (
        not inspect.isbuiltin(func)
        and not inspect.isfunction(func)
        and not inspect.ismethod(func)
        and not func.__class__ == functools.partial
        and func.__class__ != _CallbackWrapper
        and not getattr(func, "__CALLBACK_KEEP_STRONG_REFERENCE__", False)
    )


@attr.s(auto_attribs=True)
class _UnregisterContext:
    """
    Returned by Register(), supports easy removal of the callback later.

    Useful if many related callbacks are registered, so the contexts can be stored and used to
    unregister all the callbacks at once.
    """

    _callback: Callback
    _key: Hashable

    def Unregister(self) -> None:
        """Unregister the callback which returned this context"""
        self._callback._UnregisterByKey(self._key)


class _CallbackWrapper(Method):
    def __init__(self, weak_method_callback: Callable) -> None:
        self.weak_method_callback = weak_method_callback

        # Maintaining the OriginalMethod() interface that clients expect.
        self.OriginalMethod = weak_method_callback

    def __call__(self, sender: Any, *args: object, **kwargs: object) -> None:
        c = self.weak_method_callback()
        if c is None:
            raise ReferenceError(
                "This should never happen: The sender already died, so, "
                "how can this method still be called?"
            )
        c(sender(), *args, **kwargs)
