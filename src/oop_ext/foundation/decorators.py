
import warnings

from oop_ext.foundation.is_frozen import IsDevelopment

"""
Collection of decorator with ONLY standard library dependencies.
"""


# ===================================================================================================
# Override
# ===================================================================================================
def Override(method):
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

    def Wrapper(func):
        if func.__name__ != method.__name__:
            msg = "Wrong @Override: %r expected, but overwriting %r."
            msg = msg % (func.__name__, method.__name__)
            raise AssertionError(msg)

        if func.__doc__ is None:
            func.__doc__ = method.__doc__

        return func

    return Wrapper


# ===================================================================================================
# Implements
# ===================================================================================================
def Implements(method):
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

    def Wrapper(func):
        if func.__name__ != method.__name__:
            msg = "Wrong @Implements: %r expected, but overwriting %r."
            msg = msg % (func.__name__, method.__name__)
            raise AssertionError(msg)

        if func.__doc__ is None:
            func.__doc__ = method.__doc__

        return func

    return Wrapper


# ===================================================================================================
# Deprecated
# ===================================================================================================
def Deprecated(name=None):
    """
    Decorator that marks a method as deprecated.

    :param str name:
        The name of the method that substitutes this one, if any.
    """
    if not IsDevelopment():
        # Optimization: we don't want deprecated to add overhead in release mode.

        def DeprecatedDecorator(func):
            return func

    else:

        def DeprecatedDecorator(func):
            """
            The actual deprecated decorator, configured with the name parameter.
            """

            def DeprecatedWrapper(*args, **kwargs):
                """
                This method wrapper gives a deprecated message before calling the original
                implementation.
                """
                if name is not None:
                    msg = "DEPRECATED: '%s' is deprecated, use '%s' instead" % (
                        func.__name__,
                        name,
                    )
                else:
                    msg = "DEPRECATED: '%s' is deprecated" % func.__name__
                warnings.warn(msg, stacklevel=2)
                return func(*args, **kwargs)

            DeprecatedWrapper.__name__ = func.__name__
            DeprecatedWrapper.__doc__ = func.__doc__
            return DeprecatedWrapper

    return DeprecatedDecorator


# ===================================================================================================
# Abstract
# ===================================================================================================
def Abstract(func):
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

    def AbstractWrapper(self, *args, **kwargs):
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
    return AbstractWrapper
