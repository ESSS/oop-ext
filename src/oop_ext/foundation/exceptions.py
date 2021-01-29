# mypy: disallow-untyped-defs
from typing import Optional


def ExceptionToUnicode(exception: Exception) -> str:
    """
    Python 3 exception handling already deals with string error messages. Here we
    will only append the original exception message to the returned message (this is automatically done in Python 2
    since the original exception message is added into the new exception while Python 3 keeps the original exception
    as a separated attribute
    """
    messages = []
    exc: Optional[BaseException] = exception
    while exc:
        messages.append(str(exc))
        exc = exc.__cause__ or exc.__context__
    return "\n".join(messages)
