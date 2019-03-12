
from oop_ext.foundation.types_ import Method


# ===================================================================================================
# _CallbackWrapper
# ===================================================================================================
class _CallbackWrapper(Method):
    def __init__(self, weak_method_callback):
        self.weak_method_callback = weak_method_callback

        # Maintaining the OriginalMethod() interface that clients expect.
        self.OriginalMethod = weak_method_callback

    def __call__(self, sender, *args, **kwargs):
        c = self.weak_method_callback()
        if c is None:
            raise ReferenceError(
                "This should never happen: The sender already died, so, "
                "how can this method still be called?"
            )
        c(sender(), *args, **kwargs)
