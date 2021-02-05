import copy

from oop_ext.foundation.types_ import Null


def testNull() -> None:
    # constructing and calling

    dummy = Null()
    dummy = Null("value")
    n = Null("value", param="value")

    n()
    n("value")
    n("value", param="value")

    # attribute handling
    n.attr1
    n.attr1.attr2
    n.method1()
    n.method1().method2()
    n.method("value")
    n.method(param="value")
    n.method("value", param="value")
    n.attr1.method1()
    n.method1().attr1

    n.attr1 = "value"
    n.attr1.attr2 = "value"  # type:ignore[attr-defined]

    del n.attr1
    del n.attr1.attr2.attr3  # type:ignore[attr-defined]

    # Iteration
    for _ in n:
        "Not executed"

    # representation and conversion to a string
    assert repr(n) == "<Null>"
    assert str(n) == "Null"

    # truth value
    assert bool(n) == False
    assert bool(n.foo()) == False

    dummy = Null()
    # context manager
    with dummy:
        assert dummy.__name__ == "Null"  # Name should return a str

    # Null objects are always equal to other null object
    assert n != 1
    assert n == dummy

    assert hash(Null()) == hash(Null())


def testNullCopy() -> None:
    n = Null()
    n1 = copy.copy(n)
    assert str(n) == str(n1)
