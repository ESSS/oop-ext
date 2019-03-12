
from .immutable import AsImmutable
from .odict import odict
from .types_ import Method
from .weak_ref import WeakMethodRef


# ===================================================================================================
# AbstractCachedMethod
# ===================================================================================================
class AbstractCachedMethod(Method):
    """
    Base class for cache-manager.
    The abstract class does not implement the storage of results.
    """

    def __init__(self, cached_method=None):
        # REMARKS: Use WeakMethodRef to avoid cyclic reference.
        self._method = WeakMethodRef(cached_method)
        self.enabled = True
        self.ResetCounters()

    def __call__(self, *args, **kwargs):
        key = self.GetCacheKey(*args, **kwargs)
        result = None

        if self.enabled and self._HasResult(key):
            self.hit_count += 1
            result = self._GetCacheResult(key, result)
        else:
            self.miss_count += 1
            result = self._CallMethod(*args, **kwargs)
            self._AddCacheResult(key, result)

        self.call_count += 1
        return result

    def _CallMethod(self, *args, **kwargs):
        return self._method()(*args, **kwargs)

    def GetCacheKey(self, *args, **kwargs):
        """
        Use the arguments to build the cache-key.
        """
        if args:
            if kwargs:
                return AsImmutable(args), AsImmutable(kwargs)

            return AsImmutable(args)

        if kwargs:
            return AsImmutable(kwargs)

    def _HasResult(self, key):
        raise NotImplementedError()

    def _AddCacheResult(self, key, result):
        raise NotImplementedError()

    def DoClear(self):
        raise NotImplementedError()

    def Clear(self):
        self.DoClear()
        self.ResetCounters()

    def ResetCounters(self):
        self.call_count = 0
        self.hit_count = 0
        self.miss_count = 0

    def _GetCacheResult(self, key, result):
        raise NotImplementedError()


# ===================================================================================================
# CachedMethod
# ===================================================================================================
class CachedMethod(AbstractCachedMethod):
    """
        Stores ALL the different results and never delete them.
    """

    def __init__(self, cached_method=None):
        super().__init__(cached_method)
        self._results = {}

    def _HasResult(self, key):
        return key in self._results

    def _AddCacheResult(self, key, result):
        self._results[key] = result

    def DoClear(self):
        self._results.clear()

    def _GetCacheResult(self, key, result):
        return self._results[key]


# ===================================================================================================
# ImmutableParamsCachedMethod
# ===================================================================================================
class ImmutableParamsCachedMethod(CachedMethod):
    """
    Expects all parameters to already be immutable
    Considers only the positional parameters of key, ignoring the keyword arguments
    """

    def GetCacheKey(self, *args, **kwargs):
        """
        Use the arguments to build the cache-key.
        """
        return args


# ===================================================================================================
# LastResultCachedMethod
# ===================================================================================================
class LastResultCachedMethod(AbstractCachedMethod):
    """
    A cache that stores only the last result.
    """

    def __init__(self, cached_method=None):
        super().__init__(cached_method)
        self._key = None
        self._result = None

    def _HasResult(self, key):
        return self._key == key

    def _AddCacheResult(self, key, result):
        self._key = key
        self._result = result

    def DoClear(self):
        self._key = None
        self._result = None

    def _GetCacheResult(self, key, result):
        return self._result


# ===================================================================================================
# AttributeBasedCachedMethod
# ===================================================================================================
class AttributeBasedCachedMethod(CachedMethod):
    """
    This cached method consider changes in object attributes
    """

    def __init__(self, cached_method, attr_name_list, cache_size=1, results=None):
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
            self._attr_name_list = attr_name_list
        self._cache_size = cache_size
        if results is None:
            self._results = odict()
        else:
            self._results = results

    def GetCacheKey(self, *args, **kwargs):
        instance = self._method().__self__
        for attr_name in self._attr_name_list:
            kwargs["_object_%s" % attr_name] = getattr(instance, attr_name)
        return AbstractCachedMethod.GetCacheKey(self, *args, **kwargs)

    def _AddCacheResult(self, key, result):
        CachedMethod._AddCacheResult(self, key, result)
        if len(self._results) > self._cache_size:
            key0 = next(iter(self._results))
            del self._results[key0]
