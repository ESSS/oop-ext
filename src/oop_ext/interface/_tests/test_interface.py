
import textwrap

import pytest

from oop_ext.foundation.types_ import Method, Null
from oop_ext.interface import (
    AssertImplements,
    Attribute,
    BadImplementationError,
    DeclareClassImplements,
    GetImplementedInterfaces,
    IAdaptable,
    ImplementsInterface,
    Interface,
    InterfaceError,
    InterfaceImplementorStub,
    IsImplementation,
    ReadOnlyAttribute,
)


# ===================================================================================================
# _InterfM1
# ===================================================================================================
class _InterfM1(Interface):
    def m1(self):
        ""


# ===================================================================================================
# _InterfM2
# ===================================================================================================
class _InterfM2(Interface):
    def m2(self):
        ""


# ===================================================================================================
# _InterfM3
# ===================================================================================================
class _InterfM3(Interface):
    def m3(self, arg1, arg2):
        ""


# ===================================================================================================
# _InterfM4
# ===================================================================================================
class _InterfM4(_InterfM3):
    def m4(self):
        ""


def testBasics():
    class I(Interface):
        def foo(self, a, b=None):
            ""

        def bar(self):
            ""

    @ImplementsInterface(I)
    class C:
        def foo(self, a, b=None):
            ""

        def bar(self):
            ""

    class C2:
        def foo(self, a, b=None):
            ""

        def bar(self):
            ""

    class D:
        ""

    assert IsImplementation(I(C()), I) == True  # OK

    assert IsImplementation(C, I) == True  # OK
    assert IsImplementation(C2, I) == False  # Does not declare
    assert not IsImplementation(D, I) == True  # nope

    assert I(C) is C
    assert I(C2) is C2
    with pytest.raises(InterfaceError):
        I()

    with pytest.raises(BadImplementationError):
        I(D)

    # Now declare that C2 implements I
    DeclareClassImplements(C2, I)

    assert IsImplementation(C2, I) == True  # Does not declare


def testMissingMethod():
    class I(Interface):
        def foo(self, a, b=None):
            ""

    with pytest.raises(
        AssertionError,
        match=r"Method 'foo' is missing in class 'C' \(required by interface 'I'\)",
    ):

        @ImplementsInterface(I)
        class C:
            pass

    def TestMissingSignature():
        @ImplementsInterface(I)
        class C:
            def foo(self, a):
                ""

    with pytest.raises(AssertionError) as e:
        TestMissingSignature()
    assert str(e.value) == textwrap.dedent(
        """
        Method C.foo signature:
          (self, a)
        differs from defined in interface I
          (self, a, b=None)"""
    )

    def TestMissingSignatureOptional():
        @ImplementsInterface(I)
        class C:
            def foo(self, a, b):
                ""

    with pytest.raises(AssertionError) as e:
        TestMissingSignatureOptional()
    assert str(e.value) == textwrap.dedent(
        """
        Method C.foo signature:
          (self, a, b)
        differs from defined in interface I
          (self, a, b=None)"""
    )

    def TestWrongParameterName():
        @ImplementsInterface(I)
        class C:
            def foo(self, a, c):
                ""

    with pytest.raises(AssertionError) as e:
        TestWrongParameterName()
    assert str(e.value) == textwrap.dedent(
        """
        Method C.foo signature:
          (self, a, c)
        differs from defined in interface I
          (self, a, b=None)"""
    )


def testSubclasses():
    class I(Interface):
        def foo(self, a, b=None):
            ""

    @ImplementsInterface(I)
    class C:
        def foo(self, a, b=None):
            ""

    class D(C):
        ""


def testSubclasses2():
    class I(Interface):
        def foo(self):
            ""

    class I2(Interface):
        def bar(self):
            ""

    @ImplementsInterface(I)
    class C:
        def foo(self):
            ""

    @ImplementsInterface(I2)
    class D(C):
        def bar(self):
            ""

    class E(D):
        ""

    assert GetImplementedInterfaces(C) == {I}
    assert GetImplementedInterfaces(D) == {I2, I}
    assert GetImplementedInterfaces(E) == {I2, I}


def testNoName():
    class I(Interface):
        def MyMethod(self, foo):
            ""

    class C:
        def MyMethod(self, bar):
            ""

    with pytest.raises(AssertionError):
        AssertImplements(C(), I)


def testAttributes():
    class IZoo(Interface):
        zoo = Attribute(int)

    class I(Interface):
        foo = Attribute(int)
        bar = Attribute(str)
        foobar = Attribute(int, None)
        a_zoo = Attribute(IZoo)

    @ImplementsInterface(IZoo)
    class Zoo:
        pass

    # NOTE: This class 'C' doesn't REALLY implements 'I', although it says so. The problem is
    #       that there's a flaw with attributes *not being checked*.

    # In fact: Attributes should not be in the  (Abstract) properties COULD be in
    #          the interface, but they SHOULD NOT be type-checked (because it involves a
    #          getter call, and this affects runtime behaviour).
    #          This should be reviewed later.
    @ImplementsInterface(I)
    class C:
        pass

    c1 = C()
    c1.foo = 10
    c1.bar = "hello"
    c1.foobar = 20

    a_zoo = Zoo()
    a_zoo.zoo = 99
    c1.a_zoo = a_zoo

    c2 = C()

    assert IsImplementation(C, I) == True
    assert IsImplementation(c1, I) == True
    assert IsImplementation(c2, I) == True

    # NOTE: Testing private methods here
    # If we do a deprecated "full check", then its behaviour is a little bit more correct.
    from oop_ext.interface._interface import _IsImplementationFullChecking

    assert not _IsImplementationFullChecking(C, I) == True  # only works with instances
    assert _IsImplementationFullChecking(c1, I) == True  # OK, has attributes
    assert (
        not _IsImplementationFullChecking(c2, I) == True
    )  # not all the attributes necessary

    # must not be true if including an object that doesn't implement IZoo interface expected for
    # a_zoo attribute
    c1.a_zoo = "wrong"
    assert not _IsImplementationFullChecking(c1, I) == True  # failed, invalid attr type
    c1.a_zoo = a_zoo

    # test if we can set foobar to None
    c1.foobar = None
    assert IsImplementation(c1, I) == True  # OK

    c1.foobar = "hello"
    assert not _IsImplementationFullChecking(c1, I) == True  # failed, invalid attr type


def testPassNoneInAssertImplementsFullChecking():
    with pytest.raises(AssertionError):
        AssertImplements(None, _InterfM1)

    with pytest.raises(AssertionError):
        AssertImplements(10, _InterfM1)


def testNoCheck():
    @ImplementsInterface(_InterfM1, no_check=True)
    class NoCheck:
        pass

    no_check = NoCheck()
    with pytest.raises(AssertionError):
        AssertImplements(no_check, _InterfM1)


def testCallbackAndInterfaces():
    """
        Tests if the interface "AssertImplements" works with "callbacked" methods.
    """

    @ImplementsInterface(_InterfM1)
    class My:
        def m1(self):
            ""

    def MyCallback():
        ""

    from oop_ext.foundation.callback import After

    o = My()
    AssertImplements(o, _InterfM1)

    After(o.m1, MyCallback)

    AssertImplements(o, _InterfM1)
    AssertImplements(o, _InterfM1)  # Not raises BadImplementationError


def testInterfaceStub():
    @ImplementsInterface(_InterfM1)
    class My:
        def m1(self):
            return "m1"

        def m2(self):
            ""

    m0 = My()
    m1 = _InterfM1(
        m0
    )  # will make sure that we only access the attributes/methods declared in the interface
    assert "m1" == m1.m1()
    getattr(m0, "m2")  # Not raises AttributeError
    with pytest.raises(AttributeError):
        getattr(m1, "m2")

    _InterfM1(m1)  # Not raise BadImplementationError


def testIsImplementationWithSubclasses():
    """
    Checks if the IsImplementation method works with subclasses interfaces.

    Given that an interface I2 inherits from I1 of a given object declared that it implements I2
    then it is implicitly declaring that implements I1.
    """

    @ImplementsInterface(_InterfM2)
    class My2:
        def m2(self):
            ""

    @ImplementsInterface(_InterfM3)
    class My3:
        def m3(self, arg1, arg2):
            ""

    @ImplementsInterface(_InterfM4)
    class My4:
        def m3(self, arg1, arg2):
            ""

        def m4(self):
            ""

    m2 = My2()
    m3 = My3()
    m4 = My4()

    # My2
    assert IsImplementation(m2, _InterfM3) == False

    # My3
    assert IsImplementation(m3, _InterfM3) == True
    assert IsImplementation(m3, _InterfM4) == False

    # My4
    assert IsImplementation(m4, _InterfM4) == True
    assert IsImplementation(m4, _InterfM3) == True

    # When wrapped in an m4 interface it should still accept m3 as a declared interface
    wrapped_intef_m4 = _InterfM4(m4)
    assert IsImplementation(wrapped_intef_m4, _InterfM4) == True
    assert IsImplementation(wrapped_intef_m4, _InterfM3) == True


def testIsImplementationWithBuiltInObjects():

    my_number = 10
    assert IsImplementation(my_number, _InterfM1) == False


def testClassImplementMethod():
    """
    Tests replacing a method that implements an interface with a class.

    The class must be derived from "Method" in order to be accepted as a valid
    implementation.
    """

    @ImplementsInterface(_InterfM1)
    class My:
        def m1(self):
            ""

    class MyRightMethod(Method):
        def __call__(self):
            ""

    class MyWrongMethod:
        def __call__(self):
            ""

    # NOTE: It doesn't matter runtime modifications in the instance, what is really being tested
    #       is the *class* of the object (My) is what is really being tested.
    m = My()
    m.m1 = MyWrongMethod()
    assert IsImplementation(m, _InterfM1) == True

    m.m1 = MyRightMethod()
    assert IsImplementation(m, _InterfM1) == True

    # NOTE: Testing behaviour of private methods here.
    from oop_ext.interface._interface import _IsImplementationFullChecking

    m = My()
    m.m1 = MyWrongMethod()
    r = _IsImplementationFullChecking(m, _InterfM1)
    assert r == False

    m.m1 = MyRightMethod()
    r = _IsImplementationFullChecking(m, _InterfM1)
    assert r == True

    del m.m1
    assert IsImplementation(m, _InterfM1) == True


def testGetImplementedInterfaces():
    @ImplementsInterface(_InterfM1)
    class A:
        def m1(self):
            ""

    class B(A):
        ""

    @ImplementsInterface(_InterfM4)
    class C:
        def m4(self):
            ""

        def m3(self, arg1, arg2):
            ""

    assert 1 == len(GetImplementedInterfaces(B()))
    assert set(GetImplementedInterfaces(C())) == {_InterfM4, _InterfM3}


def testGetImplementedInterfaces2():
    @ImplementsInterface(_InterfM1)
    class A:
        def m1(self):
            ""

    @ImplementsInterface(_InterfM2)
    class B(A):
        def m2(self):
            ""

    assert 2 == len(GetImplementedInterfaces(B()))
    with pytest.raises(AssertionError):
        AssertImplements(A(), _InterfM2)

    AssertImplements(B(), _InterfM2)


def testAdaptableInterface():
    @ImplementsInterface(IAdaptable)
    class A:
        def GetAdapter(self, interface_class):
            if interface_class == _InterfM1:
                return B()

    @ImplementsInterface(_InterfM1)
    class B:
        def m1(self):
            ""

    a = A()
    b = _InterfM1(a)  # will try to adapt, as it does not directly implements m1
    assert b is not None
    b.m1()  # has m1
    with pytest.raises(AttributeError):
        getattr(b, "non_existent")

    assert isinstance(b, InterfaceImplementorStub)


def testNull():
    AssertImplements(Null(), _InterfM2)  # Not raises BadImplementationError

    class ExtendedNull(Null):
        ""

    AssertImplements(ExtendedNull(), _InterfM2)  # Not raises BadImplementationError


def testSetItem():
    class InterfSetItem(Interface):
        def __setitem__(self, item_id, subject):
            ""

        def __getitem__(self, item_id):
            ""

    @ImplementsInterface(InterfSetItem)
    class A:
        def __setitem__(self, item_id, subject):
            self.set = (item_id, subject)

        def __getitem__(self, item_id):
            return self.set

    a = InterfSetItem(A())
    a["10"] = 1
    assert ("10", 1) == a["10"]


def testAssertImplementsDoesNotDirObject():
    """
    AssertImplements does not attempt to __getattr__ methods from an object, it only considers
    methods that are actually bound to the class.
    """

    class M1:
        def __getattr__(self, attr):
            assert attr == "m1"  # This test only accepts this attribute

            class MyMethod(Method):
                def __call__(self):
                    ""

            return MyMethod()

    m1 = M1()
    m1.m1()
    with pytest.raises(AssertionError):
        AssertImplements(m1, _InterfM1)


def testImplementorWithAny():
    """
    You must explicitly declare that you implement an Interface.
    """

    class M3:
        def m3(self, *args, **kwargs):
            ""

    with pytest.raises(AssertionError):
        AssertImplements(M3(), _InterfM3)


def testInterfaceCheckRequiresInterface():
    class M3:
        def m3(self, *args, **kwargs):
            ""

    with pytest.raises(InterfaceError):
        AssertImplements(M3(), M3)

    with pytest.raises(InterfaceError):
        IsImplementation(M3(), M3)


def testReadOnlyAttribute():
    class IZoo(Interface):
        zoo = ReadOnlyAttribute(int)

    @ImplementsInterface(IZoo)
    class Zoo:
        def __init__(self, value):
            self.zoo = value

    a_zoo = Zoo(value=99)
    AssertImplements(a_zoo, IZoo)


def testReadOnlyAttributeMissingImplementation():
    """
    First implementation of changes in interfaces to support read-only attributes was not
    including read-only attributes when AssertImplements was called.

    This caused missing read-only attributes to go unnoticed and sometimes false positives,
    recognizing objects as valid implementations when in fact they weren't.
    """

    class IZoo(Interface):
        zoo = ReadOnlyAttribute(int)

    # Doesn't have necessary 'zoo' attribute, should raise a bad implementation error
    @ImplementsInterface(IZoo)
    class FlawedZoo:
        def __init__(self, value):
            ""

    # NOTE: Testing private methods here
    from oop_ext.interface._interface import _AssertImplementsFullChecking

    a_flawed_zoo = FlawedZoo(value=101)
    with pytest.raises(BadImplementationError):
        _AssertImplementsFullChecking(a_flawed_zoo, IZoo)


def testImplementsTwice():
    class I1(Interface):
        def Method1(self):
            ""

    class I2(Interface):
        def Method2(self):
            ""

    def Create():
        @ImplementsInterface(I1)
        @ImplementsInterface(I2)
        class Foo:
            def Method2(self):
                ""

    # Error because I1 is not implemented.
    with pytest.raises(AssertionError):
        Create()


def testDeclareClassImplements():
    class I1(Interface):
        def M1(self):
            ""

    class I2(Interface):
        def M2(self):
            ""

    class C0:
        ""

    class C1:
        def M1(self):
            ""

    class C2:
        def M2(self):
            ""

    @ImplementsInterface(I2)
    class C2B:
        def M2(self):
            ""

    class C12B(C1, C2B):
        ""

    with pytest.raises(AssertionError):
        DeclareClassImplements(C0, I1)

    assert IsImplementation(C1, I1) == False
    with pytest.raises(AssertionError):
        AssertImplements(C1, I1)

    assert IsImplementation(C12B, I1) == False  # C1 still does not implements I1

    DeclareClassImplements(C1, I1)

    assert IsImplementation(C1, I1) == True
    AssertImplements(C1, I1)

    # C1 is parent of C12B, and, above, it was declared that C1 implements I1, so C12B should
    # automatically implement I1. But this is not automatic, so you must also declare for it!

    assert IsImplementation(C12B, I1) == False  # not automatic
    assert (
        IsImplementation(C12B, I2) == True
    )  # inheritance for Implements still works automatically

    DeclareClassImplements(C12B, I1)

    assert IsImplementation(C12B, I1) == True  # now it implements
    assert IsImplementation(C12B, I2) == True

    DeclareClassImplements(C2, I2)

    assert IsImplementation(C2, I2) == True
    AssertImplements(C2, I2)

    # Exception: if I define a class *after* using DeclareClassImplements in the base, it works:
    class C12(C1, C2):
        ""

    AssertImplements(C12, I1)
    AssertImplements(C12, I2)


def testCallableInterfaceStub():
    """
    Validates that is possible to create stubs for interfaces of callables (i.e. declaring
    __call__ method in interface).

    If a stub for a interface not declared as callable is tried to be executed as callable it
    raises an error.
    """

    # ok, calling a stub for a callable
    class IFoo(Interface):
        def __call__(self, bar):
            ""

    @ImplementsInterface(IFoo)
    class Foo:
        def __call__(self, bar):
            ""

    foo = Foo()
    stub = IFoo(foo)
    stub(bar=None)  # NotRaises TypeError

    # wrong, calling a stub for a non-callable
    class IBar(Interface):
        def something(self, stuff):
            ""

    @ImplementsInterface(IBar)
    class Bar:
        def something(self, stuff):
            ""

    bar = Bar()
    stub = IBar(bar)
    with pytest.raises(AttributeError):
        stub(stuff=None)


def testImplementsInterfaceAsBoolError():
    """
    Test if the common erroneous use of interface.ImplementsInterface() instead of
    interface.IsImplementation() to test if an object implements an interface correctly
    raises a RuntimeError.
    """

    class I1(Interface):
        def M1(self):
            pass

    @ImplementsInterface(I1)
    class C1:
        def M1(self):
            pass

    obj = C1()

    assert IsImplementation(obj, I1)

    with pytest.raises(RuntimeError):
        if ImplementsInterface(obj, I1):
            pytest.fail('Managed to test "if ImplementsInterface(obj, I1):"')


@pytest.mark.parametrize("check_before", [True, False])
@pytest.mark.parametrize("autospec", [True, False])
def test_interface_subclass_mocked(mocker, check_before, autospec):
    """
    Interfaces check implementation during class declaration. However a
    subclass doesn't have its implementation checked.

    Then if there is an implementation AFTER subclass is already mocked
    the interface check will only work if `autospec` is used.

    Note that interface implementation checks keeps a cache, so if
    subclass was checked before it was mocked it would pass anyway.

    :type mocker: MockTestFixture
    :type check_before: bool
    :type autospec: bool
    """
    from oop_ext import interface

    class II(interface.Interface):
        def foo(self, a, b, c):
            pass

    @interface.ImplementsInterface(II)
    class Foo:
        def foo(self, a, b, c):
            pass

    class Bar(Foo):
        pass

    if check_before:
        interface.IsImplementation(Bar, II)

    mocker.patch.object(Foo, "foo", autospec=autospec)

    assert interface.IsImplementation(Bar, II) == (autospec or check_before)


def testErrorOnInterfaceDeclaration():
    def Check():
        class Foo:
            pass

        from oop_ext import interface

        interface.ImplementsInterface(_InterfM1)(Foo)

    with pytest.raises(AssertionError):
        Check()
