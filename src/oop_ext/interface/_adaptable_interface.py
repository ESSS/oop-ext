from ._interface import TypeCheckingSupport
from ._interface import Interface


class IAdaptable(Interface, TypeCheckingSupport):
    """
    An interface for an object that is adaptable.

    Adaptable objects can be queried about interfaces they adapt to (to which they
    may respond or not).

    For example:

    a = [some IAdaptable];
    x = a.GetAdapter(IFoo);
    if x is not None:
        [do IFoo things with x]
    """

    def GetAdapter(self, interface_class):
        """
        :type interface_class: this is the interface for which an adaptation is required
        :param interface_class:
        :rtype: an object implementing the required interface or None if this object cannot
        adapt to that interface.

        Note: explicitly not adding type hints here as this would break every implementation, as
            Interface also checks type hints.
        """
