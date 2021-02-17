# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
from typing import Callable, Any, Tuple

from oop_ext.foundation.decorators import Override
from oop_ext.foundation.odict import odict

from ._callback import Callback


class PriorityCallback(Callback):
    """
    Class that's able to give a priority to the added callbacks when they're registered.
    """

    INFO_POS_PRIORITY = 3

    @Override(Callback._GetInfo)
    def _GetInfo(  # type:ignore[misc, override]
        self, func: Callable, priority: int
    ) -> Any:
        """
        Overridden to add the priority to the info.

        :param priority:
            The priority to be set to the added callback.
        """
        info = Callback._GetInfo(self, func)
        return info + (priority,)

    @Override(Callback.Register)
    def Register(  # type:ignore[misc, override]
        self,
        func: Callable,
        extra_args: Tuple[object, ...] = Callback._EXTRA_ARGS_CONSTANT,
        priority: int = 5,
    ) -> None:
        """
        Register a function in the callback.
        :param object func:
            Method or function that will be called later.

        :param int priority:
            If passed, it'll be be used to put the callback into the correct place based on the
            priority passed (lower numbers have higher priority).
        """
        if extra_args is not self._EXTRA_ARGS_CONSTANT:
            extra_args = tuple(extra_args)

        key = self._GetKey(func)
        try:
            callbacks = self._callbacks
        except AttributeError:
            callbacks = self._callbacks = odict()

        callbacks.pop(key, None)  # Remove if it exists
        new_info = self._GetInfo(func, priority)

        i = 0
        for i, (info, _extra) in enumerate(callbacks.values()):
            if info[self.INFO_POS_PRIORITY] > priority:
                break
        else:
            # Iterated all... so, go one more the last position.
            i += 1

        callbacks.insert(i, key, (new_info, extra_args))
