

# ===================================================================================================
# FunctionNotRegisteredError
# ===================================================================================================
class FunctionNotRegisteredError(RuntimeError):
    pass


# ===================================================================================================
# ErrorNotHandledInCallback
# ===================================================================================================
class ErrorNotHandledInCallback(RuntimeError):
    """
    This class identifies an error that should not be handled in the callback.
    """


# ===================================================================================================
# HandleErrorOnCallback
# ===================================================================================================
def HandleErrorOnCallback(func, *args, **kwargs):
    """
    Called when there's some error calling a callback.

    :param object func:
        The callback called.

    :param list args:
        The arguments passed to the callback.

    :param dict kwargs:
        The keyword arguments passed to the callback.
    """
    if hasattr(func, "func_code"):
        name, filename, line = (
            func.__code__.co_name,
            func.__code__.co_filename,
            func.__code__.co_firstlineno,
        )
        # Use default python trace format so that we have linking on pydev.
        func = '\n  File "{}", line {}, in {} (Called from Callback)\n'.format(
            filename, line, name
        )
    else:
        # That's ok, it may be that it's not really a method.
        func = "{}\n".format(repr(func))

    msg = "Error while trying to call {}".format(func)
    if args:
        msg += "Args: {}\n".format(args)
    if kwargs:
        msg += "Kwargs: {}\n".format(kwargs)

    from oop_ext.foundation import handle_exception

    handle_exception.HandleException(msg)
