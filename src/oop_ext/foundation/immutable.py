# mypy: disallow-untyped-defs
"""
    Defines types and functions to generate immutable structures.

    USER: The cache-manager uses this module to generate a valid KEY for its cache dictionary.
"""
from typing import Type, Any, Dict, Tuple, Callable, TypeVar, Generic, NoReturn

_IMMUTABLE_TYPES = {float, int, str, bytes, bool, type(None)}


def RegisterAsImmutable(immutable_type: Type[object]) -> None:
    """
    Registers the given class as being immutable. This makes it be immutable for this module and
    also registers a faster copy in the copy module (to return the same instance being copied).

    :param type immutable_type:
        The type to be considered immutable.
    """
    _IMMUTABLE_TYPES.add(immutable_type)

    # Fix it for the copy too!
    import copy

    copy._copy_dispatch[  # type:ignore[attr-defined]
        immutable_type
    ] = copy._copy_immutable  # type:ignore[attr-defined]


def AsImmutable(value: Any, return_str_if_not_expected: bool = True) -> Any:
    """
    Returns the given instance as a immutable object:
        - Converts lists to tuples
        - Converts dicts to ImmutableDicts
        - Converts other objects to str
        - Does not convert basic types (int/float/str/bool)

    :param object value:
        The value to be returned as an immutable value

    :param bool return_str_if_not_expected:
        If True, a string representation of the object will be returned if we're unable to match the
        type as a known type (otherwise, an error is thrown if we cannot handle the passed type).

    :rtype: object
    :returns:
        Returns an immutable representation of the passed object
    """

    # Micro-optimization (a 40% improvement on the AsImmutable function overall in a real case
    # using sci20 processes).
    # Checking the type of the class before going to the isinstance series and added
    # SemanticAssociation as an immutable object.
    value_class = value.__class__

    if value_class in _IMMUTABLE_TYPES:
        return value

    if value_class == dict:
        return ImmutableDict((i, AsImmutable(j)) for i, j in value.items())

    if value_class in (tuple, list):
        return tuple(AsImmutable(i) for i in value)

    if value_class in (set, frozenset):
        return frozenset(value)

    # Now, on to the isinstance series...
    if isinstance(value, int):
        return value

    if isinstance(value, (float, str, bytes, bool)):
        return value

    if isinstance(value, dict):
        return ImmutableDict((i, AsImmutable(j)) for i, j in value.items())

    if isinstance(value, (tuple, list)):
        return tuple(AsImmutable(i) for i in value)

    if isinstance(value, (set, frozenset)):
        return frozenset(value)

    if return_str_if_not_expected:
        return str(value)

    else:
        raise RuntimeError("Cannot make %s immutable (not supported)." % value)


class ImmutableDict(dict):
    """A hashable dict."""

    def __deepcopy__(self, memo: Any) -> "ImmutableDict":
        return self  # it's immutable, so, there's no real need to make any copy

    def __setitem__(self, key: object, value: object) -> NoReturn:
        raise NotImplementedError("dict is immutable")

    def __delitem__(self, key: object) -> NoReturn:
        raise NotImplementedError("dict is immutable")

    def clear(self) -> NoReturn:
        raise NotImplementedError("dict is immutable")

    def setdefault(self, k: Any, default: Any = None) -> NoReturn:
        raise NotImplementedError("dict is immutable")

    def popitem(self) -> NoReturn:
        raise NotImplementedError("dict is immutable")

    def update(self, *args: object) -> NoReturn:  # type:ignore[override]
        raise NotImplementedError("dict is immutable")

    def __hash__(self) -> int:  # type:ignore[override]
        if not hasattr(self, "_hash"):
            # must be sorted (could give different results for dicts that should be the same
            # if it's not).
            self._hash = hash(tuple(sorted(self.items())))

        return self._hash

    def AsMutable(self) -> Dict:
        """
        :rtype: this dict as a new dict that can be changed (without altering the state
        of this immutable dict).
        """
        return dict(self.items())

    def __reduce__(self) -> Tuple[Callable, Tuple[object]]:
        """
        Making ImmutableDict work with newer versions of pickle protocol.

        Without this, it uses the default behavior on loading which tries to create an empty dict
        and then set its items, which is not an allowed operation on ImmutableDict.

        In general, there are higher level functions to be redefined for pickle customization, but
        for dict subclasses we need to define __reduce__ method. For more details of this special
        case, see __reduce__ in the referenced docs (links below).

        See also:
        - https://docs.python.org/2/library/pickle.html#pickling-and-unpickling-extension-types
        - https://docs.python.org/3/library/pickle.html#pickling-class-instances

        :return tuple:
            (Callable, tuple of arguments). See __reduce__ docs for more details.
        """
        return (ImmutableDict, (list(self.items()),))


T = TypeVar("T")


class IdentityHashableRef(Generic[T]):
    """
    Represents a immutable reference to an object.

    Useful when is desired to use some mutable object as key in a dict or element in a set.
    Any form of overwriting the `__hash__`, `__eq__`, or `__ne__` in the original object is ignored
    when taking the hash or comparing the reference (for they to be equal they must point to the
    same object and if equal they will have the same hash).

    Usage:

    ```
    foo = NonHashableWithFancyEquality()
    ref_to_foo = IdentityHashableRef(foo)

    ref_to_foo() is foo  # True

    aset = set()
    aset.add(IdentityHashableRef(foo))
    IdentityHashableRef(foo) in aset  # True

    adict = dict()
    adict[IdentityHashableRef(foo)] = 7
    IdentityHashableRef(foo) in adict  # True
    ```
    """

    _SENTINEL = object()

    def __init__(self, original: T):
        self._original = original

    def __eq__(self, other: object) -> bool:
        return self._original is getattr(other, "_original", self._SENTINEL)

    def __ne__(self, other: object) -> bool:
        return self._original is not getattr(other, "_original", self._SENTINEL)

    def __hash__(self) -> int:
        return id(self._original)

    def __call__(self) -> T:
        return self._original


RegisterAsImmutable(IdentityHashableRef)
