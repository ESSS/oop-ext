

# ===================================================================================================
# ExceptionToUnicode
# ===================================================================================================
def ExceptionToUnicode(exception):
    """
    Python 3 exception handling already deals with string error messages. Here we
    will only append the original exception message to the returned message (this is automatically done in Python 2
    since the original exception message is added into the new exception while Python 3 keeps the original exception
    as a separated attribute
    """
    messages = []
    while exception:
        messages.append(str(exception))
        exception = exception.__cause__ or exception.__context__
    return "\n".join(messages)
