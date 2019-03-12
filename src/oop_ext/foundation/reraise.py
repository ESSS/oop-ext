def Reraise(exception, message, separator="\n"):
    """
    Forwards to a `raise exc from cause` statement. Kept alive for backwards compatibility
    (`separator` argument only kept for this reason).
    """
    # Important: Don't create a local variable for the new exception otherwise we'll get a
    # cyclic reference between the exception and its traceback, meaning the traceback will
    # keep all frames (and their contents) alive.
    raise type(exception)(message) from exception
