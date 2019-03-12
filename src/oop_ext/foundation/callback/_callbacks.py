
from ._shortcuts import After, Before, Remove


# ===================================================================================================
# Callbacks
# ===================================================================================================
class Callbacks:
    """
    Holds created callbacks, making it easy to disconnect later.

    Note: keeps a strong reference to the callback and the sender, thus, they won't be garbage-
    collected while still connected in this case.
    """

    def __init__(self):
        self._callbacks = []

    def Before(self, sender, *callbacks, **kwargs):
        sender = Before(sender, *callbacks, **kwargs)
        for callback in callbacks:
            self._callbacks.append((sender, callback))
        return sender

    def After(self, sender, *callbacks, **kwargs):
        sender = After(sender, *callbacks, **kwargs)
        for callback in callbacks:
            self._callbacks.append((sender, callback))
        return sender

    def RemoveAll(self):
        for sender, callback in self._callbacks:
            Remove(sender, callback)
        self._callbacks[:] = []
