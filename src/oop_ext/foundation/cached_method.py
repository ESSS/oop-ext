# mypy: disallow-untyped-defs
from abc import abstractmethod
from typing import (
    Generic,
    TypeVar,
    Callable,
    Hashable,
    Optional,
    Dict,
    Sequence,
    Union,
    cast,
)

from .immutable import AsImmutable
from .odict import odict
from .types_ import Method
from .weak_ref import WeakMethodRef


ResultType = TypeVar("ResultType")


class AbstractCachedMethod(Method, Generic[ResultType]):
    """
    Base class for cache-manager.
    The abstract class does not implement the storage of results.
    """

    def __init__(self, cached_method: Callable[..., ResultType]) -> None:
        # Using WeakMethodRef to avoid cyclic reference.
        self._method = WeakMethodRef(cached_method)
        self.enabled = True
        self.ResetCounters()

    def __call__(self, *args: object, **kwargs: object) -> ResultType:
        key = self.GetCacheKey(*args, **kwargs)

        if self.enabled and self._HasResult(key):
            self.hit_count += 1
            result = self._GetCacheResult(key, cast(ResultType, None))
        else:
            self.miss_count += 1
            result = self._CallMethod(*args, **kwargs)
            self._AddCacheResult(key, result)

        self.call_count += 1
        return result

    def _CallMethod(self, *args: object, **kwargs: object) -> ResultType:
        return self._method()(*args, **kwargs)

    def GetCacheKey(self, *args: object, **kwargs: object) -> Hashable:
        """
        Use the arguments to build the cache-key.
        """
        if args:
            if kwargs:
                return AsImmutable(args), AsImmutable(kwargs)

            return AsImmutable(args)

        if kwargs:
            return AsImmutable(kwargs)

        return None

    @abstractmethod
    def _HasResult(self, key: Hashable) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _AddCacheResult(self, key: Hashable, result: ResultType) -> None:
        raise NotImplementedError()

    @abstractmethod
    def DoClear(self) -> None:
        raise NotImplementedError()

    def Clear(self) -> None:
        self.DoClear()
        self.ResetCounters()

    def ResetCounters(self) -> None:
        self.call_count = 0
        self.hit_count = 0
        self.miss_count = 0

    @abstractmethod
    def _GetCacheResult(self, key: Hashable, result: ResultType) -> ResultType:
        raise NotImplementedError()


class CachedMethod(AbstractCachedMethod, Generic[ResultType]):
    """
    Stores ALL the different results and never delete them.
    """

    def __init__(self, cached_method: Callable[..., ResultType]) -> None:
        super().__init__(cached_method)
        self._results: Dict[Hashable, ResultType] = {}

    def _HasResult(self, key: Hashable) -> bool:
        return key in self._results

    def _AddCacheResult(self, key: Hashable, result: ResultType) -> None:
        self._results[key] = result

    def DoClear(self) -> None:
        self._results.clear()

    def _GetCacheResult(self, key: Hashable, result: ResultType) -> ResultType:
        return self._results[key]


class ImmutableParamsCachedMethod(CachedMethod, Generic[ResultType]):
    """
    Expects all parameters to already be immutable
    Considers only the positional parameters of key, ignoring the keyword arguments
    """

    def GetCacheKey(self, *args: object, **kwargs: object) -> Hashable:
        """
        Use the arguments to build the cache-key.
        """
        return args


class LastResultCachedMethod(AbstractCachedMethod, Generic[ResultType]):
    """
    A cache that stores only the last result.
    """

    def __init__(self, cached_method: Callable[..., ResultType]) -> None:
        super().__init__(cached_method)
        self._key: Optional[object] = None
        self._result: Optional[ResultType] = None

    def _HasResult(self, key: Hashable) -> bool:
        return self._key == key

    def _AddCacheResult(self, key: Hashable, result: ResultType) -> None:
        self._key = key
        self._result = result

    def DoClear(self) -> None:
        self._key = None
        self._result = None

    def _GetCacheResult(self, key: Hashable, result: ResultType) -> ResultType:
        # This could return None (_result is Optional), but not doing an assert
        # here to avoid breaking code.
        return self._result  # type:ignore[return-value]


class AttributeBasedCachedMethod(CachedMethod, Generic[ResultType]):
    """
    This cached method consider changes in object attributes
    """

    def __init__(
        self,
        cached_method: Callable[..., ResultType],
        attr_name_list: Union[str, Sequence[str]],
        cache_size: int = 1,
        results: Optional[odict] = None,
    ):
        """
        :type cached_method: bound method to be cached
        :param cached_method:
        :type attr_name_list: attr names in a C{str} separated by spaces OR in a sequence of C{str}
        :param attr_name_list:
        :type cache_size: the cache size
        :param cache_size:
        :type results: an optional ref. to an C{odict} for keep cache results
        :param results:
        """
        CachedMethod.__init__(self, cached_method)
        if isinstance(attr_name_list, str):
            self._attr_name_list = attr_name_list.split()
        else:
            self._attr_name_list = list(attr_name_list)
        self._cache_size = cache_size
        if results is None:
            self._results = odict()
        else:
            self._results = results

    def GetCacheKey(self, *args: object, **kwargs: object) -> Hashable:
        instance = self._method().__self__
        for attr_name in self._attr_name_list:
            kwargs["_object_%s" % attr_name] = getattr(instance, attr_name)
        return super().GetCacheKey(*args, **kwargs)

    def _AddCacheResult(self, key: Hashable, result: ResultType) -> None:
        super()._AddCacheResult(key, result)
        if len(self._results) > self._cache_size:
            key0 = next(iter(self._results))
            del self._results[key0]
