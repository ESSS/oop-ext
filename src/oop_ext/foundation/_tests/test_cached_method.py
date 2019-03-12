
import pytest

from oop_ext.foundation.cached_method import (
    AttributeBasedCachedMethod,
    CachedMethod,
    LastResultCachedMethod,
)


def testCacheMethod(_cached_obj):
    cache = MyMethod = CachedMethod(_cached_obj.CachedMethod)

    MyMethod(1)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod(1)
    _cached_obj.CheckCounts(cache, hit=1)

    MyMethod(2)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod(2)
    _cached_obj.CheckCounts(cache, hit=1)

    # ALL results are stored, so these calls are HITs
    MyMethod(1)
    _cached_obj.CheckCounts(cache, hit=1)

    MyMethod(2)
    _cached_obj.CheckCounts(cache, hit=1)


def testCacheMethodEnabled(_cached_obj):
    cache = MyMethod = CachedMethod(_cached_obj.CachedMethod)

    MyMethod(1)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod(1)
    _cached_obj.CheckCounts(cache, hit=1)

    MyMethod.enabled = False

    MyMethod(1)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod.enabled = True

    MyMethod(1)
    _cached_obj.CheckCounts(cache, hit=1)


def testCacheMethodLastResultCachedMethod(_cached_obj):
    cache = MyMethod = LastResultCachedMethod(_cached_obj.CachedMethod)

    MyMethod(1)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod(1)
    _cached_obj.CheckCounts(cache, hit=1)

    MyMethod(2)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod(2)
    _cached_obj.CheckCounts(cache, hit=1)

    # Only the LAST result is stored, so this call is a MISS.
    MyMethod(1)
    _cached_obj.CheckCounts(cache, method=1, miss=1)


def testCacheMethodObjectInKey(_cached_obj):
    cache = MyMethod = CachedMethod(_cached_obj.CachedMethod)

    class MyObject:
        def __init__(self):
            self.name = "alpha"
            self.id = 1

        def __str__(self):
            return "%s %d" % (self.name, self.id)

    alpha = MyObject()

    MyMethod(alpha)
    _cached_obj.CheckCounts(cache, method=1, miss=1)

    MyMethod(alpha)
    _cached_obj.CheckCounts(cache, hit=1)

    alpha.name = "bravo"
    alpha.id = 2

    MyMethod(alpha)
    _cached_obj.CheckCounts(cache, method=1, miss=1)


def testCacheMethodAttributeBasedCachedMethod():
    class TestObject:
        def __init__(self):
            self.name = "alpha"
            self.id = 1
            self.n_calls = 0

        def Foo(self, par):
            self.n_calls += 1
            return "%s %d" % (par, self.id)

    alpha = TestObject()
    alpha.Foo = AttributeBasedCachedMethod(alpha.Foo, "id", cache_size=3)
    alpha.Foo("test1")
    alpha.Foo("test1")

    assert alpha.n_calls == 1

    alpha.Foo("test2")
    assert alpha.n_calls == 2
    assert len(alpha.Foo._results) == 2

    alpha.id = 3
    alpha.Foo("test2")
    assert alpha.n_calls == 3

    assert len(alpha.Foo._results) == 3

    alpha.Foo("test3")
    assert alpha.n_calls == 4
    assert len(alpha.Foo._results) == 3


@pytest.fixture
def _cached_obj():
    """
    A test_object common to many cached_method tests.
    """

    class TestObj:
        def __init__(self):
            self.method_count = 0

        def CachedMethod(self, *args, **kwargs):
            self.method_count += 1
            return self.method_count

        def CheckCounts(self, cache, method=0, miss=0, hit=0):

            if not hasattr(cache, "check_counts"):
                cache.check_counts = dict(method=0, miss=0, hit=0, call=0)

            cache.check_counts["method"] += method
            cache.check_counts["miss"] += miss
            cache.check_counts["hit"] += hit
            cache.check_counts["call"] += miss + hit

            assert self.method_count == cache.check_counts["method"]
            assert cache.miss_count == cache.check_counts["miss"]
            assert cache.hit_count == cache.check_counts["hit"]
            assert cache.call_count == cache.check_counts["call"]

    return TestObj()
