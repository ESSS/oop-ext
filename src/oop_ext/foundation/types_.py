# mypy: disallow-untyped-defs
"""
Extensions to python native types.
"""
from typing import TYPE_CHECKING, Any, NoReturn, Iterator

if TYPE_CHECKING:
    from typing_extensions import Literal


class Method:
    """
    This class is an 'organization' class, so that subclasses are considered as methods
    (and its __call__ method is checked for the parameters)
    """

    __self__: object
    __name__: str


class Null:
    """
    This is a sample implementation of the 'Null Object' design pattern.

    Roughly, the goal with Null objects is to provide an 'intelligent'
    replacement for the often used primitive data type None in Python or
    Null (or Null pointers) in other languages. These are used for many
    purposes including the important case where one member of some group
    of otherwise similar elements is special for whatever reason. Most
    often this results in conditional statements to distinguish between
    ordinary elements and the primitive Null value.

    Among the advantages of using Null objects are the following:

      - Superfluous conditional statements can be avoided
        by providing a first class object alternative for
        the primitive value None.

      - Code readability is improved.

      - Null objects can act as a placeholder for objects
        with behaviour that is not yet implemented.

      - Null objects can be replaced for any other class.

      - Null objects are very predictable at what they do.

    To cope with the disadvantage of creating large numbers of passive
    objects that do nothing but occupy memory space Null objects are
    often combined with the Singleton pattern.

    For more information use any internet search engine and look for
    combinations of these words: Null, object, design and pattern.

    Dinu C. Gherman,
    August 2001

    ---

    A class for implementing Null objects.

    This class ignores all parameters passed when constructing or
    calling instances and traps all attribute and method requests.
    Instances of it always (and reliably) do 'nothing'.

    The code might benefit from implementing some further special
    Python methods depending on the context in which its instances
    are used. Especially when comparing and coercing Null objects
    the respective methods' implementation will depend very much
    on the environment and, hence, these special methods are not
    provided here.
    """

    # object constructing

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        "Ignore parameters."
        # Setting the name of what's gotten (so that __name__ is properly preserved).
        self.__dict__["_Null__name__"] = "Null"

    def __call__(self, *_args: object, **_kwargs: object) -> "Null":
        "Ignore method calls."
        return self

    def __getattr__(self, mname: str) -> Any:
        "Ignore attribute requests."
        if mname == "__getnewargs__":
            raise AttributeError(
                "No support for that (pickle causes error if it returns self in this case.)"
            )

        if mname == "__name__":
            return self.__dict__["_Null__name__"]

        return self

    def __setattr__(self, _name: str, _value: object) -> Any:
        "Ignore attribute setting."
        return self

    def __delattr__(self, _name: str) -> None:
        "Ignore deleting attributes."

    def __enter__(self) -> "Null":
        return self

    def __exit__(self, *args: object, **kwargs: object) -> None:
        pass

    def __repr__(self) -> str:
        "Return a string representation."
        return "<Null>"

    def __str__(self) -> str:
        "Convert to a string and return it."
        return "Null"

    def __bool__(self) -> "Literal[False]":
        "Null objects are always false"
        return False

    # iter

    def __iter__(self) -> Iterator["Null"]:
        "I will stop it in the first iteration"
        return iter([self])

    def __next__(self) -> NoReturn:
        "Stop the iteration right now"
        raise StopIteration()

    def __eq__(self, o: Any) -> Any:
        "It is just equal to another Null object."
        return self.__class__ == o.__class__

    def __hash__(self) -> int:
        """Null is hashable"""
        return 0


NULL = Null()  # Create a default instance to be used.
