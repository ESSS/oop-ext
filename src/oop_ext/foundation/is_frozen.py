"""
frozen
Setup the sys.frozen attribute when the application is not in release mode.
This attribute is automatically set when the source code is in an executable.

Use "IsFrozen" instead of "sys.frozen == False" because some libraries (pywin32) checks for the
attribute existence, not the value.
"""
import sys

_is_frozen = hasattr(sys, "frozen") and getattr(sys, "frozen")


def IsFrozen() -> bool:
    """
    Returns true if the code is frozen, that is, the code is inside a generated executable.

    Frozen == False means the we are running the code using Python interpreter, usually associated with the code being
    in development.
    """
    return _is_frozen


def SetIsFrozen(is_frozen: bool) -> bool:
    """
    Sets the is_frozen value manually, overriding the "calculated" value.

    :param bool is_frozen:
        The new value for is_frozen.

    :returns bool:
        Returns the original value, before the given value is set.
    """
    global _is_frozen
    try:
        return _is_frozen
    finally:
        _is_frozen = is_frozen


_is_development = not _is_frozen


def IsDevelopment() -> bool:
    """
    This function is used to indentify if we're in a development environment or production
    environment.

    :return bool:
        Returns True if we're in a development environment or False if we're in a production
        environment.

        By default, the "development environment" is understood as not in frozen mode. However, be
        careful not think that this will always be equivalent to 'not IsFrozen()'. This could also
        return True in frozen environment, particularly when running tests on the executable.

        ..seealso:: SetIsDevelopment to understand why.
    """
    return _is_development


def SetIsDevelopment(is_development: bool) -> bool:
    """
    :param bool is_development:
        The new is-development value, which is returned by ..seealso:: IsDevelopment.

    :return bool:
        The previous value of is-development property.

    We wanted this method for the following reason:
    Some methods we use in our codebase can make some checks/assertions that might be overly time-consuming to
    have them running in production code. Therefore, the helper IsDevelopment is used to know if those methods
    should run or not. However, due to the fact that we run tests on the executable and we want those methods
    to be executed during testing, we need this method to make sure IsDevelopment returns true even in "frozen
    environment".

    DevelopmentCheckType is an example of a method using IsDevelopment to be enabled.

    So always mind this difference and think.
    """
    global _is_development
    try:
        return _is_development
    finally:
        _is_development = is_development
