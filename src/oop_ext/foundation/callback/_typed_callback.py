# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
"""
Implement specializations of Callback and PriorityCallback which are type-checker friendly.

Each new Callback variant (Callback0, Callback1, Callback2, etc) subclasses ``Callback``, but
explicitly declare the signature of each method so it only accepts the correct number and type
of arguments of the declaration. Same for `PriorityCallback`.

Also, the method signatures are only seen by the type checker, so using one of the specialized
variants should have nearly zero runtime cost (only the cost of an empty subclass).

Implemented so far up to 5 arguments, more can be added if we think it is necessary.

Note the separate classes are needed for now, but after Python 3.11, we should be able to
implement the generic variants (`pep-0646 <https://www.python.org/dev/peps/pep-0646>`__) into ``Callback`` itself.
"""
from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar

from collections.abc import Callable
from collections.abc import Sequence

from ._callback import Callback
from ._callback import UnregisterContext
from ._priority_callback import PriorityCallback

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")


class Callback0(Callback):
    if TYPE_CHECKING:

        def __call__(self) -> None:  # type:ignore[override]
            ...

        def Register(
            self,
            func: Callable[[], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class Callback1(Callback, Generic[T1]):
    if TYPE_CHECKING:

        def __call__(self, v1: T1) -> None:  # type:ignore[override]
            ...

        def Register(
            self,
            func: Callable[[T1], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class Callback2(Callback, Generic[T1, T2]):
    if TYPE_CHECKING:

        def __call__(self, v1: T1, v2: T2) -> None:  # type:ignore[override]
            ...

        def Register(
            self,
            func: Callable[[T1, T2], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class Callback3(Callback, Generic[T1, T2, T3]):
    if TYPE_CHECKING:

        def __call__(self, v1: T1, v2: T2, v3: T3) -> None:  # type:ignore[override]
            ...

        def Register(
            self,
            func: Callable[[T1, T2, T3], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2, T3], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2, T3], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class Callback4(Callback, Generic[T1, T2, T3, T4]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1, v2: T2, v3: T3, v4: T4
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class Callback5(Callback, Generic[T1, T2, T3, T4, T5]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1, v2: T2, v3: T3, v4: T4, v5: T5
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1, T2, T3, T4, T5], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2, T3, T4, T5], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2, T3, T4, T5], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class PriorityCallback0(PriorityCallback):
    if TYPE_CHECKING:

        def __call__(self) -> None:  # type:ignore[override]
            ...

        def Register(
            self,
            func: Callable[[], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
            priority: int = 5,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class PriorityCallback1(PriorityCallback, Generic[T1]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
            priority: int = 5,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class PriorityCallback2(PriorityCallback, Generic[T1, T2]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1, v2: T2
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1, T2], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
            priority: int = 5,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class PriorityCallback3(PriorityCallback, Generic[T1, T2, T3]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1, v2: T2, v3: T3
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1, T2, T3], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
            priority: int = 5,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2, T3], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2, T3], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class PriorityCallback4(PriorityCallback, Generic[T1, T2, T3, T4]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1, v2: T2, v3: T3, v4: T4
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
            priority: int = 5,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...


class PriorityCallback5(PriorityCallback, Generic[T1, T2, T3, T4, T5]):
    if TYPE_CHECKING:

        def __call__(  # type:ignore[override]
            self, v1: T1, v2: T2, v3: T3, v4: T4, v5: T5
        ) -> None: ...

        def Register(
            self,
            func: Callable[[T1, T2, T2, T3, T4], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
            priority: int = 5,
        ) -> "UnregisterContext": ...

        def Unregister(
            self,
            func: Callable[[T1, T2, T3, T4, T5], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> None: ...

        def Contains(
            self,
            func: Callable[[T1, T2, T3, T4, T5], None],
            extra_args: Sequence[object] = Callback._EXTRA_ARGS_CONSTANT,
        ) -> bool: ...
