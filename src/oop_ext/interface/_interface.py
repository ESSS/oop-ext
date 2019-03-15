"""
This module provides a basic interface concept.

To use, create an interface:


class IMyCalculator(Interface):

    def Sum(self, *values):
        ...


Have classes implement an interface:

class MyCalculatorImpl(object):

    ImplementsInterface(IMyCalculator)

    ...


Then, to check an interface:


impl = MyCalculatorImpl()

if IsImplementation(impl, IMyCalculator):
    ...


Or if it *needs* to check an interface:

AssertImplements(impl, IMyCalculator)


"""

import inspect
import sys

from oop_ext.foundation.decorators import Deprecated
from oop_ext.foundation.is_frozen import IsDevelopment
from oop_ext.foundation.types_ import Method


# ===================================================================================================
# InterfaceError
# ===================================================================================================
class InterfaceError(RuntimeError):
    pass


# ===================================================================================================
# BadImplementationError
# ===================================================================================================
class BadImplementationError(InterfaceError):
    pass


# ===================================================================================================
# InterfaceImplementationMetaClass
# ===================================================================================================
class InterfaceImplementationMetaClass(type):
    def __new__(cls, name, bases, dct):
        C = type.__new__(cls, name, bases, dct)
        if IsDevelopment():  # Only doing check in dev mode.
            for I in dct.get("__implements__", []):
                # Will do full checking this first time, and also cache the results
                AssertImplements(C, I)
        return C


# ===================================================================================================
# InterfaceImplementorStub
# ===================================================================================================
class InterfaceImplementorStub:
    """
        A helper for acting as a stub for some object (in this way, we're only able to access
        attributes declared directly in the interface.

        It forwards the calls to the actual implementor (the wrapped object)
    """

    def __init__(self, wrapped, implemented_interface):
        self.__wrapped = wrapped
        self.__implemented_interface = implemented_interface

        self.__interface_methods, self.__attrs = cache_interface_attrs.GetInterfaceMethodsAndAttrs(
            implemented_interface
        )

    def GetWrappedFromImplementorStub(self):
        """
            Really big and awkward name because we don't want name-clashes
        """
        return self.__wrapped

    def __getattr__(self, attr):
        if attr not in self.__attrs and attr not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, attr
                )
            )
        return getattr(self.__wrapped, attr)

    def __getitem__(self, *args, **kwargs):
        if "__getitem__" not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, "__getitem__"
                )
            )
        return self.__wrapped.__getitem__(*args, **kwargs)

    def __setitem__(self, *args, **kwargs):
        if "__setitem__" not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, "__setitem__"
                )
            )
        return self.__wrapped.__setitem__(*args, **kwargs)

    def __repr__(self):
        return "<InterfaceImplementorStub %s>" % self.__wrapped

    def __call__(self, *args, **kwargs):
        if "__call__" not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, "__call__"
                )
            )
        return self.__wrapped.__call__(*args, **kwargs)


# ===================================================================================================
# Interface
# ===================================================================================================
class Interface:
    """Base class for interfaces.

    A interface describes a behavior that some objects must implement.
    """

    # : instance to check if we are receiving an argument during __new__
    _SENTINEL = []

    def __new__(cls, class_=_SENTINEL):
        # if no class is given, raise InterfaceError('trying to instantiate interface')
        # check if class_or_object implements this interface
        from ._adaptable_interface import IAdaptable

        if class_ is cls._SENTINEL:
            raise InterfaceError("Can't instantiate Interface.")
        else:
            if isinstance(class_, type):
                # We're doing something as Interface(InterfaceImpl) -- not instancing
                _AssertImplementsFullChecking(class_, cls, check_attr=False)
                return class_
            elif isinstance(class_, InterfaceImplementorStub):
                return class_
            else:
                implemented_interfaces = GetImplementedInterfaces(class_)

                if cls in implemented_interfaces:
                    return InterfaceImplementorStub(class_, cls)

                elif IAdaptable in implemented_interfaces:
                    adapter = class_.GetAdapter(cls)
                    if adapter is not None:
                        return InterfaceImplementorStub(adapter, cls)

                # We're doing something as Interface(InterfaceImpl()) -- instancing
                _AssertImplementsFullChecking(class_, cls, check_attr=True)
                return InterfaceImplementorStub(class_, cls)


# ===================================================================================================
# _GetClassForInterfaceChecking
# ===================================================================================================
def _GetClassForInterfaceChecking(class_or_instance):
    if _IsClass(class_or_instance):
        return class_or_instance  # is class
    elif isinstance(class_or_instance, InterfaceImplementorStub):
        return _GetClassForInterfaceChecking(
            class_or_instance.GetWrappedFromImplementorStub()
        )

    return class_or_instance.__class__  # is instance


def _IsClass(obj):
    return isinstance(obj, type)


# ===================================================================================================
# IsImplementation
# ===================================================================================================
def IsImplementation(class_or_instance, interface):
    """
    :type class_or_instance: type or classobj or object

    :type interface: Type[Interface]

    :rtype: bool

    :see: :py:func:`.AssertImplements`
    """
    is_interface = issubclass(interface, Interface)
    if not is_interface:
        raise InterfaceError(
            "To check against an interface, an interface is required (received: %s -- mro:%s)"
            % (interface, interface.__mro__)
        )

    class_ = _GetClassForInterfaceChecking(class_or_instance)

    is_implementation, _reason = _CheckIfClassImplements(class_, interface)

    # Check older revisions of this file for helper debug code in this place.

    return is_implementation


# ===================================================================================================
# IsImplementationOfAny
# ===================================================================================================
def IsImplementationOfAny(class_or_instance, interfaces):
    """
    Check if the class or instance implements any of the given interfaces

    :type class_or_instance: type or classobj or object

    :type interfaces: list(Interface)

    :rtype: bool

    :see: :py:func:`.IsImplementation`
    """
    for interface in interfaces:
        if IsImplementation(class_or_instance, interface):
            return True

    return False


# ===================================================================================================
# AssertImplements
# ===================================================================================================
def AssertImplements(class_or_instance, interface):
    """
    If given a class, will try to match the class against a given interface. If given an object
    (instance), will try to match the class of the given object.

    NOTE: The Interface must have been explicitly declared through :py:func:`ImplementsInterface`.

    :type class_or_instance: type or classobj or object

    :type interface: Interface

    :raises BadImplementationError:
        If the object's class does not implement the given :arg interface:.

    :raises InterfaceError:
        In case the :arg interface: object is not really an interface.

    .. attention:: Caching
        Will do a full checking only once, and then cache the result for the given class.

    .. attention:: Runtime modifications
        Runtime modifications in the instances (appending methods or attributed) won't affect
        implementation checking (after the first check), because what is really being tested is the
        class.
    """
    class_ = _GetClassForInterfaceChecking(class_or_instance)

    is_implementation, reason = _CheckIfClassImplements(class_, interface)

    assert is_implementation, reason


# ===================================================================================================
# __ResultsCache
# ===================================================================================================
class __ResultsCache:
    def __init__(self):
        self._cache = {}

    def SetResult(self, args, result):
        self._cache[args] = result

    def GetResult(self, args):
        return self._cache.get(args, None)

    def ForgetResult(self, args):
        self._cache.pop(args, None)


__ImplementsCache = __ResultsCache()

__ImplementedInterfacesCache = __ResultsCache()


# ===================================================================================================
# _CheckIfClassImplements
# ===================================================================================================
def _CheckIfClassImplements(class_, interface):
    """
    :type class_: type or classobj
    :param class_:
        A class type (NOT an instance of the class).

    :type interface: Interface

    :rtype: (bool, str) or (bool, None)
    :returns:
        (is_implementation, reason)
        If the class doesn't implement the given interface, will return False, and a message stating
        the reason (missing methods, etc.). The message may be None.
    """
    assert _IsClass(class_)

    # Using explicit memoization, because we need to forget some values at some times
    cache = __ImplementsCache

    cached_result = cache.GetResult((class_, interface))
    if cached_result is not None:
        return cached_result

    is_implementation = True
    reason = None

    # Exception: Null implements every Interface (useful for Null Object Pattern and for testing)
    from oop_ext.foundation.types_ import Null

    if not issubclass(class_, Null):
        if _IsInterfaceDeclared(class_, interface):
            # It is required to explicitly declare that the class implements the interface.

            # Since this will only run *once*, a full check is also done here to ensure it is really
            # implementing.
            try:
                _AssertImplementsFullChecking(class_, interface, check_attr=False)
            except BadImplementationError as e:
                is_implementation = False
                from oop_ext.foundation.exceptions import ExceptionToUnicode

                reason = ExceptionToUnicode(e)
        else:
            is_implementation = False
            reason = "The class {} does not declare that it implements the interface {}.".format(
                class_, interface
            )

    result = (is_implementation, reason)
    cache.SetResult((class_, interface), result)
    return result


# ===================================================================================================
# _IsImplementationFullChecking
# ===================================================================================================
def _IsImplementationFullChecking(class_or_instance, interface):
    """
    Used internally by Attribute.

    :see: :py:func:`._AssertImplementsFullChecking`
    :type class_or_instance: type or instance
    :param class_or_instance:
        Class or instance to check

    :param Interface interface:
        Interface to check

    :rtype: bool
    :returns:
        If it implements the interface
    """
    try:
        _AssertImplementsFullChecking(class_or_instance, interface)
    except BadImplementationError:
        return False
    else:
        return True


# ===================================================================================================
# Attribute
# ===================================================================================================
class Attribute:
    """
    """

    _do_not_check_instance = object()

    def __init__(self, attribute_type, instance=_do_not_check_instance):
        """
        :param type attribute_type:
            Will check the attribute type in the implementation against this type.
            Checks if the attribute is a direct instance of attribute_type, or of it implements it.

        :param object instance:
            If passed, will check for *equality* against this instance. The default is to not check
            for equality.
        """
        self.attribute_type = attribute_type
        self.instance = instance

    def Match(self, attribute):
        """
        :param object attribute:
            Object that will be compared to see if it matches the expected interface.

        :rtype: (bool, str)
        :returns:
            If the given object implements or inherits from the interface expected by this
            attribute, will return (True, None), otherwise will return (False, message), where
            message is an error message of why there was a mismatch (may be None also).
        """
        msg = None

        if isinstance(attribute, self.attribute_type):
            return (True, None)

        if self.instance is not self._do_not_check_instance:
            if self.instance == attribute:
                return (True, None)
            else:
                return (
                    False,
                    "The instance ({}) does not match the expected one ({}).".format(
                        self.instance, attribute
                    ),
                )

        try:
            if _IsImplementationFullChecking(attribute, self.attribute_type):
                return (True, msg)
        except InterfaceError as exception_msg:
            # Necessary because whenever a value is compared to an interface it does not inherits
            # from, IsImplementation raises an InterfaceError. In this context, an error like that
            # will mean that our candidate attribute is in fact not matching the interface, so we
            # capture this error and return False.
            msg = exception_msg

        return (False, None)


# ===================================================================================================
# ReadOnlyAttribute
# ===================================================================================================
class ReadOnlyAttribute(Attribute):
    """
    This is an attribute that should be treated as read-only (note that usually this means that
    the related property should be also declared as read-only).
    """


# ===================================================================================================
# CacheInterfaceAttrs
# ===================================================================================================
class CacheInterfaceAttrs:
    """
    Cache for holding the attrs for a given interface (separated by attrs and methods).
    """

    _ATTRIBUTE_CLASSES = (Attribute, ReadOnlyAttribute)
    INTERFACE_OWN_METHODS = {
        i for i in dir(Interface) if inspect.isfunction(getattr(Interface, i))
    }
    FUTURE_OBJECT_ATTRS = (
        "next",
        "__long__",
        "__nonzero__",
        "__unicode__",
        "__native__",
    )

    @classmethod
    def RegisterAttributeClass(cls, attribute_class):
        """
        Registers a class to be considered as an attribute class.

        This provides a way of extending the Interface behavior by declaring new attributes classes
        such as ScalarAttribute.

        :param Attribute attribute_class:
            An Attribute class to register as an attribute class.

        :return set(Attribute):
            Returns a set with all the current attribute classes.
        """
        result = set(cls._ATTRIBUTE_CLASSES)
        result.add(attribute_class)
        cls._ATTRIBUTE_CLASSES = tuple(result)
        return result

    def __GetInterfaceMethodsAndAttrs(self, interface):
        """
            :type interface: the interface from where the methods and attributes should be gotten.
            :param interface:
            :rtype: the interface methods and attributes available in a given interface.
        """
        all_attrs = dir(interface)

        interface_methods = dict()
        interface_attrs = dict()
        interface_vars = vars(interface)

        # Python 3+ changed how functions are represented, so it isn't possible anymore to
        # determine if a function is a method BEFORE it is bound to an object.
        # For this reason, it is necessary to also search by functions on Python and to filter out
        # functions like `__new__`, which are part of `Interface` class implementation and not part
        # expected interface.
        for attr in all_attrs:
            # If name inherited from `Interface`, check if isn't in list of reserved names
            if attr not in interface_vars:
                if attr in self.INTERFACE_OWN_METHODS:
                    continue

            val = getattr(interface, attr)

            if type(val) in self._ATTRIBUTE_CLASSES:
                interface_attrs[attr] = val

            if _IsMethod(val, include_functions=True):
                interface_methods[attr] = val

        return interface_methods, interface_attrs

    def GetInterfaceMethodsAndAttrs(self, interface):
        """
            We have to make the creation of the ImmutableParamsCacheManager lazy because
            otherwise we'd enter a cyclic import.

            :type interface: the interface from where the methods and attributes should be gotten
            :param interface:
                (used as the cache-key)
            :rtype: @see: CacheInterfaceAttrs.__GetInterfaceMethodsAndAttrs
        """
        try:
            cache = self.cache
        except AttributeError:
            # create it on the 1st access
            from oop_ext.foundation.cached_method import ImmutableParamsCachedMethod

            cache = self.cache = ImmutableParamsCachedMethod(
                self.__GetInterfaceMethodsAndAttrs
            )
        return cache(interface)


# cache for the interface attrs (for Methods and Attrs).
cache_interface_attrs = CacheInterfaceAttrs()


# ===================================================================================================
# _IsMethod
# ===================================================================================================
def _IsMethod(member, include_functions):
    """
        Consider method the following:
            1) Methods
            2) Functions (if include_functions is True)
            3) instances of Method (should it be implementors of "IMethod"?)

        USER: cache mechanism for coilib50.basic.process
    """
    if include_functions and inspect.isfunction(member):
        return True
    elif inspect.ismethod(member):
        return True
    elif isinstance(member, Method):
        return True
    return False


# ===================================================================================================
# AssertImplementsFullChecking
# ===================================================================================================
@Deprecated(AssertImplements)
def AssertImplementsFullChecking(class_or_instance, interface, check_attr=True):
    return AssertImplements(class_or_instance, interface)


# ===================================================================================================
# _AssertImplementsFullChecking
# ===================================================================================================
def _AssertImplementsFullChecking(class_or_instance, interface, check_attr=True):
    """
    Used internally.

    This method will check each member of the given instance (or class) comparing them against the
    ones declared in the interface, making sure that it actually implements it even if it does not
    declare it so using ImplementsInterface.

    .. note:: Slow
        This method is *slow*, so make sure to never use it in hot-spots.

    :raises BadImplementationError:
        If :arg class_or_instance: doesn't implement this interface.
    """
    # Moved from the file to avoid cyclic import:
    from oop_ext.foundation.types_ import Null

    is_interface = issubclass(interface, Interface)
    if not is_interface:
        raise InterfaceError(
            "To check against an interface, an interface is required (received: %s -- mro:%s)"
            % (interface, interface.__mro__)
        )

    if isinstance(class_or_instance, Null):
        return True

    try:
        classname = class_or_instance.__name__
    except:
        classname = class_or_instance.__class__.__name__

    if classname == "InterfaceImplementorStub":
        return _AssertImplementsFullChecking(
            class_or_instance.GetWrappedFromImplementorStub(), interface, check_attr
        )

    interface_methods, interface_attrs = cache_interface_attrs.GetInterfaceMethodsAndAttrs(
        interface
    )
    if check_attr:
        for attr_name, val in interface_attrs.items():
            if hasattr(class_or_instance, attr_name):
                attr = getattr(class_or_instance, attr_name)
                match, match_msg = val.Match(attr)
                if not match:
                    msg = "Attribute %r for class %s does not match the interface %s"
                    msg = msg % (attr_name, class_or_instance, interface)
                    if match_msg:
                        msg += ": " + match_msg
                    raise BadImplementationError(msg)
            else:
                msg = "Attribute %r is missing in class %s and it is required by interface %s"
                msg = msg % (attr_name, class_or_instance, interface)
                raise BadImplementationError(msg)

    def GetArgSpec(method):
        """
            Get the arguments for the method, considering the possibility of instances of Method,
            in which case, we must obtain the arguments of the instance "__call__" method.

            USER: cache mechanism for coilib50.basic.process
        """
        if isinstance(method, Method):
            argspec = inspect.getfullargspec(method.__call__)
        else:
            argspec = inspect.getfullargspec(method)
        assert (not argspec.kwonlyargs) and (
            not argspec.kwonlydefaults
        ), "Not supported"
        return argspec[:4]

    for name in interface_methods:
        # only check the interface methods (because trying to get all the instance methods is
        # too slow).
        try:
            cls_method = getattr(class_or_instance, name)
            if not _IsMethod(cls_method, True):
                raise AttributeError

        except AttributeError:
            msg = "Method %r is missing in class %r (required by interface %r)"
            raise BadImplementationError(msg % (name, classname, interface.__name__))
        else:
            interface_method = interface_methods[name]

            c_args, c_varargs, c_varkw, c_defaults = GetArgSpec(cls_method)

            if c_varargs is not None and c_varkw is not None:
                if not c_args or c_args == ["self"] or c_args == ["cls"]:
                    # Accept the implementor if it matches the signature: (*args, **kwargs)
                    # Accept the implementor if it matches the signature: (self, *args, **kwargs)
                    # Accept the implementor if it matches the signature: (cls, *args, **kwargs)
                    continue

            i_args, i_varargs, i_varkw, i_defaults = GetArgSpec(interface_method)

            # Rules:
            #
            #   1. Variable arguments or keyword arguments: if present
            #      in interface, then it MUST be present in class too
            #
            #   2. Arguments: names must be the same
            #
            #   3. Defaults: for now we assume that default values
            #      must be the same too
            mismatch_varargs = i_varargs is not None and c_varargs is None
            mismatch_varkw = i_varkw is not None and c_varkw is None
            mismatch_args = i_args != c_args
            mismatch_defaults = i_defaults != c_defaults
            if mismatch_varargs or mismatch_varkw or mismatch_args or mismatch_defaults:
                class_sign = inspect.formatargspec(
                    c_args, c_varargs, c_varkw, c_defaults
                )
                interface_sign = inspect.formatargspec(
                    i_args, i_varargs, i_varkw, i_defaults
                )
                msg = "\nMethod %s.%s signature:\n  %s\ndiffers from defined in interface %s\n  %s"
                msg = msg % (
                    classname,
                    name,
                    class_sign,
                    interface.__name__,
                    interface_sign,
                )
                raise BadImplementationError(msg)


# ===================================================================================================
# PROFILING FOR ASSERT IMPLEMENTS

# NOTE: There was code here for profiling AssertImplements in revisions prior to 2013-03-19.
#       That code can be useful for seeing where exactly it is being slow.
# ===================================================================================================


class _IfGuard:
    """
    Guard that raises an error if an attempt to convert it to a boolean value is made.
    """

    def __bool__(self):
        raise RuntimeError(
            "Invalid attempt to test interface.ImplementsInterface(). Did you mean interface.IsImplementation()?"
        )


__IF_GUARD = _IfGuard()

DEBUG = False


# ===================================================================================================
# ImplementsInterface
# ===================================================================================================
def ImplementsInterface(*interfaces, **kwargs):
    """
    Make sure a class implements the given interfaces. Must be used in as class decorator:

    ```python
    @ImplementsInterface(IFoo)
    class Foo(object):
        pass
    ```

    To avoid checking if the class implements declared interfaces during class creation time, or for
    old-style classes, make sure to pass the flag `no_check` as True:

    ```python
    @ImplementsInterface(IFoo, no_check=True)
    class Foo(object):
        pass
    ```
    """
    no_check = kwargs.pop("no_check", False)
    assert (
        len(kwargs) == 0
    ), "Expected only 'no_init_check' as kwargs. Found: {}".format(kwargs)

    called = [False]

    class Check:
        def __init__(self):
            def _OnDie(ref):
                # We may just use warnings.warn in the future, after our
                # codebase is properly 'sanitized', instead of handle_exception.
                #
                # This is to prevent users of doing an ImplementsInterface()
                # without using it as a decorator.
                if not called[0]:
                    if not DEBUG:
                        created_at_line = "\nSet DEBUG == True in: {} to see location.".format(
                            __file__
                        )
                    else:
                        # This may be slow, so, just do it if DEBUG is enabled.
                        import traceback

                        created_at_line = traceback.extract_stack(
                            sys._getframe(), limit=10
                        )

                    if isinstance(created_at_line, str):
                        created_at_str = created_at_line
                    else:
                        created_at_str = "".join(traceback.format_list(created_at_line))

                    raise AssertionError(
                        "A call with ImplementsInterface({}) was not properly done as a class decorator.\nCreated at: {}".format(
                            ", ".join(
                                tuple(
                                    str(getattr(x, "__name__", x)) for x in interfaces
                                )
                            ),
                            created_at_str,
                        )
                    )

            import weakref

            self._ref = weakref.ref(self, _OnDie)

        def __call__(self, type_):
            called[0] = True
            namespace = type_
            curr = getattr(namespace, "__implements__", None)
            if curr is not None:
                all_interfaces = curr + interfaces
            else:
                all_interfaces = interfaces
            namespace.__implements__ = all_interfaces

            if not no_check:
                if IsDevelopment():  # Only doing check in dev mode.
                    for I in interfaces:
                        # Will do full checking this first time, and also cache the results
                        AssertImplements(type_, I)

            return type_

        def __bool__(self):
            called[0] = True
            raise RuntimeError(
                "Invalid attempt to test interface.ImplementsInterface(). Did you "
                "mean interface.IsImplementation()?"
            )

        def __nonzero__(self):
            # Py 2 compatibility
            return self.__bool__()

    return Check()


# ===================================================================================================
# DeclareClassImplements
# ===================================================================================================
def DeclareClassImplements(class_, *interfaces):
    """
    This is a way to tell, from outside of the class, that a given :arg class_: implements the
    given :arg interfaces:.

    .. attention:: Use Implements whenever possible
        This method should be used only when you can't use :py:func:`Implements`, or when you can't
        change the code of the class being declared, i.e., when you:
        * Can't add metaclass because the class already has one
        * Class can't depend on the library where the interface is defined
        * Class is defined from bindings
        * Class is defined in an external library
        * Class is defined by generated code

    :type interfaces: list(Interface)
    :type class_: type

    :raises BadImplementationError:
        If, after checking the methods, :arg class_: doesn't really implement the :arg interface:.

    .. note:: Inheritance
        When you use this method to declare that a base class implements a given interface, you
        should *also* use this in the derived classes, it does not propagate automatically to
        the derived classes. See testDeclareClassImplements.
    """
    assert _IsClass(class_)

    from itertools import chain

    old_implements = getattr(class_, "__implements__", [])
    class_.__implements__ = list(chain(old_implements, interfaces))

    # This check must be done *after* adding the interfaces to __implements__, because it will
    # also check that the interfaces are declared there.
    try:
        for interface in interfaces:
            # Forget any previous checks
            __ImplementsCache.ForgetResult((class_, interface))
            __ImplementedInterfacesCache.ForgetResult(class_)

            AssertImplements(class_, interface)
    except:
        # Roll back...
        class_.__implements__ = old_implements
        raise


# ===================================================================================================
# _GetMROForOldStyleClass
# ===================================================================================================
def _GetMROForOldStyleClass(class_):
    """
    :type class_: classobj
    :param class_:
        An old-style class

    :rtype: list(classobj)
    :return:
        A list with all the bases in the older MRO (method resolution order)
    """

    def _CalculateMro(class_, mro):
        for base in class_.__bases__:
            if base not in mro:
                mro.append(base)
                _CalculateMro(base, mro)

    mro = [class_]
    _CalculateMro(class_, mro)
    return mro


# ===================================================================================================
# _GetClassImplementedInterfaces
# ===================================================================================================
def _GetClassImplementedInterfaces(class_):
    cache = __ImplementedInterfacesCache
    result = cache.GetResult(class_)
    if result is not None:
        return result

    result = set()

    mro = inspect.getmro(class_)

    for c in mro:
        interfaces = getattr(c, "__implements__", ())
        for interface in interfaces:
            interface_mro = inspect.getmro(interface)

            for interface_type in interface_mro:
                if interface_type in (Interface, object):
                    continue
                result.add(interface_type)

    result = frozenset(result)

    cache.SetResult(class_, result)
    return result


# ===================================================================================================
# GetImplementedInterfaces
# ===================================================================================================
def GetImplementedInterfaces(class_or_object):
    """
   :rtype: frozenset([interfaces])
       The interfaces implemented by the object or class passed.
    """
    class_ = _GetClassForInterfaceChecking(class_or_object)

    # we have to build the cache attribute given the name of the class, otherwise setting in a base
    # class before a subclass may give errors.
    return _GetClassImplementedInterfaces(class_)


# ===================================================================================================
# _IsInterfaceDeclared
# ===================================================================================================
def _IsInterfaceDeclared(class_, interface):
    """
        :type interface: Interface or iterable(Interface)
        :param interface:
            The target interface(s). If multitple interfaces are passed the method will return True
            if the given class or instance implements any of the given interfaces.

        :rtype: True if the object declares the interface passed and False otherwise. Note that
        to declare an interface, the class MUST have declared

            >>> ImplementsInterface(Class)
    """
    if class_ is None:
        return False

    is_collection = False
    if isinstance(interface, (set, list, tuple)):
        is_collection = True
        for i in interface:
            if not issubclass(i, Interface):
                raise InterfaceError(
                    "To check against an interface, an interface is required (received: %s -- mro:%s)"
                    % (interface, interface.__mro__)
                )
    elif not issubclass(interface, Interface):
        raise InterfaceError(
            "To check against an interface, an interface is required (received: %s -- mro:%s)"
            % (interface, interface.__mro__)
        )

    declared_interfaces = GetImplementedInterfaces(class_)

    # This set will include all interfaces (and its subclasses) declared for the given objec
    declared_and_subclasses = set()
    for implemented in declared_interfaces:
        declared_and_subclasses.update(implemented.__mro__)

    # Discarding object (it will always be returned in the mro collection)
    declared_and_subclasses.discard(object)

    if not is_collection:
        return interface in declared_and_subclasses
    else:
        return bool(set(interface).intersection(declared_and_subclasses))


# ===================================================================================================
# PROFILING FOR IsInterfaceDeclared

# NOTE: There was code here for profiling IsInterfaceDeclared in revisions prior to 2013-03-19.
#       That code can be useful for seeing where exactly it is being called.
# ===================================================================================================


# ===================================================================================================
# AssertDeclaresInterface
# ===================================================================================================
@Deprecated(AssertImplements)
def AssertDeclaresInterface(class_or_instance, interface):
    return AssertImplements(class_or_instance, interface)
