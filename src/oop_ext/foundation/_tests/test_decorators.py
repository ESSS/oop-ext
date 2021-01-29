import warnings
from typing import Tuple, Any, List

import pytest

from oop_ext.foundation import is_frozen
from oop_ext.foundation.decorators import Abstract, Deprecated, Implements, Override


def testImplementsFail() -> None:
    with pytest.raises(AssertionError):

        class IFoo:
            def DoIt(self):
                ""

        class Implementation:
            @Implements(IFoo.DoIt)
            def DoNotDoIt(self):
                ""


def testImplementsOK() -> None:
    class IFoo:
        def Foo(self):
            """
            docstring
            """

    class Impl:
        @Implements(IFoo.Foo)
        def Foo(self):
            return self.__class__.__name__

    assert IFoo.Foo.__doc__ == Impl.Foo.__doc__

    # Just for 100% coverage.
    assert Impl().Foo() == "Impl"


def testOverride() -> None:
    def TestOK():
        class A:
            def Method(self):
                """
                docstring
                """

        class B(A):
            @Override(A.Method)
            def Method(self):
                return 2

        b = B()
        assert b.Method() == 2
        assert A.Method.__doc__ == B.Method.__doc__

    def TestERROR():
        class A:
            def MyMethod(self):
                ""

        class B(A):
            @Override(A.Method)  # it will raise an error at this point
            def Method(self):
                ""

    def TestNoMatch():
        class A:
            def Method(self):
                ""

        class B(A):
            @Override(A.Method)
            def MethodNoMatch(self):
                ""

    TestOK()
    with pytest.raises(AttributeError):
        TestERROR()

    with pytest.raises(AssertionError):
        TestNoMatch()


def testDeprecated(monkeypatch) -> None:
    def MyWarn(*args, **kwargs):
        warn_params.append((args, kwargs))

    monkeypatch.setattr(warnings, "warn", MyWarn)

    was_development = is_frozen.SetIsDevelopment(True)
    try:
        # Emit messages when in development
        warn_params: List[Tuple[Any, Any]] = []

        # ... deprecation with alternative
        @Deprecated("OtherMethod")
        def Method1():
            pass

        # ... deprecation without alternative
        @Deprecated()
        def Method2():
            pass

        Method1()
        Method2()
        assert warn_params == [
            (
                ("DEPRECATED: 'Method1' is deprecated, use 'OtherMethod' instead",),
                {"stacklevel": 2},
            ),
            (("DEPRECATED: 'Method2' is deprecated",), {"stacklevel": 2}),
        ]

        # No messages on release code
        is_frozen.SetIsDevelopment(False)

        warn_params = []

        @Deprecated()
        def FrozenMethod():
            pass

        FrozenMethod()
        assert warn_params == []
    finally:
        is_frozen.SetIsDevelopment(was_development)


def testAbstract() -> None:
    class Alpha:
        @Abstract
        def Method(self):
            ""

    alpha = Alpha()
    with pytest.raises(NotImplementedError):
        alpha.Method()
