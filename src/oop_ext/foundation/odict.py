# mypy: disallow-untyped-defs
import collections
from typing import Any, Iterable, Hashable, Union


class odict(collections.OrderedDict):
    def insert(
        self,
        index: int,
        key: Hashable,
        value: Any,
        dict_setitem: Any = dict.__setitem__,
    ) -> None:
        """
        Convenience method to have same interface as `ruamel.ordereddict`, which as traditionally
        used on Python 2.
        """
        self[key] = value
        # Determine which direction is cheaper to move items first. If new item is more to the left
        # of center, move items to its left to first, otherwise it is cheaper to move items to
        # right to last.
        #
        # Note that `move_to_end` is a O(1) operation that just swaps endpoints of underlying
        # double linked list maintained by C-extension ordered dict.
        moved: Iterable[Any]
        if (len(self) - index) <= (len(self) // 2):
            moved = [k for i, k in enumerate(self.keys()) if i >= index and k != key]
            last = True
        else:
            moved = reversed(
                [k for i, k in enumerate(self.keys()) if i < index or k == key]
            )

            last = False
        for k in moved:
            self.move_to_end(k, last=last)

    def __delitem__(self, key: Union[Hashable, slice]) -> None:
        if isinstance(key, slice):
            # Properly deal with slices (based on order).
            keys = list(self.keys())
            for k in keys[key]:
                collections.OrderedDict.__delitem__(self, k)

        else:
            collections.OrderedDict.__delitem__(self, key)
