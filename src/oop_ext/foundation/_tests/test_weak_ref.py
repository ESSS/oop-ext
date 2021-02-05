import sys
import weakref
from typing import Any

import pytest

from oop_ext.foundation.weak_ref import (
    GetRealObj,
    GetWeakProxy,
    GetWeakRef,
    IsSame,
    IsWeakProxy,
    IsWeakRef,
    WeakList,
    WeakMethodProxy,
    WeakMethodRef,
    WeakSet,
)


class _Stub:
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return True  # always equal

    def __ne__(self, o):
        return not self == o

    def Method(self):
        pass


class Obj:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


def testStub() -> None:
    a = _Stub()
    b = _Stub()
    assert not a != a
    assert not a != b
    assert a == a
    assert a == b
    a.Method()


def testIsSame() -> None:
    s1 = _Stub()
    s2 = _Stub()

    r1 = weakref.ref(s1)
    r2 = weakref.ref(s2)

    p1 = weakref.proxy(s1)
    p2 = weakref.proxy(s2)

    assert IsSame(s1, s1)
    assert not IsSame(s1, s2)

    assert IsSame(s1, r1)
    assert IsSame(s1, p1)

    assert not IsSame(s1, r2)
    assert not IsSame(s1, p2)

    assert IsSame(p2, r2)
    assert IsSame(r1, p1)
    assert not IsSame(r1, p2)

    with pytest.raises(ReferenceError):
        IsSame(p1, p2)


def testGetWeakRef() -> None:
    b = GetWeakRef(None)
    assert callable(b)
    assert b() is None


def testGeneral() -> None:
    b = _Stub()
    r = GetWeakRef(b.Method)
    assert callable(r)
    assert (
        r() is not None
    )  # should not be a regular weak ref here (but a weak method ref)

    assert IsWeakRef(r)
    assert not IsWeakProxy(r)

    r = GetWeakProxy(b.Method)
    assert callable(r)
    r()
    assert IsWeakProxy(r)
    assert not IsWeakRef(r)

    r = weakref.ref(b)
    b2 = _Stub()
    r2 = weakref.ref(b2)
    assert r == r2
    assert hash(r) == hash(r2)

    r_m1 = GetWeakRef(b.Method)
    r_m2 = GetWeakRef(b.Method)
    assert r_m1 == r_m2
    assert hash(r_m1) == hash(r_m2)


def testGetRealObj() -> None:
    b = _Stub()
    r = GetWeakRef(b)
    assert GetRealObj(r) is b

    r = GetWeakRef(None)
    assert GetRealObj(r) is None


def testGetWeakProxyFromWeakRef() -> None:
    b = _Stub()
    r = GetWeakRef(b)
    proxy = GetWeakProxy(r)
    assert IsWeakProxy(proxy)


def testWeakSet() -> None:
    weak_set = WeakSet[Any]()
    s1 = _Stub()
    s2 = _Stub()

    weak_set.add(s1)
    assert isinstance(next(iter(weak_set)), _Stub)

    assert s1 in weak_set
    CustomAssertEqual(len(weak_set), 1)
    del s1
    CustomAssertEqual(len(weak_set), 0)

    weak_set.add(s2)
    CustomAssertEqual(len(weak_set), 1)
    weak_set.remove(s2)
    CustomAssertEqual(len(weak_set), 0)

    weak_set.add(s2)
    weak_set.clear()
    CustomAssertEqual(len(weak_set), 0)

    weak_set.add(s2)
    weak_set.add(s2)
    weak_set.add(s2)
    CustomAssertEqual(len(weak_set), 1)
    del s2
    CustomAssertEqual(len(weak_set), 0)

    # >>> Testing with FUNCTION

    # Adding twice, having one
    def function() -> None:
        pass

    weak_set.add(function)
    weak_set.add(function)
    CustomAssertEqual(len(weak_set), 1)


def testRemove() -> None:
    weak_set = WeakSet[_Stub]()

    s1 = _Stub()

    CustomAssertEqual(len(weak_set), 0)

    # Trying remove, raises KeyError
    with pytest.raises(KeyError):
        weak_set.remove(s1)
    CustomAssertEqual(len(weak_set), 0)

    # Trying discard, no exception raised
    weak_set.discard(s1)
    CustomAssertEqual(len(weak_set), 0)


def testWeakSet2() -> None:
    weak_set = WeakSet[Any]()

    # >>> Removing with DEL
    s1 = _Stub()
    weak_set.add(s1.Method)
    CustomAssertEqual(len(weak_set), 1)
    del s1
    CustomAssertEqual(len(weak_set), 0)

    # >>> Removing with REMOVE
    s2 = _Stub()
    weak_set.add(s2.Method)
    CustomAssertEqual(len(weak_set), 1)
    weak_set.remove(s2.Method)
    CustomAssertEqual(len(weak_set), 0)


def testWeakSetUnionWithWeakSet() -> None:
    ws1, ws2 = WeakSet[Obj](), WeakSet[Obj]()
    a, b, c = Obj("a"), Obj("b"), Obj("c")

    ws1.add(a)
    ws1.add(b)

    ws2.add(a)
    ws2.add(c)

    ws3 = ws1.union(ws2)
    assert set(ws3) == set(ws2.union(ws1)) == {a, b, c}

    del c
    assert set(ws3) == set(ws2.union(ws1)) == {a, b}


def testWeakSetUnionWithSet() -> None:
    ws = WeakSet[Obj]()
    a, b, c = Obj("a"), Obj("b"), Obj("c")

    ws.add(a)
    ws.add(b)

    s = {a, c}

    ws3 = ws.union(s)
    assert set(ws3) == set(s.union(set(ws))) == {a, b, c}

    del b
    assert set(ws3) == set(s.union(set(ws))) == {a, c}


def testWeakSetSubWithWeakSet() -> None:
    ws1, ws2 = WeakSet[Obj](), WeakSet[Obj]()
    a, b, c = Obj("a"), Obj("b"), Obj("c")

    ws1.add(a)
    ws1.add(b)

    ws2.add(a)
    ws2.add(c)
    assert set(ws1 - ws2) == {b}
    assert set(ws2 - ws1) == {c}

    del c
    assert set(ws1 - ws2) == {b}
    assert set(ws2 - ws1) == set()


def testWeakSetSubWithSet() -> None:
    ws = WeakSet[Obj]()
    s = set()
    a, b, c = Obj("a"), Obj("b"), Obj("c")

    ws.add(a)
    ws.add(b)

    s.add(a)
    s.add(c)

    assert set(ws - s) == {b}
    assert s - ws == {c}

    del b
    assert set(ws - s) == set()
    assert s - ws == {c}


def testWithError() -> None:
    weak_set = WeakSet[Any]()

    # Not WITH, everything ok
    s1 = _Stub()
    weak_set.add(s1.Method)
    CustomAssertEqual(len(weak_set), 1)
    del s1
    CustomAssertEqual(len(weak_set), 0)

    # Using WITH, s2 is not deleted from weak_set
    s2 = _Stub()
    with pytest.raises(KeyError):
        raise KeyError("key")
    CustomAssertEqual(len(weak_set), 0)

    weak_set.add(s2.Method)
    CustomAssertEqual(len(weak_set), 1)
    del s2
    CustomAssertEqual(len(weak_set), 0)


def testFunction() -> None:
    weak_set = WeakSet[Any]()

    def function() -> None:
        "Never called"

    # Adding twice, having one.
    weak_set.add(function)
    weak_set.add(function)
    CustomAssertEqual(len(weak_set), 1)

    # Removing function
    weak_set.remove(function)
    assert len(weak_set) == 0


def CustomAssertEqual(a, b):
    """
    Avoiding using "assert a == b" because it adds another reference to the ref-count.
    """
    if a == b:
        pass
    else:
        assert False, "{} != {}".format(a, b)


def SetupTestAttributes():
    class C:
        x: int

        def f(self, y=0):
            return self.x + y

    class D:
        def f(self):
            "Never called"

    c = C()
    c.x = 1
    d = D()

    return (C, c, d)


def testCustomAssertEqual() -> None:
    with pytest.raises(AssertionError) as excinfo:
        CustomAssertEqual(1, 2)

    assert str(excinfo.value) == "1 != 2\nassert False"


def testRefcount() -> None:
    _, c, _ = SetupTestAttributes()

    CustomAssertEqual(
        sys.getrefcount(c), 2
    )  # 2: one in self, and one as argument to getrefcount()
    cf = c.f
    CustomAssertEqual(sys.getrefcount(c), 3)  # 3: as above, plus cf
    rf = WeakMethodRef(c.f)
    pf = WeakMethodProxy(c.f)
    CustomAssertEqual(sys.getrefcount(c), 3)
    del cf
    CustomAssertEqual(sys.getrefcount(c), 2)
    rf2 = WeakMethodRef(c.f)
    CustomAssertEqual(sys.getrefcount(c), 2)
    del rf
    del rf2
    del pf
    CustomAssertEqual(sys.getrefcount(c), 2)


def testDies() -> None:
    _, c, _ = SetupTestAttributes()

    rf = WeakMethodRef(c.f)
    pf = WeakMethodProxy(c.f)
    assert not rf.is_dead()
    assert not pf.is_dead()
    assert rf()() == 1
    assert pf(2) == 3
    c = None
    assert rf.is_dead()
    assert pf.is_dead()
    assert rf() == None
    with pytest.raises(ReferenceError):
        pf()


def testWorksWithFunctions() -> None:
    SetupTestAttributes()

    def foo(y):
        return y + 1

    rf = WeakMethodRef(foo)
    pf = WeakMethodProxy(foo)
    assert foo(1) == 2
    assert rf()(1) == 2
    assert pf(1) == 2
    assert not rf.is_dead()
    assert not pf.is_dead()


def testWorksWithUnboundMethods() -> None:
    C, c, _ = SetupTestAttributes()

    meth = C.f
    rf = WeakMethodRef(meth)
    pf = WeakMethodProxy(meth)
    assert meth(c) == 1
    assert rf()(c) == 1
    assert pf(c) == 1
    assert not rf.is_dead()
    assert not pf.is_dead()


def testEq() -> None:
    _, c, d = SetupTestAttributes()

    rf1 = WeakMethodRef(c.f)
    rf2 = WeakMethodRef(c.f)
    assert rf1 == rf2
    rf3 = WeakMethodRef(d.f)
    assert rf1 != rf3
    del c
    assert rf1.is_dead()
    assert rf2.is_dead()
    assert rf1 == rf2


def testProxyEq() -> None:
    _, c, d = SetupTestAttributes()

    pf1 = WeakMethodProxy(c.f)
    pf2 = WeakMethodProxy(c.f)
    pf3 = WeakMethodProxy(d.f)
    assert pf1 == pf2
    assert pf3 != pf2
    del c
    assert pf1 == pf2
    assert pf1.is_dead()
    assert pf2.is_dead()


def testHash() -> None:
    _, c, _ = SetupTestAttributes()

    r = WeakMethodRef(c.f)
    r2 = WeakMethodRef(c.f)
    assert r == r2
    h = hash(r)
    assert hash(r) == hash(r2)
    del c
    assert r() is None
    assert hash(r) == h


def testRepr() -> None:
    _, c, _ = SetupTestAttributes()

    r = WeakMethodRef(c.f)
    assert str(r)[:33] == "<WeakMethodRef to C.f for object "

    def Foo() -> None:
        "Never called"

    r = WeakMethodRef(Foo)
    assert str(r) == "<WeakMethodRef to Foo>"


def testWeakRefToWeakMethodRef() -> None:
    def Foo() -> None:
        "Never called"

    r = WeakMethodRef(Foo)
    m_ref = weakref.ref(r)
    assert m_ref() is r


def testWeakList() -> None:
    weak_list = WeakList[_Stub]()
    s1 = _Stub()
    s2 = _Stub()

    weak_list.append(s1)
    assert isinstance(weak_list[0], _Stub)

    assert s1 in weak_list
    assert 1 == len(weak_list)
    del s1
    assert 0 == len(weak_list)

    weak_list.append(s2)
    assert 1 == len(weak_list)
    weak_list.remove(s2)
    assert 0 == len(weak_list)

    weak_list.append(s2)
    del weak_list[:]
    assert 0 == len(weak_list)

    weak_list.append(s2)
    del s2
    del weak_list[:]
    assert 0 == len(weak_list)

    s1 = _Stub()
    weak_list.append(s1)
    assert 1 == len(weak_list[:])

    del s1

    assert 0 == len(weak_list[:])

    def m1() -> None:
        "Never called"

    weak_list.append(m1)  # type:ignore[arg-type]
    assert 1 == len(weak_list[:])
    del m1
    assert 0 == len(weak_list[:])

    s = _Stub()
    weak_list.append(s.Method)  # type:ignore[arg-type]
    assert 1 == len(weak_list[:])
    ref_s = weakref.ref(s)
    del s
    assert 0 == len(weak_list[:])
    assert ref_s() is None

    s0 = _Stub()
    s1 = _Stub()
    weak_list.extend([s0, s1])
    assert len(weak_list) == 2


def testSetItem() -> None:
    weak_list = WeakList[_Stub]()
    s1 = _Stub()
    s2 = _Stub()
    weak_list.append(s1)
    weak_list.append(s1)
    assert s1 == weak_list[0]
    weak_list[0] = s2
    assert s2 == weak_list[0]
