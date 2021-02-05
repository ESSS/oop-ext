# mypy: disallow-untyped-defs
"""
Collection of decorator with ONLY standard library dependencies.
"""
import warnings
from typing import Callable, Optional, NoReturn, TypeVar, Any, TYPE_CHECKING, cast

from oop_ext.foundation.is_frozen import IsDevelopment


F = TypeVar("F", bound=Callable[..., Any])
G = TypeVar("G", bound=Callable[..., Any])


def Override(method: G) -> Callable[[F], F]:
    """
    Decorator that marks that a method overrides a method in the superclass.

    :param type method:
        The overridden method

    :returns function:
        The decorated function

    .. note:: This decorator actually works by only making the user to access the class and the overridden method at
    class level scope, so if in the future that method gets deleted or renamed, the import of the decorated method will
    fail.

    Example::

      class MyInterface:
        def foo():
            pass

      class MyClass(MyInterface):

        @Overrides(MyInterace.foo)
        def foo():
            pass
    """

    def Wrapper(func: F) -> F:
        if func.__name__ != method.__name__:
            msg = "Wrong @Override: %r expected, but overwriting %r."
            msg = msg % (func.__name__, method.__name__)
            raise AssertionError(msg)

        if func.__doc__ is None:
            func.__doc__ = method.__doc__

        return func

    return Wrapper


def Implements(method: G) -> Callable[[F], F]:
    """
    Decorator that marks that a method implements a method in some interface.

    :param function method:
        The implemented method

    :returns function:
        The decorated function

    :raises AssertionError:
        if the implementation method's name is different from the one
        that is being defined. This is a common error when copying/pasting the @Implements code.

    .. note:: This decorator actually works by only making the user to access the class and the implemented method at
    class level scope, so if in the future that method gets deleted or renamed, the import of the decorated method will
    fail.

    Example::

      class MyInterface:
        def foo():
            pass

      class MyClass(MyInterface):

        @Implements(MyInterace.foo)
        def foo():
            pass
    """

    def Wrapper(func: Callable) -> Callable:
        if func.__name__ != method.__name__:
            msg = "Wrong @Implements: %r expected, but overwriting %r."
            msg = msg % (func.__name__, method.__name__)
            raise AssertionError(msg)

        if func.__doc__ is None:
            func.__doc__ = method.__doc__

        return func

    return cast(Callable[[F], F], Wrapper)


def Deprecated(what: Optional[object] = None) -> Callable[[F], F]:
    """
    Decorator that marks a method as deprecated.

    :param what:
        Method that replaces the deprecated method, if any. Here it is common to pass
        either a function or the name of the method.
    """
    if not IsDevelopment():
        # Optimization: we don't want deprecated to add overhead in release mode.

        def DeprecatedDecorator(func: Callable) -> Callable:
            return func

    else:

        def DeprecatedDecorator(func: Callable) -> Callable:
            """
            The actual deprecated decorator, configured with the name parameter.
            """

            def DeprecatedWrapper(*args: object, **kwargs: object) -> object:
                """
                This method wrapper gives a deprecated message before calling the original
                implementation.
                """
                if what is not None:
                    msg = "DEPRECATED: '%s' is deprecated, use '%s' instead" % (
                        func.__name__,
                        what,
                    )
                else:
                    msg = "DEPRECATED: '%s' is deprecated" % func.__name__
                warnings.warn(msg, stacklevel=2)
                return func(*args, **kwargs)

            DeprecatedWrapper.__name__ = func.__name__
            DeprecatedWrapper.__doc__ = func.__doc__
            return DeprecatedWrapper

    return cast(Callable[[F], F], DeprecatedDecorator)


def Abstract(func: F) -> F:
    '''
    Decorator to make methods 'abstract', which are meant to be overwritten in subclasses. If some
    subclass doesn't override the method, it will raise NotImplementedError when called. Note that
    this decorator should be used together with :dec:Override.

    Example::

        class Base(object):

            @Abstract
            def Foo(self):
                """
                This method ...
                """
                # no body required here; an exception will be raised automatically


        class Derived(Base):

            @Override(Base.Foo)
            def Foo(self):
                ...

    '''

    def AbstractWrapper(self: object, *args: object, **kwargs: object) -> NoReturn:
        """
        This wrapper method replaces the implementation of the (abstract) method, providing a
        friendly message to the user.
        """
        # # Unused argument args, kwargs
        # # pylint: disable-msg=W0613
        msg = "method {} not implemented in class {}.".format(
            repr(func.__name__), repr(self.__class__)
        )
        raise NotImplementedError(msg)

    # # Redefining build-in
    # # pylint: disable-msg=W0622
    AbstractWrapper.__name__ = func.__name__
    AbstractWrapper.__doc__ = func.__doc__
    return cast(F, AbstractWrapper)
