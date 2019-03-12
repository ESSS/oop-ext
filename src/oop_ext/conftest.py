import pytest


class _ShowHandledExceptionsError:
    """
    Helper class to deal with handled exceptions.
    """

    def __init__(self):
        self._handled_exceptions = []
        self._handled_exceptions_types = []

    def _OnHandledException(self):
        """
        Called when a handled exceptions was found.
        """
        import traceback
        from io import StringIO

        s = StringIO()
        traceback.print_exc(file=s)
        self._handled_exceptions_types.append(sys.exc_info()[0])
        self._handled_exceptions.append(s.getvalue())

    def __enter__(self, *args, **kwargs):
        from oop_ext.foundation import handle_exception

        handle_exception.on_exception_handled.Register(self._OnHandledException)
        return self

    def __exit__(self, *args, **kwargs):
        from oop_ext.foundation import handle_exception

        handle_exception.on_exception_handled.Unregister(self._OnHandledException)

    def ClearHandledExceptions(self):
        """
        Clears the handled exceptions
        """
        del self._handled_exceptions_types[:]
        del self._handled_exceptions[:]

    def GetHandledExceptionTypes(self):
        """
        :return list(type):
            Returns a list with the exception types we found.
        """
        return self._handled_exceptions_types

    def GetHandledExceptions(self):
        """
        :return list(str):
            Returns a list with the representation of the handled exceptions.
        """
        return self._handled_exceptions

    def RaiseFoundExceptions(self):
        """
        Raises error for the handled exceptions found.
        """

        def ToString(s):
            if not isinstance(s, str):
                s = s.decode("utf-8", "replace")
            return s

        if self._handled_exceptions:
            raise AssertionError(
                "\n".join(ToString(i) for i in self._handled_exceptions)
            )


@pytest.yield_fixture(scope="function", autouse=True)
def handled_exceptions():
    """
    This method will be called for all the functions automatically.

    For users which expect handled exceptions, it's possible to declare the fixture and
    say that the errors are expected and clear them later.

    I.e.:

    from oop_ext.foundation.handle_exception import IgnoringHandleException
    from oop_ext.foundation import handle_exception

    def testSomething(handled_exceptions):
        with IgnoringHandleException():
            try:
                raise RuntimeError('test')
            except:
                handle_exception.HandleException()

        # Check that they're there...
        assert len(handled_exceptions.GetHandledExceptions()) == 1

        # Clear them
        handled_exceptions.ClearHandledExceptions()

    Note that test-cases can still deal with this API without using a fixture by importing handled_exceptions
    and using it as an object.

    I.e.:

    from oop_ext.fixtures import handled_exceptions
    handled_exceptions.GetHandledExceptions()
    handled_exceptions.ClearHandledExceptions()
    """
    try:
        with _ShowHandledExceptionsError() as show_handled_exceptions_error:
            handled_exceptions.ClearHandledExceptions = (
                show_handled_exceptions_error.ClearHandledExceptions
            )

            handled_exceptions.GetHandledExceptions = (
                show_handled_exceptions_error.GetHandledExceptions
            )

            handled_exceptions.GetHandledExceptionTypes = (
                show_handled_exceptions_error.GetHandledExceptionTypes
            )

            yield show_handled_exceptions_error
    finally:
        handled_exceptions.ClearHandledExceptions = None
        handled_exceptions.GetHandledExceptions = None
        handled_exceptions.GetHandledExceptionTypes = None

    show_handled_exceptions_error.RaiseFoundExceptions()
