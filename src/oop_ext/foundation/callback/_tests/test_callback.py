import weakref
from functools import partial
from typing import Generator, Any, List

import pytest

from oop_ext.foundation.callback import After, Before, Callback, Callbacks, Remove
from oop_ext.foundation.types_ import Null
from oop_ext.foundation.weak_ref import GetWeakProxy, WeakMethodProxy, WeakMethodRef


class _MyClass:
    def SetAlpha(self, value):
        self.alpha = value

    def SetBravo(self, value):
        self.bravo = value


class C:
    def __init__(self, test_case):
        self.test_case = test_case

    def foo(self, arg):
        self.test_case.foo_called = (self, arg)
        return arg


class Stub:
    def call(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def restore_test_classes() -> Generator[None, None, None]:
    """
    It can't reliably bind callbacks to methods in local temporary classes from Python 3 onward,
    as callback is unable to later know to which class was bound to.

    For this reason, we have to use global, shared classes for these tests. This fixture makes sure
    these test classes used are always restored to clean state to avoid undesired side-effects in
    other tests.
    """
    original_stub_call = Stub.call
    original_c_foo = C.foo

    yield
    Stub.call = original_stub_call  # type:ignore[assignment]
    C.foo = original_c_foo  # type:ignore[assignment]


class Test:
    def setup_method(self, method):
        self.foo_called = None

        self.a = C(self)
        self.b = C(self)

        def after(*args):
            self.after_called = args
            self.after_count += 1

        self.after = after
        self.after_called = None
        self.after_count = 0

        def before(*args):
            self.before_called = args
            self.before_count += 1

        self.before = before
        self.before_called = None
        self.before_count = 0

    def testClassOverride(self) -> None:
        Before(C.foo, self.before)
        After(C.foo, self.after)

        self.a.foo(1)
        assert self.foo_called == (self.a, 1)
        assert self.after_called == (self.a, 1)
        assert self.after_count == 1
        assert self.before_called == (self.a, 1)
        assert self.before_count == 1

        self.b.foo(2)
        assert self.foo_called == (self.b, 2)
        assert self.after_called == (self.b, 2)
        assert self.after_count == 2
        assert self.before_called == (self.b, 2)
        assert self.before_count == 2

        assert Remove(C.foo, self.before)

        self.a.foo(3)
        assert self.foo_called == (self.a, 3)
        assert self.after_called == (self.a, 3)
        assert self.after_count == 3
        assert self.before_called == (self.b, 2)
        assert self.before_count == 2

    def testInstanceOverride(self) -> None:
        Before(self.a.foo, self.before)
        After(self.a.foo, self.after)

        self.a.foo(1)
        assert self.foo_called == (self.a, 1)
        assert self.after_called == (1,)
        assert self.before_called == (1,)
        assert self.after_count == 1
        assert self.before_count == 1

        self.b.foo(2)
        assert self.foo_called == (self.b, 2)
        assert self.after_called == (1,)
        assert self.before_called == (1,)
        assert self.after_count == 1
        assert self.before_count == 1

        assert Remove(self.a.foo, self.before) == True

        self.a.foo(2)
        assert self.foo_called == (self.a, 2)
        assert self.after_called == (2,)
        assert self.before_called == (1,)
        assert self.after_count == 2
        assert self.before_count == 1

        Before(self.a.foo, self.before)
        Before(self.a.foo, self.before)  # Registering twice has no effect the 2nd time

        self.a.foo(5)
        assert self.before_called == (5,)
        assert self.before_count == 2

    def testBoundMethodsWrong(self) -> None:
        foo = self.a.foo
        Before(foo, self.before)
        After(foo, self.after)

        foo(10)
        assert 0 == self.before_count
        assert 0 == self.after_count

    def testBoundMethodsRight(self) -> None:
        foo = self.a.foo
        foo = Before(foo, self.before)
        foo = After(foo, self.after)

        foo(10)
        assert self.before_count == 1
        assert self.after_count == 1

    def testReferenceDies(self) -> None:
        class Receiver:
            def before(dummy, *args):  # @NoSelf
                self.before_count += 1
                self.before_args = args

        rec = Receiver()
        self.before_count = 0
        self.before_args = None

        foo = self.a.foo
        foo = Before(foo, rec.before)

        foo(10)
        assert self.before_args == (10,)
        assert self.before_count == 1

        del rec  # kill the receiver

        foo(20)
        assert self.before_args == (10,)
        assert self.before_count == 1

    def testSenderDies(self) -> None:
        class Sender:
            def foo(s, *args):  # @NoSelf
                s.args = args

            def __del__(dummy):  # @NoSelf
                self.sender_died = True

        self.sender_died = False
        s = Sender()
        w = weakref.ref(s)
        Before(s.foo, self.before)
        s.foo(10)
        f = s.foo  # hold a strong reference to s
        assert self.before_count == 1
        assert self.before_called == (10,)

        assert not self.sender_died
        del s
        assert self.sender_died

        with pytest.raises(ReferenceError):
            f(10)  # must have already died: we don't have a strong reference
        assert w() is None

    def testLessArgs(self) -> None:
        class C:
            def foo(self, _x, _y, **_kwargs):
                pass

        def after_2(x, y, *args, **kwargs):
            self.after_2_res = x, y

        def after_1(x, *args, **kwargs):
            self.after_1_res = x

        def after_0(*args, **kwargs):
            self.after_0_res = 0

        self.after_2_res = None
        self.after_1_res = None
        self.after_0_res = None

        c = C()

        After(c.foo, after_2)
        After(c.foo, after_1)
        After(c.foo, after_0)

        c.foo(10, 20, foo=1)
        assert self.after_2_res == (10, 20)
        assert self.after_1_res == 10
        assert self.after_0_res == 0

    def testWithCallable(self) -> None:
        class Stub:
            def call(self, _b):
                pass

        class Aux:
            def __call__(self, _b):
                self.called = True

        s = Stub()
        a = Aux()
        After(s.call, a)
        s.call(True)

        assert a.called

    def testCallback(self) -> None:

        self.args = [None, None]

        def f1(*args):
            self.args[0] = args

        def f2(*args):
            self.args[1] = args

        c = Callback()
        c.Register(f1)

        c(1, 2)

        assert self.args[0] == (1, 2)

        c.Unregister(f1)
        self.args[0] = None
        c(10, 20)
        assert self.args[0] == None

        def foo():
            pass

        c.Unregister(foo)

    def test_extra_args(self) -> None:
        """
        Tests the extra-args parameter in Register method.
        """
        self.zulu_calls: List[Any] = []

        def zulu_one(*args):
            self.zulu_calls.append(args)

        def zulu_too(*args):
            self.zulu_calls.append(args)

        alpha = Callback()
        alpha.Register(zulu_one, (1, 2))

        assert self.zulu_calls == []

        alpha("a")
        assert self.zulu_calls == [(1, 2, "a")]

        alpha("a", "b", "c")
        assert self.zulu_calls == [(1, 2, "a"), (1, 2, "a", "b", "c")]

        # Test a second method with extra-args
        alpha.Register(zulu_too, (9,))

        alpha("a")
        assert self.zulu_calls == [
            (1, 2, "a"),
            (1, 2, "a", "b", "c"),
            (1, 2, "a"),
            (9, "a"),
        ]

    def test_sender_as_parameter(self) -> None:
        self.zulu_calls = []

        def zulu_one(*args):
            self.zulu_calls.append(args)

        def zulu_two(*args):
            self.zulu_calls.append(args)

        Before(self.a.foo, zulu_one, sender_as_parameter=True)

        assert self.zulu_calls == []
        self.a.foo(0)
        assert self.zulu_calls == [(self.a, 0)]

        # The second method registered with the sender_as_parameter on did not receive it.
        Before(self.a.foo, zulu_two, sender_as_parameter=True)

        self.zulu_calls = []
        self.a.foo(1)
        assert self.zulu_calls == [(self.a, 1), (self.a, 1)]

    def test_sender_as_parameter_after_and_before(self) -> None:
        self.zulu_calls = []

        def zulu_one(*args):
            self.zulu_calls.append((1, args))

        def zulu_too(*args):
            self.zulu_calls.append((2, args))

        Before(self.a.foo, zulu_one, sender_as_parameter=True)
        After(self.a.foo, zulu_too)

        assert self.zulu_calls == []
        self.a.foo(0)
        assert self.zulu_calls == [(1, (self.a, 0)), (2, (0,))]

    def testContains(self) -> None:
        def foo(x):
            pass

        c = Callback()
        assert not c.Contains(foo)
        c.Register(foo)

        assert c.Contains(foo)
        c.Unregister(foo)
        assert not c.Contains(foo)

    args: Any

    def testCallbackReceiverDies(self) -> None:
        class A:
            def on_foo(dummy, *args):  # @NoSelf
                self.args = args

        self.args = None
        a = A()
        weak_a = weakref.ref(a)

        foo = Callback()
        foo.Register(a.on_foo)

        foo(1, 2)
        assert self.args == (1, 2)
        assert weak_a() is a

        foo(3, 4)
        assert self.args == (3, 4)
        assert weak_a() is a

        del a
        assert weak_a() is None
        foo(5, 6)
        assert self.args == (3, 4)

    def testActionMethodDies(self) -> None:
        class A:
            def foo(self):
                pass

        def FooAfter():
            self.after_exec += 1

        self.after_exec = 0

        a = A()
        weak_a = weakref.ref(a)
        After(a.foo, FooAfter)
        a.foo()

        assert self.after_exec == 1

        del a

        # IMPORTANT: behaviour change. The description below is for the previous
        # behaviour. That is not true anymore (the circular reference is not kept anymore)

        # callback creates a circular reference; that's ok, because we want
        # to still be able to do "x = a.foo" and keep a strong reference to it

        assert weak_a() is None

    def testAfterRegisterMultipleAndUnregisterOnce(self) -> None:
        class A:
            def foo(self):
                pass

        a = A()

        def FooAfter1():
            Remove(a.foo, FooAfter1)
            self.after_exec += 1

        def FooAfter2():
            self.after_exec += 1

        self.after_exec = 0
        After(a.foo, FooAfter1)
        After(a.foo, FooAfter2)
        a.foo()

        # it was iterating in the original after, so, this case
        # was only giving 1 result and not 2 as it should
        assert 2 == self.after_exec

        a.foo()
        assert 3 == self.after_exec
        a.foo()
        assert 4 == self.after_exec

        After(a.foo, FooAfter2)
        After(a.foo, FooAfter2)
        After(a.foo, FooAfter2)

        a.foo()
        assert 5 == self.after_exec

        Remove(a.foo, FooAfter2)
        a.foo()
        assert 5 == self.after_exec

    def testOnClassMethod(self) -> None:
        class A:
            @classmethod
            def foo(cls):
                pass

        self.after_exec_class_method = 0

        def FooAfterClassMethod():
            self.after_exec_class_method += 1

        self.after_exec_self_method = 0

        def FooAfterSelfMethod():
            self.after_exec_self_method += 1

        After(A.foo, FooAfterClassMethod)

        a = A()
        After(a.foo, FooAfterSelfMethod)

        a.foo()
        assert 1 == self.after_exec_class_method
        assert 1 == self.after_exec_self_method

        Remove(A.foo, FooAfterClassMethod)
        a.foo()
        assert 1 == self.after_exec_class_method
        assert 2 == self.after_exec_self_method

    def testSenderDies2(self) -> None:
        After(self.a.foo, self.after, True)
        self.a.foo(1)
        assert (self.a, 1) == self.after_called

        a = weakref.ref(self.a)
        self.after_called = None
        self.foo_called = None
        del self.a
        assert a() is None

    def testCallbacksBeforeAfter(self) -> None:
        """
        Callbacks.Before and After should call the registered function before/after another
        function.
        """
        events = []

        def bar(arg, when):
            assert arg == 42
            events.append(when)

        callbacks = Callbacks()
        callbacks.Before(self.a.foo, partial(bar, when="before_bar"))
        callbacks.After(self.a.foo, partial(bar, when="after_bar"))

        self.a.foo(42)
        assert events == ["before_bar", "after_bar"]
        callbacks.RemoveAll()
        self.a.foo(42)
        assert events == ["before_bar", "after_bar"]

    def testCallbacksRegister(self) -> None:
        """
        Callbacks().Register() when used as a context manager unregisters the callbacks
        automatically when the context ends.
        """
        c1 = Callback()
        c2 = Callback()

        events = []

        def bar(when):
            events.append(when)

        with Callbacks() as callbacks:
            callbacks.Register(c1, bar)
            callbacks.Register(c2, bar)

            c1(when="c1-first")
            c2(when="c2-first")
            assert events == ["c1-first", "c2-first"]

        c1(when="c1-second")
        c2(when="c2-second")

        assert events == ["c1-first", "c2-first"]

    def testAfterRemove(self) -> None:

        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)

        After(my_object.SetAlpha, my_object.SetBravo)

        my_object.SetAlpha(1)
        assert my_object.bravo == 1

        Remove(my_object.SetAlpha, my_object.SetBravo)

        my_object.SetAlpha(2)
        assert my_object.bravo == 1

    def testAfterRemoveCallback(self) -> None:
        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)

        # Test After/Remove with a callback
        event = Callback()
        After(my_object.SetAlpha, event)
        event.Register(my_object.SetBravo)

        my_object.SetAlpha(3)
        assert my_object.bravo == 3

        Remove(my_object.SetAlpha, event)

        my_object.SetAlpha(4)
        assert my_object.bravo == 3

    def testAfterRemoveCallbackAndSenderAsParameter(self) -> None:
        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)

        def event(obj_or_value, value):
            self._value = value

        # Test After/Remove with a callback and sender_as_parameter
        After(my_object.SetAlpha, event, sender_as_parameter=True)

        my_object.SetAlpha(3)

        assert 3 == self._value

        Remove(my_object.SetAlpha, event)

        my_object.SetAlpha(4)
        assert 3 == self._value

    def testDeadCallbackCleared(self) -> None:
        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)
        self._value = []

        class B:
            def event(s, value):  # @NoSelf
                self._b_value = value

        class A:
            def event(s, obj, value):  # @NoSelf
                self._a_value = value

        a = A()
        b = B()

        self._a_value = None
        self._b_value = None

        # Test After/Remove with a callback and sender_as_parameter
        After(my_object.SetAlpha, a.event, sender_as_parameter=True)
        After(my_object.SetAlpha, b.event, sender_as_parameter=False)

        w = weakref.ref(a)
        my_object.SetAlpha(3)
        assert 3 == self._a_value
        assert 3 == self._b_value
        del a
        my_object.SetAlpha(4)
        assert 3 == self._a_value
        assert 4 == self._b_value
        assert w() is None

    def testRemoveCallbackPlain(self) -> None:
        class C:
            def __init__(self, name):
                self.name = name

            def OnCallback(self):
                pass

            def __eq__(self, other):
                return self.name == other.name

            def __ne__(self, other):
                return not self == other

        instance1 = C("instance")
        instance2 = C("instance")
        assert instance1 == instance2

        c = Callback()
        c.Register(instance1.OnCallback)
        c.Register(instance2.OnCallback)

        # removing first callback, and checking that it was actually removed as expected
        c.Unregister(instance1.OnCallback)
        assert not c.Contains(instance1.OnCallback) == True

        # self.assertNotRaises(RuntimeError, c.Unregister, instance1.OnCallback)
        c.Unregister(instance1.OnCallback)

        # removing second callback, and checking that it was actually removed as expected
        c.Unregister(instance2.OnCallback)
        assert not c.Contains(instance2.OnCallback) == True

        # self.assertNotRaises(RuntimeError, c.Unregister, instance2.OnCallback)
        c.Unregister(instance2.OnCallback)

    def testRemoveCallbackContext(self) -> None:
        """Callback.Register() returns a context that can be used to unregister that call."""
        events = []

        def bar(when):
            events.append(when)

        contexts = []
        c1 = Callback()
        contexts.append(c1.Register(bar))

        c2 = Callback()
        contexts.append(c2.Register(bar))

        c1("c1-first")
        c2("c2-first")

        assert events == ["c1-first", "c2-first"]

        for context in contexts:
            context.Unregister()

        c1("c1-second")
        c2("c2-second")
        assert events == ["c1-first", "c2-first"]

    def testRegisterTwice(self) -> None:
        self.called = 0

        def After(*args):
            self.called += 1

        c = Callback()
        c.Register(After)
        c.Register(After)
        c.Register(After)
        c()
        assert self.called == 1

    def testHandleErrorOnCallback(self, mocker) -> None:
        self.called = 0

        def After(*args, **kwargs):
            self.called += 1
            raise RuntimeError("test")

        def After2(*args, **kwargs):
            self.called += 1
            raise RuntimeError("test2")

        c = Callback()
        c.Register(After)
        c.Register(After2)

        # test the default behaviour: errors are not handled and stop execution as usual
        self.called = 0
        c = Callback()
        c.Register(After)
        c.Register(After2)
        with pytest.raises(RuntimeError):
            c()
        assert self.called == 1

    def testAfterBeforeHandleError(self) -> None:
        class C:
            def Method(self, x):
                return x * 2

        def AfterMethod(*args):
            self.after_called += 1
            raise RuntimeError

        def BeforeMethod(*args):
            self.before_called += 1
            raise RuntimeError

        self.before_called = 0
        self.after_called = 0

        c = C()
        Before(c.Method, BeforeMethod)
        After(c.Method, AfterMethod)

        # Now behavior changed and it will fail on first callback error
        with pytest.raises(RuntimeError):
            assert c.Method(10) == 20

        assert self.before_called == 1
        assert self.after_called == 0

    def testKeyReusedAfterDead(self, monkeypatch) -> None:
        self._gotten_key = False

        def GetKey(*args, **kwargs):
            self._gotten_key = True
            return 1

        monkeypatch.setattr(Callback, "_GetKey", GetKey)

        def AfterMethod(*args):
            pass

        def AfterMethodB(*args):
            pass

        c = Callback()

        c.Register(AfterMethod)
        self._gotten_key = False
        assert not c.Contains(AfterMethodB)
        assert c.Contains(AfterMethod)
        assert self._gotten_key

        # As we made _GetKey return always the same, this will make it remove one and add the
        # other one, so, the contains will have to check if they're actually the same or not.
        c.Register(AfterMethodB)
        self._gotten_key = False
        assert c.Contains(AfterMethodB)
        assert not c.Contains(AfterMethod)
        assert self._gotten_key

        class A:
            def __init__(self):
                self._a = 0

            def GetA(self):
                return self._a

            def SetA(self, value):
                self._a = value

            a = property(GetA, SetA)

        a = A()
        # If registering a bound, it doesn't contain the unbound
        c.Register(a.SetA)
        assert not c.Contains(AfterMethodB)
        assert not c.Contains(A.SetA)
        assert c.Contains(a.SetA)

        # But if registering an unbound, it contains the bound
        c.Register(A.SetA)
        assert not c.Contains(AfterMethodB)
        assert c.Contains(A.SetA)
        assert c.Contains(a.SetA)

        c.Register(a.SetA)
        assert len(c) == 1
        del a
        assert not c.Contains(AfterMethodB)
        assert len(c) == 0

        a = A()
        from oop_ext.foundation.callback._callback import _CallbackWrapper

        c.Register(_CallbackWrapper(WeakMethodRef(a.SetA)))
        assert len(c) == 1
        del a
        assert not c.Contains(AfterMethodB)
        assert len(c) == 0

    def testNeedsUnregister(self) -> None:
        c = Callback()

        # Even when the function isn't registered, we not raise an error.
        def Func():
            pass

        # self.assertNotRaises(RuntimeError, c.Unregister, Func)
        c.Unregister(Func)

    def testUnregisterAll(self) -> None:
        c = Callback()

        # self.assertNotRaises(AttributeError, c.UnregisterAll)
        c.UnregisterAll()

        self.called = False

        def Func():
            self.called = True

        c.Register(Func)
        c.UnregisterAll()

        c()
        assert self.called == False

    def testOnClassAndOnInstance1(self) -> None:
        vals = []

        def OnCall1(instance, val):
            vals.append(("call_instance", val))

        def OnCall2(val):
            vals.append(("call_class", val))

        After(Stub.call, OnCall1)
        s = Stub()
        After(s.call, OnCall2)

        s.call(True)
        assert [("call_instance", True), ("call_class", True)] == vals

    def testOnClassAndOnInstance2(self) -> None:
        vals = []

        def OnCall1(instance, val):
            vals.append(("call_class", val))

        def OnCall2(val):
            vals.append(("call_instance", val))

        s = Stub()
        After(s.call, OnCall2)
        After(Stub.call, OnCall1)

        # Tricky thing here: because we added the callback in the class after we added it to the
        # instance, the callback on the instance cannot be rebound, thus, calling it on the instance
        # won't really trigger the callback on the class (not really what would be expected of the
        # after method, but I couldn't find a reasonable way to overcome that).
        # A solution could be keeping track of all callbacks and rebinding all existent ones in the
        # instances to the one in the class, but it seems overkill for such an odd situation.
        s.call(True)
        assert [("call_instance", True)] == vals

    def testOnNullClass(self) -> None:
        class _MyNullSubClass(Null):
            def GetIstodraw(self):
                return True

        s = _MyNullSubClass()

        def AfterSetIstodraw():
            pass

        After(s.SetIstodraw, AfterSetIstodraw)

    def testListMethodAsCallback(self, mocker) -> None:
        """
        This was based on a failure on
        souring20.core.model.multiple_simulation_runs._tests.test_multiple_simulation_runs.testNormalExecution
        which failed with "TypeError: cannot create weak reference to 'list' object"
        """
        vals: List[str] = []

        class Stub:
            def call(self, *args, **kwargs):
                pass

        s = Stub()
        After(s.call, vals.append)

        s.call("call_append")
        assert ["call_append"] == vals

    def testCallbackWithMagicMock(self, mocker) -> None:
        """
        Check that we can register mock.MagicMock objects in callbacks.

        This makes it easier to test that public callbacks are being called with correct arguments.

        Usage (in testing, of course):

            save_listener = mock.MagicMock(spec=lambda: None)
            project_manager.on_save.Register(save_listener)
            project_manager.SlotSave()
            assert save_listener.call_args == mock.call('foo.file', '.txt')

        Instead of the more traditional:

            def OnSave(filename, ext):
                self.filename = filename
                self.ext = ext

            self.filename = None
            self.ext = ext

            project_manager.on_save.Register(OnSave)
            project_manager.SlotSave()
            assert (self.filename, self.ext) == ('foo.file', '.txt')
        """
        c = Callback()

        with pytest.raises(RuntimeError):
            c.Register(mocker.MagicMock())

        magic_mock = mocker.stub()
        c = Callback()
        c.Register(magic_mock)

        c(10, name="X")
        assert magic_mock.call_args_list == [mocker.call(10, name="X")]

        c(20, name="Y")
        assert magic_mock.call_args_list == [
            mocker.call(10, name="X"),
            mocker.call(20, name="Y"),
        ]

        c.Unregister(magic_mock)
        c(30, name="Z")
        assert len(magic_mock.call_args_list) == 2

    def testCallbackInstanceWeakRef(self) -> None:
        class Obj:
            def __init__(self):
                self.called = False

            def __call__(self):
                self.called = True

        c = Callback()
        obj = Obj()
        c.Register(obj)
        c()
        assert c.Contains(obj)
        assert obj.called
        obj_ref = weakref.ref(obj)
        del obj
        assert obj_ref() is None

    def testBeforeAfterWeakProxy(self) -> None:
        class Foo:
            def __init__(self):
                Before(self.SetFilename, GetWeakProxy(self._BeforeSetFilename))
                After(self.SetFilename, GetWeakProxy(self._AfterSetFilename))
                self.before = False
                self.after = False

            def _BeforeSetFilename(self, *args, **kwargs):
                self.before = True

            def _AfterSetFilename(self, *args, **kwargs):
                self.after = True

            def SetFilename(self, f):
                pass

        foo = Foo()
        foo.SetFilename("bar")
        assert foo.before
        assert foo.after

    def testKeepStrongReference(self) -> None:
        class Obj:
            __CALLBACK_KEEP_STRONG_REFERENCE__ = True

            def __init__(self):
                self.called = False

            def __call__(self):
                self.called = True

        c = Callback()
        obj = Obj()
        c.Register(obj)
        c()
        assert c.Contains(obj)
        assert obj.called
        obj_ref = weakref.ref(obj)
        del obj
        # Not collected because of __CALLBACK_KEEP_STRONG_REFERENCE__ in the class.
        assert obj_ref() is not None

    def testWeakMethodProxy(self) -> None:
        class Obj:
            def Foo(self):
                self.called = True

        obj = Obj()
        proxy = WeakMethodProxy(obj.Foo)

        c = Callback()
        c.Register(proxy)
        c()
        assert obj.called
        assert c.Contains(proxy)
        obj_ref = weakref.ref(obj)
        del obj
        assert obj_ref() is None
        c()
        assert len(c) == 0

    def testWeakMethodProxy2(self) -> None:
        def Foo():
            self.called = True

        proxy = WeakMethodProxy(Foo)

        c = Callback()
        c.Register(proxy)
        c()
        assert self.called
        assert c.Contains(proxy)

    def testWeakRefToCallback(self) -> None:
        c = Callback()
        c_ref = weakref.ref(c)
        assert c_ref() is c

    def testCallbackAndPartial(self) -> None:
        from functools import partial

        called = []

        def Method(a):
            called.append(a)

        c = Callback()
        c.Register(lambda: Method("lambda"))
        c.Register(partial(Method, "partial"))
        c()
        assert called == ["lambda", "partial"]

    def testCallbackInsideCallback(self) -> None:
        class A(object):
            c = Callback()

            def __init__(self, **ka):
                super().__init__(**ka)
                self.value = 0.0
                self.other_value = 0.0
                self.c.Register(self._UpdateBValue)

            def SetValue(self, value):
                self.value = value
                self.c(value)

            def _UpdateBValue(self, new_value):
                self.other_value = new_value / 0  # division by zero

        class B(object):
            c = Callback()

            def __init__(self, **ka):
                super().__init__(**ka)
                self._a = A()
                self.value = 0.0
                self.c.Register(self._UpdateAValue)

            def SetValue(self, value):
                self.value = value
                self.c(value * 0.1)

            def _UpdateAValue(self, new_value):
                self._a.SetValue(new_value)

        b = B()
        with pytest.raises(ZeroDivisionError):
            b.SetValue(5)
