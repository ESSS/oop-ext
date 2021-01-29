# mypy: disallow-untyped-defs
"""
A compatibility module for quirks when porting from py2->py3.
"""
from typing import Any


def GetClassForUnboundMethod(method: Any) -> Any:
    """
    On Python 3 there are no unbound methods anymore. They are only regular functions.

    This function abstracts that difference and implements a workaround for Python 3.

    However this has a drawback: callback to method of local classes AREN'T SUPPORTED anymore,
    as it is impossible to retrieve their class object just by method object alone.
    """
    locals_name = "<locals>"

    # Find the class which this method belongs too. We need this because on Python 3, unbound
    # methods are just regular functions with no reference to its class
    names = method.__qualname__.split(".")
    names.pop()
    method_class = method.__globals__[names.pop(0)]
    while names:
        name = names.pop(0)
        if name == locals_name:
            raise NotImplementedError(
                "Impossible to retrieve class object for "
                "unbound methods in local classes."
            )

        method_class = getattr(method_class, name)
    return method_class
