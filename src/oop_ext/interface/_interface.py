# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
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
from contextlib import suppress
from typing import (
    TypeVar,
    Generic,
    Type,
    Any,
    Sequence,
    Tuple,
    Optional,
    Dict,
    Set,
    Union,
    TYPE_CHECKING,
    Callable,
    List,
    FrozenSet,
    NoReturn,
)

from oop_ext.foundation.decorators import Deprecated
from oop_ext.foundation.is_frozen import IsDevelopment
from oop_ext.foundation.types_ import Method
from oop_ext.foundation.cached_method import ImmutableParamsCachedMethod

if TYPE_CHECKING:
    from traceback import StackSummary


# TypeCheckingSupport acts as a subclass during type checking so the type-checker
# recognizes Interface subclasses as Protocol implementations.
# When subclassing a Protocol, the subclass must also explicitly subclass Protocol again
# for the type checker to recognize them:
#
# https://www.python.org/dev/peps/pep-0544/#merging-and-extending-protocols
#
# Quote:
# Subclassing a protocol class would not turn the subclass into a protocol unless
# it also has typing.Protocol as an explicit base class.
#
# We declare TypeCheckingSupport as an alias to Protocol only during type checking,
# because Protocol is a complex meta class and brings a bunch of problems when trying to use
# it as an Interface superclass, namely declaring new methods
# (__init__, __init_subclass__, __getitem__, etc) which our Interface code now assumes
# should be part of the interface.
#
# By using a custom alias, only really enabled during type-checking, we hide that detail
# from users and avoid the runtime problems.
if TYPE_CHECKING:
    from typing_extensions import Protocol as TypeCheckingSupport
else:
    TypeCheckingSupport = object


class InterfaceError(RuntimeError):
    pass


class BadImplementationError(InterfaceError):
    pass


class InterfaceImplementationMetaClass(type):
    def __new__(cls, name: str, bases: Tuple, dct: Dict) -> Any:
        C = type.__new__(cls, name, bases, dct)
        if IsDevelopment():  # Only doing check in dev mode.
            for I in dct.get("__implements__", []):
                # Will do full checking this first time, and also cache the results
                AssertImplements(C, I)
        return C


T = TypeVar("T")


class InterfaceImplementorStub(Generic[T]):
    """
    A helper for acting as a stub for some object (in this way, we're only able to access
    attributes declared directly in the interface.

    It forwards the calls to the actual implementor (the wrapped object)
    """

    def __init__(self, wrapped: T, implemented_interface: Type["Interface"]) -> None:
        self.__wrapped = wrapped
        self.__implemented_interface = implemented_interface

        (
            self.__interface_methods,
            self.__attrs,
        ) = cache_interface_attrs.GetInterfaceMethodsAndAttrs(implemented_interface)

    def GetWrappedFromImplementorStub(self) -> T:
        """
        Really big and awkward name because we don't want name-clashes
        """
        return self.__wrapped

    def __getattr__(self, attr: str) -> Any:
        if attr not in self.__attrs and attr not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, attr
                )
            )
        return getattr(self.__wrapped, attr)

    def __getitem__(self, *args: Any, **kwargs: Any) -> Any:
        if "__getitem__" not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, "__getitem__"
                )
            )
        return self.__wrapped.__getitem__(*args, **kwargs)  # type:ignore[index]

    def __setitem__(self, *args: Any, **kwargs: Any) -> Any:
        if "__setitem__" not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, "__setitem__"
                )
            )
        return self.__wrapped.__setitem__(*args, **kwargs)  # type:ignore[index]

    def __repr__(self) -> str:
        return "<InterfaceImplementorStub %s>" % self.__wrapped

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if "__call__" not in self.__interface_methods:
            raise AttributeError(
                "Error. The interface {} does not have the attribute '{}' declared.".format(
                    self.__implemented_interface, "__call__"
                )
            )
        return self.__wrapped.__call__(*args, **kwargs)  # type:ignore[operator]


# Instance to check if we are receiving an argument during Interface.__new__
_SENTINEL = object()


class Interface(TypeCheckingSupport):
    """Base class for interfaces.

    A interface describes a behavior that some objects must implement.

    **TypeCheckingSupport**

    .. versionadded:: 1.1.0

    Interfaces that which to support static type checkers such as ``mypy`` also need to subclass
    from this class:

    .. code-block:: python

        from oop_ext.interface import Interface, TypeCheckingSupport


        class IDataSaver(Interface, TypeCheckingSupport):
            ...


    The ``TypeCheckingSupport`` exists solely for the benefit of type checkers, and has zero runtime
    cost associated with it.
    """

    def __new__(cls, class_: Any = _SENTINEL) -> Any:
        """
        The __new__ method of an interface has two behaviors:

        1. Receiving a class

        In this case the class is verified to implement the interface, and returned unchanged.

        2. Receiving an instance

        In this case the instance is verified to implement the interface, and an
        ``InterfaceImplementorStub`` is returned.

        A note about type checking:

        mypy has restrictions about what __new__ can do (it must return an instance of the
        class), and this is violated here, so we can't really use type checking in __new__
        for the cases used by Interface.
        """
        # if no class is given, raise InterfaceError('trying to instantiate interface')
        # check if class_or_object implements this interface
        from ._adaptable_interface import IAdaptable

        if class_ is _SENTINEL:
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

    if not TYPE_CHECKING:

        @classmethod
        def __init_subclass__(cls, **kwargs: object) -> None:

            for name in dir(cls):
                obj = getattr(cls, name)
                if _IsMethod(obj):
                    sig = inspect.signature(obj)
                    try:
                        hash(sig)
                    except TypeError:
                        raise TypeError(
                            f"Method {cls.__name__}.{name} contains unhashable arguments:\n{sig}"
                        ) from None


def _GetClassForInterfaceChecking(class_or_instance: Any) -> Type:
    if _IsClass(class_or_instance):
        return class_or_instance  # is class
    elif isinstance(class_or_instance, InterfaceImplementorStub):
        return _GetClassForInterfaceChecking(
            class_or_instance.GetWrappedFromImplementorStub()
        )

    return class_or_instance.__class__  # is instance


def _IsClass(obj: object) -> bool:
    return isinstance(obj, type)


if TYPE_CHECKING:

    def _CheckIsInterfaceSubclass(interface: Any) -> None:
        pass


else:

    def _CheckIsInterfaceSubclass(interface: Any) -> None:
        """
        Checks that the given class is an Interface subclass.

        Note: during type-checking this is a no-op, because during type checking Interface
        subclasses Protocol, however issubclass will only work in Protocol subclasses decorated
        with @runtime_checkable; given this is not really used during type-checking, a
        no-op during type checking seems a good solution.
        """
        # noinspection PyProtocol
        is_interface = issubclass(interface, Interface)
        if not is_interface:
            raise InterfaceError(
                "To check against an interface, an interface is required (received: %s -- mro:%s)"
                % (interface, interface.__mro__)
            )


def IsImplementation(
    class_or_instance: Any,
    interface: Type[Interface],
    *,
    requires_declaration: bool = True,
) -> bool:
    """
    :type class_or_instance: type or classobj or object

    :type interface: Type[Interface]

    :type requires_declaration: bool
        If `True`, the Interface must have been explicitly declared through :py:func:`ImplementsInterface`
        for `class_or_interface` to be considered an implementation of `interface`. Otherwise it'd only
        check if `class_or_interface` has all methods defined on `interface`.
        Note that `class_or_instance` attributes are never evaluated.
        Alternatively, it's possible to use :py:func:`DeclareClassImplements` from outside the class in
        order to tell which interfaces are implemented.

    :rtype: bool

    :see: :py:func:`.AssertImplements`
    """
    _CheckIsInterfaceSubclass(interface)

    class_ = _GetClassForInterfaceChecking(class_or_instance)

    is_implementation, _reason = _CheckIfClassImplements(
        class_, interface, requires_declaration=requires_declaration
    )

    # Check older revisions of this file for helper debug code in this place.
    return is_implementation


def IsImplementationOfAny(
    class_or_instance: Any,
    interfaces: Sequence[Type[Interface]],
    *,
    requires_declaration: bool = True,
) -> bool:
    """
    Check if the class or instance implements any of the given interfaces

    :param class_or_instance: type or classobj or object.

    :param interfaces: interfaces to check.

    :param requires_declaration:
        If `True`, the Interface must have been explicitly declared through :py:func:`ImplementsInterface`
        for `class_or_interface` to be considered an implementation of `interface`. Alternatively, it's
        possible to use :py:func:`DeclareClassImplements` from outside the class in order to tell that
        interfaces are implemented.

    :see: :py:func:`.IsImplementation`
    """
    return any(
        IsImplementation(
            class_or_instance, x, requires_declaration=requires_declaration
        )
        for x in interfaces
    )


def AssertImplements(
    class_or_instance: Any,
    interface: Type[Interface],
    *,
    requires_declaration: bool = True,
) -> None:
    """
    If given a class, will try to match the class against a given interface. If given an object
    (instance), will try to match the class of the given object.

    :type class_or_instance: type or classobj or object

    :type interface: Interface

    :type requires_declaration: bool
        If `True`, the Interface must have been explicitly declared through :py:func:`ImplementsInterface`
        for `class_or_interface` to be considered an implementation of `interface`. Alternatively, it's
        possible to use :py:func:`DeclareClassImplements` from outside the class in order to tell that
        interfaces are implemented.

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

    is_implementation, reason = _CheckIfClassImplements(
        class_, interface, requires_declaration=requires_declaration
    )

    assert is_implementation, reason


# Using explicit memoization, because we need to forget some values at some times
__ImplementsCache: Dict[
    Tuple[Type, Type[Interface], bool], Tuple[bool, Optional[str]]
] = {}
__ImplementedInterfacesCache: Dict[Type, FrozenSet[Type[Interface]]] = {}


def _CheckIfClassImplements(
    class_: Type, interface: Type[Interface], *, requires_declaration: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    :type class_: type or classobj
    :param class_:
        A class type (NOT an instance of the class).

    :type interface: Interface

    :type requires_declaration: bool
        See :py:func:`IsImplementation`

    :rtype: (bool, str) or (bool, None)
    :returns:
        (is_implementation, reason)
        If the class doesn't implement the given interface, will return False, and a message stating
        the reason (missing methods, etc.). The message may be None.
    """
    with suppress(KeyError):
        return __ImplementsCache[(class_, interface, requires_declaration)]

    assert _IsClass(class_)

    is_implementation = True
    reason = None
    # Exception: Null implements every Interface (useful for Null Object Pattern and for testing)
    from oop_ext.foundation.types_ import Null

    if not issubclass(class_, Null):
        try:
            _AssertImplementsFullChecking(class_, interface, check_attr=False)
        except BadImplementationError as e:
            is_implementation = False
            from oop_ext.foundation.exceptions import ExceptionToUnicode

            reason = ExceptionToUnicode(e)

    if (
        is_implementation
        and requires_declaration
        and not _IsInterfaceDeclared(class_, interface)
    ):
        is_implementation = False
        reason = (
            "The class or object '{}' does not declare that it implements interface '{}' "
            "and 'requires_declaration' is True.".format(class_, interface)
        )

    result = (is_implementation, reason)
    __ImplementsCache[(class_, interface, requires_declaration)] = result
    return result


def _IsImplementationFullChecking(
    class_or_instance: Any, interface: Type[Interface]
) -> bool:
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


def _IsInterfaceDeclared(class_: Optional[Type], interface: Type[Interface]) -> bool:
    """
    :type interface: Interface
    :param interface:
        The target interface.
    :rtype:
        True if the object declares the interface passed and False otherwise. Note that
    to declare an interface, the class MUST have declared it with :py:func:`ImplementsInterface`
    """
    if class_ is None:
        return False

    _CheckIsInterfaceSubclass(interface)

    declared_interfaces = GetImplementedInterfaces(class_)

    # This set will include all interfaces (and its subclasses) declared for the given object
    declared_and_subclasses: Set[Type] = set()
    for implemented in declared_interfaces:
        declared_and_subclasses.update(implemented.__mro__)

    # Discarding object (it will always be returned in the mro collection)
    declared_and_subclasses.discard(object)

    return interface in declared_and_subclasses


class Attribute:
    """"""

    _do_not_check_instance = object()

    def __init__(
        self, attribute_type: Type, instance: object = _do_not_check_instance
    ) -> None:
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

    def Match(self, attribute: object) -> Tuple[bool, Optional[str]]:
        """
        :param object attribute:
            Object that will be compared to see if it matches the expected interface.

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


class ReadOnlyAttribute(Attribute):
    """
    This is an attribute that should be treated as read-only (note that usually this means that
    the related property should be also declared as read-only).
    """


class CacheInterfaceAttrs:
    """
    Cache for holding the attrs for a given interface (separated by attrs and methods).
    """

    _ATTRIBUTE_CLASSES: Tuple[Any, ...] = (Attribute, ReadOnlyAttribute)
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
    def RegisterAttributeClass(
        cls: Type["CacheInterfaceAttrs"], attribute_class: Type[Attribute]
    ) -> Set[Attribute]:
        """
        Registers a class to be considered as an attribute class.

        This provides a way of extending the Interface behavior by declaring new attributes classes
        such as ScalarAttribute.

        :param Attribute attribute_class:
            An Attribute class to register as an attribute class.

        :return set(Attribute):
            Returns a set with all the current attribute classes.
        """
        result: Set[Any] = set(cls._ATTRIBUTE_CLASSES)
        result.add(attribute_class)
        cls._ATTRIBUTE_CLASSES = tuple(result)
        return result

    def __GetInterfaceMethodsAndAttrs(
        self, interface: Type[Interface]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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

            if _IsMethod(val):
                interface_methods[attr] = val

        return interface_methods, interface_attrs

    cache: ImmutableParamsCachedMethod

    def GetInterfaceMethodsAndAttrs(
        self, interface: Type[Interface]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
            cache = self.cache = ImmutableParamsCachedMethod(
                self.__GetInterfaceMethodsAndAttrs
            )
        return cache(interface)


# cache for the interface attrs (for Methods and Attrs).
cache_interface_attrs = CacheInterfaceAttrs()


def _IsMethod(member: object) -> bool:
    """
    Consider method the following:
        1) Methods
        2) Functions
        3) instances of Method (should it be implementors of "IMethod"?)

    """
    from unittest import mock

    return (
        inspect.isfunction(member)
        or inspect.ismethod(member)
        or isinstance(member, Method)
        or isinstance(member, mock.MagicMock)
    )


@Deprecated(AssertImplements)
def AssertImplementsFullChecking(
    class_or_instance: object, interface: Type[Interface], check_attr: bool = True
) -> None:
    return AssertImplements(class_or_instance, interface)


# set of methods that might be declared in interfaces but should be not be required by implementations
_INTERFACE_METHODS_TO_IGNORE = {"__init_subclass__"}


def _AssertImplementsFullChecking(
    class_or_instance: Any, interface: Type[Interface], check_attr: bool = True
) -> None:
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

    _CheckIsInterfaceSubclass(interface)

    if isinstance(class_or_instance, Null):
        return

    try:
        classname = class_or_instance.__name__
    except:
        classname = class_or_instance.__class__.__name__

    if classname == "InterfaceImplementorStub":
        _AssertImplementsFullChecking(
            class_or_instance.GetWrappedFromImplementorStub(), interface, check_attr
        )

    (
        interface_methods,
        interface_attrs,
    ) = cache_interface_attrs.GetInterfaceMethodsAndAttrs(interface)
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

    def GetSignature(method: Any) -> inspect.Signature:
        """
        Get the inspect.Signature object for the method, considering the possibility of instances of Method,
        in which case, we must obtain the arguments of the instance "__call__" method.
        """
        if isinstance(method, Method):
            return inspect.signature(type(method).__call__)
        else:
            return inspect.signature(method)

    # methods which use the following signatures always match against interface method checks
    acceptable_impl_signatures = {
        inspect.Signature.from_callable(lambda *args, **kwargs: None),
        inspect.Signature.from_callable(lambda self, *args, **kwargs: None),
        inspect.Signature.from_callable(lambda cls, *args, **kwargs: None),
    }

    class_ = _GetClassForInterfaceChecking(class_or_instance)

    for name in interface_methods:
        if name in _INTERFACE_METHODS_TO_IGNORE:
            continue
        try:
            cls_or_obj_method = getattr(class_or_instance, name)
            if not _IsMethod(cls_or_obj_method):
                raise AttributeError

        except AttributeError:
            msg = "Method %r is missing in class %r (required by interface %r)"
            raise BadImplementationError(msg % (name, classname, interface.__name__))
        else:
            interface_method = interface_methods[name]

            # get the signature from the class because inspect.signature for bound methods
            # doesn't include "self"
            cls_method = getattr(class_, name)

            impl_sig = GetSignature(cls_method)

            try:
                hash(impl_sig)
            except TypeError:
                raise TypeError(
                    f"Implementation {class_.__name__}.{name} contains unhashable arguments:\n{impl_sig}"
                )

            if impl_sig in acceptable_impl_signatures:
                continue

            interface_sig = GetSignature(interface_method)

            if interface_sig != impl_sig:
                msg = (
                    f"\n"
                    f"Method {classname}.{name} signature:\n"
                    f"  {impl_sig}\n"
                    f"differs from defined in interface {interface.__name__}\n"
                    f"  {interface_sig}"
                )
                raise BadImplementationError(msg)


DEBUG = False


def ImplementsInterface(*interfaces: Any, no_check: bool = False) -> Callable[[T], T]:
    """
    Make sure a class implements the given interfaces. Must be used in as class decorator:

    .. code-block:: python

        @ImplementsInterface(IFoo)
        class Foo(object):
            ...

    :param no_check:
        If ``True``, does not check if the class implements the declared interfaces
        during import time.
    """
    called = [False]

    class Check:
        def __init__(self) -> None:
            def _OnDie(ref: Any) -> None:
                # We may just use warnings.warn in the future, after our
                # codebase is properly 'sanitized', instead of handle_exception.
                #
                # This is to prevent users of doing an ImplementsInterface()
                # without using it as a decorator.
                if not called[0]:
                    created_at_line: Union[str, "StackSummary"]
                    if not DEBUG:
                        created_at_line = (
                            "\nSet DEBUG == True in: {} to see location.".format(
                                __file__
                            )
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

        def __call__(self, type_: T) -> T:
            called[0] = True
            namespace = type_
            curr = getattr(namespace, "__implements__", None)
            if curr is not None:
                all_interfaces = curr + interfaces
            else:
                all_interfaces = interfaces
            namespace.__implements__ = all_interfaces  # type:ignore[attr-defined]

            if not no_check:
                if IsDevelopment():  # Only doing check in dev mode.
                    for I in interfaces:
                        # Will do full checking this first time, and also cache the results
                        AssertImplements(type_, I)

            return type_

        def __bool__(self) -> NoReturn:
            called[0] = True
            raise RuntimeError(
                "Invalid attempt to test interface.ImplementsInterface(). Did you "
                "mean interface.IsImplementation()?"
            )

    return Check()


def DeclareClassImplements(class_: Type, *interfaces: Type[Interface]) -> None:
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
            __ImplementsCache.pop((class_, interface, False), None)
            __ImplementsCache.pop((class_, interface, True), None)
            __ImplementedInterfacesCache.pop(class_, None)

            AssertImplements(class_, interface, requires_declaration=False)
    except:
        # Roll back...
        class_.__implements__ = old_implements
        raise


def _GetMROForOldStyleClass(class_: Type) -> List[Type]:
    """
    :type class_: classobj
    :param class_:
        An old-style class

    :rtype: list(classobj)
    :return:
        A list with all the bases in the older MRO (method resolution order)
    """

    def _CalculateMro(class_: Any, mro: Any) -> Any:
        for base in class_.__bases__:
            if base not in mro:
                mro.append(base)
                _CalculateMro(base, mro)

    mro = [class_]
    _CalculateMro(class_, mro)
    return mro


def _GetClassImplementedInterfaces(class_: Type) -> FrozenSet[Type[Interface]]:
    with suppress(KeyError):
        return __ImplementedInterfacesCache[class_]

    implemented_interfaces = set()

    mro = inspect.getmro(class_)

    for c in mro:
        interfaces = getattr(c, "__implements__", ())
        for interface in interfaces:
            interface_mro = inspect.getmro(interface)

            for interface_type in interface_mro:
                if interface_type in (Interface, object):
                    continue
                implemented_interfaces.add(interface_type)

    result = frozenset(implemented_interfaces)
    __ImplementedInterfacesCache[class_] = result
    return result


def GetImplementedInterfaces(class_or_object: Any) -> FrozenSet[Type[Interface]]:
    """
    Return the interfaces implemented by the object or class passed.
    """
    class_ = _GetClassForInterfaceChecking(class_or_object)

    # we have to build the cache attribute given the name of the class, otherwise setting in a base
    # class before a subclass may give errors.
    return _GetClassImplementedInterfaces(class_)


@Deprecated(AssertImplements)
def AssertDeclaresInterface(
    class_or_instance: object, interface: Type[Interface]
) -> None:
    AssertImplements(class_or_instance, interface)
