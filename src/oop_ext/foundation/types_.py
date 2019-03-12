"""
Extensions to python native types.
"""

# ===================================================================================================
# Method
# ===================================================================================================
class Method:
    """
    This class is an 'organization' class, so that subclasses are considered as methods
    (and its __call__ method is checked for the parameters)
    """


# ===================================================================================================
# Null
# ===================================================================================================
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

    def __init__(self, *_args, **_kwargs):
        "Ignore parameters."
        # Setting the name of what's gotten (so that __name__ is properly preserved).
        self.__dict__["_Null__name__"] = "Null"
        return None

    def __call__(self, *_args, **_kwargs):
        "Ignore method calls."
        return self

    def __getattr__(self, mname):
        "Ignore attribute requests."
        if mname == "__getnewargs__":
            raise AttributeError(
                "No support for that (pickle causes error if it returns self in this case.)"
            )

        if mname == "__name__":
            return self.__dict__["_Null__name__"]

        return self

    def __setattr__(self, _name, _value):
        "Ignore attribute setting."
        return self

    def __delattr__(self, _name):
        "Ignore deleting attributes."
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return self

    def __repr__(self):
        "Return a string representation."
        return "<Null>"

    def __str__(self):
        "Convert to a string and return it."
        return "Null"

    def __bool__(self):
        "Null objects are always false"
        return False

    def __nonzero__(self):
        # Py 2 compatibility
        return self.__bool__()

    # iter

    def __iter__(self):
        "I will stop it in the first iteration"
        return self

    def __next__(self):
        "Stop the iteration right now"
        raise StopIteration()

    def next(self):
        # Py 2 compatibility
        return self.__next__()

    def __eq__(self, o):
        "It is just equal to another Null object."
        return self.__class__ == o.__class__


NULL = Null()  # Create a default instance to be used.
