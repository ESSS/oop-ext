import pytest

from oop_ext.foundation.callback.single_call_callback import SingleCallCallback


def testSingleCallCallback() -> None:
    class Stub:
        pass

    stub = Stub()
    callback = SingleCallCallback(stub)

    called = []

    def Method1(arg):
        called.append(arg)

    def Method2(arg):
        called.append(arg)

    def Method3(arg):
        called.append(arg)

    callback.Register(Method1)

    callback()

    assert called == [stub]

    with pytest.raises(AssertionError):
        callback()

    assert called == [stub]

    callback.Register(Method1)  # It was already there, so, won't be called again.

    assert called == [stub]

    callback.Register(Method2)

    assert called == [stub, stub]

    del stub
    del called[:]

    with pytest.raises(ReferenceError):
        callback.Register(Method1)


def testSingleCallCallbackNoParameter() -> None:
    class Stub:
        pass

    callback = SingleCallCallback(None)

    called = []

    def Method1():
        called.append("Method1")

    def Method2():
        called.append("Method2")

    callback.Register(Method1)

    callback()

    assert called == ["Method1"]

    callback.Register(Method2)

    assert called == ["Method1", "Method2"]

    with pytest.raises(AssertionError):
        callback()

    callback.AllowCallingAgain()
    callback()

    assert called == ["Method1", "Method2", "Method1", "Method2"]

    callback.Register(Method1)
    assert called == ["Method1", "Method2", "Method1", "Method2"]

    callback.Unregister(Method1)
    callback.Register(Method1)
    assert called == ["Method1", "Method2", "Method1", "Method2", "Method1"]
