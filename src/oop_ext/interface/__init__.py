"""
    Interfaces module.

    A Interface describes a behaviour that some objects must implement.

    To declare a interface, just subclass from Interface::

        class IFoo(interface.Interface):
            ...

    To create a class that implements that interface, use interface.Implements:

        class Foo(object):
            interface.Implements(IFoo)

    If Foo doesn't implement some method from IFoo, an exception is raised at class creation time.
"""

from ._adaptable_interface import IAdaptable
from ._interface import AssertDeclaresInterface
from ._interface import AssertImplements
from ._interface import AssertImplementsFullChecking
from ._interface import Attribute
from ._interface import BadImplementationError
from ._interface import CacheInterfaceAttrs
from ._interface import DeclareClassImplements
from ._interface import GetImplementedInterfaces
from ._interface import GetProxy
from ._interface import ImplementsInterface
from ._interface import Interface
from ._interface import InterfaceError
from ._interface import InterfaceImplementationMetaClass
from ._interface import InterfaceImplementorStub
from ._interface import IsImplementation
from ._interface import IsImplementationOfAny
from ._interface import ReadOnlyAttribute
from ._interface import TypeCheckingSupport

__all__ = [
    "AssertDeclaresInterface",
    "AssertImplements",
    "AssertImplementsFullChecking",
    "Attribute",
    "BadImplementationError",
    "CacheInterfaceAttrs",
    "DeclareClassImplements",
    "GetImplementedInterfaces",
    "GetProxy",
    "IAdaptable",
    "ImplementsInterface",
    "Interface",
    "InterfaceError",
    "InterfaceImplementationMetaClass",
    "InterfaceImplementorStub",
    "IsImplementation",
    "IsImplementationOfAny",
    "ReadOnlyAttribute",
    "TypeCheckingSupport",
]
