
import sys

import pytest

from oop_ext.foundation import handle_exception


@pytest.fixture
def captured_handled_exceptions():
    """
    Captures the exceptions using handle_exception module.
    """
    exceptions = []

    def _OnHandledException():
        info = sys.exc_info()
        exceptions.append(info)

    handle_exception.on_exception_handled.Register(_OnHandledException)
    yield exceptions
    handle_exception.on_exception_handled.Unregister(_OnHandledException)


# ===================================================================================================
# Test
# ===================================================================================================
class Test:
    @pytest.mark.qt_no_exception_capture(
        "need this mark because pytest-qt has its own exception capture mechanism, "
        'which is enabled when the job is running in "single-env" (ETK-1347)'
    )
    def testHandleException(
        self, captured_handled_exceptions, capfd, handled_exceptions
    ):
        try:
            raise RuntimeError("hey")
        except:
            handle_exception.HandleException("Test")
        assert len(captured_handled_exceptions) == 1

        stdout, stderr = capfd.readouterr()
        assert stdout == ""
        assert 'raise RuntimeError("hey")' in stderr

        handled_exceptions.ClearHandledExceptions()

    def testIgnoreHandleException(
        self, captured_handled_exceptions, capfd, handled_exceptions
    ):
        with handle_exception.IgnoringHandleException():
            try:
                raise RuntimeError()
            except:
                handle_exception.HandleException("Test")
            assert len(captured_handled_exceptions) == 1

        assert capfd.readouterr() == ("", "")
        handled_exceptions.ClearHandledExceptions()
