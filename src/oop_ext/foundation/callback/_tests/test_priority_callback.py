from oop_ext.foundation.callback import PriorityCallback0


def testPriorityCallback() -> None:
    priority_callback = PriorityCallback0()

    called = []

    def OnCall1():
        called.append(1)

    def OnCall2():
        called.append(2)

    def OnCall3():
        called.append(3)

    def OnCall4():
        called.append(4)

    def OnCall5():
        called.append(5)

    priority_callback.Register(OnCall1, priority=2)
    priority_callback.Register(OnCall2, priority=2)
    priority_callback.Register(OnCall3, priority=1)
    priority_callback.Register(OnCall4, priority=3)
    unregister5 = priority_callback.Register(OnCall5, priority=2)

    priority_callback()
    assert called == [3, 1, 2, 5, 4]

    called.clear()
    unregister5.Unregister()
    priority_callback()
    assert called == [3, 1, 2, 4]
