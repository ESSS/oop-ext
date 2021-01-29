from copy import copy, deepcopy

import pytest

from oop_ext.foundation.immutable import AsImmutable, IdentityHashableRef, ImmutableDict


def testImmutable() -> None:
    class MyClass:
        pass

    d = AsImmutable(dict(a=1, b=dict(b=2)))
    assert d == {"a": 1, "b": {"b": 2}}
    with pytest.raises(NotImplementedError):
        d.__setitem__("a", 2)

    assert d["b"].AsMutable() == dict(b=2)
    AsImmutable(d, return_str_if_not_expected=False)
    d = d.AsMutable()
    d["a"] = 2

    c = deepcopy(d)
    assert c == d

    c = copy(d)
    assert c == d
    assert AsImmutable({1, 2, 3}) == {1, 2, 3}
    assert AsImmutable(([1, 2], [2, 3])) == ((1, 2), (2, 3))
    assert AsImmutable(None) is None
    assert isinstance(AsImmutable({1, 2, 4}), frozenset)
    assert isinstance(AsImmutable(frozenset([1, 2, 4])), frozenset)
    assert isinstance(AsImmutable([1, 2, 4]), tuple)
    assert isinstance(AsImmutable((1, 2, 4)), tuple)

    # Primitive non-container types
    def AssertIsSame(value):
        assert AsImmutable(value) is value

    AssertIsSame(True)
    AssertIsSame(1.0)
    AssertIsSame(1)
    AssertIsSame("a")  # native string
    AssertIsSame(b"b")  # native bytes
    AssertIsSame(str("a"))  # future's str compatibility type
    AssertIsSame(bytes(b"b"))  # future's byte compatibility type

    # Dealing with derived values
    a = MyClass()
    assert AsImmutable(a, return_str_if_not_expected=True) == str(a)
    with pytest.raises(RuntimeError):
        AsImmutable(a, return_str_if_not_expected=False)

    # Derived basics
    class MyStr(str):
        pass

    assert AsImmutable(MyStr("alpha")) == "alpha"

    class MyList(list):
        pass

    assert AsImmutable(MyList()) == ()

    class MySet(set):
        pass

    assert AsImmutable(MySet()) == frozenset()


def testImmutableDict() -> None:
    d = ImmutableDict(alpha=1, bravo=2)

    with pytest.raises(NotImplementedError):
        d["charlie"] = 3

    with pytest.raises(NotImplementedError):
        del d["alpha"]

    with pytest.raises(NotImplementedError):
        d.clear()

    with pytest.raises(NotImplementedError):
        d.setdefault("charlie", 3)

    with pytest.raises(NotImplementedError):
        d.popitem()

    with pytest.raises(NotImplementedError):
        d.update({"charlie": 3})


def testIdentityHashableRef() -> None:
    a = {1: 2}
    b = {1: 2}

    assert IdentityHashableRef(a)() is a
    assert a == b
    assert IdentityHashableRef(a) != IdentityHashableRef(b)
    assert IdentityHashableRef(a) == IdentityHashableRef(a)

    set_a = {IdentityHashableRef(a)}
    assert IdentityHashableRef(a) in set_a
    assert IdentityHashableRef(b) not in set_a

    dict_b = {IdentityHashableRef(b): 7}
    assert IdentityHashableRef(a) not in dict_b
    assert IdentityHashableRef(b) in dict_b
    assert dict_b[IdentityHashableRef(b)] == 7
