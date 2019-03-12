
import inspect
import weakref
from types import LambdaType, MethodType

from oop_ext.foundation.decorators import Implements


# ===================================================================================================
# WeakList
# ===================================================================================================
class WeakList:
    """
    The weak list is a list that will only keep weak-references to objects passed to it.

    When iterating the actual objects are used, but internally, only weakrefs are kept.

    It does not contain the whole list interface (but can be extended as needed).

    IMPORTANT: if you got here and need to implement a new feature or fix a bug,
        consider replacing this implementation by this one instead:
        https://github.com/apieum/weakreflist
    """

    def __init__(self, initlist=None):
        self.data = []

        if initlist is not None:
            for x in initlist:
                self.append(x)

    @Implements(list.append)
    def append(self, item):
        self.data.append(GetWeakRef(item))

    @Implements(list.extend)
    def extend(self, lst):
        for o in lst:
            self.append(o)

    def __iter__(self):
        # iterate in a copy
        for ref in self.data[:]:
            d = ref()
            if d is None:
                self.data.remove(ref)
            else:
                yield d

    def remove(self, item):
        """
        Remove first occurrence of a value.

        It differs from the normal version because it will not raise an exception if the
        item is not found (because it may be garbage-collected already).

        :param object item:
            The object to be removed.
        """
        # iterate in a copy
        for ref in self.data[:]:
            d = ref()

            if d is None:
                self.data.remove(ref)

            elif d == item:
                self.data.remove(ref)
                break

    def __len__(self):
        i = 0
        for _k in self:  # we make an iteration to remove dead references...
            i += 1
        return i

    def __delitem__(self, i):
        self.data.__delitem__(i)

    def __getitem__(self, i):
        if isinstance(i, slice):
            slice_ = []
            for ref in self.data[i.start : i.stop : i.step]:
                d = ref()
                if d is not None:
                    slice_.append(d)

            return WeakList(slice_)
        else:
            return self.data[i]()

    def __setitem__(self, i, item):
        """
        Set a weakref of item on the ith position
        """
        self.data[i] = GetWeakRef(item)

    def __str__(self):
        return "\n".join(str(x) for x in self)


# ===================================================================================================
# WeakMethodRef
# ===================================================================================================
class WeakMethodRef:
    """
        Weak reference to bound-methods. This allows the client to hold a bound method
        while allowing GC to work.

        Based on recipe from Python Cookbook, page 191. Differs by only working on
        boundmethods and returning a true boundmethod in the __call__() function.

        Keeps a reference to an object but doesn't prevent that object from being garbage collected.
    """

    __slots__ = ["_obj", "_func", "_class", "_hash", "__weakref__"]

    def __init__(self, method):
        try:
            if method.__self__ is not None:
                # bound method
                self._obj = weakref.ref(method.__self__)
            else:
                # unbound method
                self._obj = None
            self._func = method.__func__
            self._class = method.__self__.__class__
        except AttributeError:
            # not a method -- a callable: create a strong reference (the CallbackWrapper
            # is depending on this behaviour... is it correct?)
            self._obj = None
            self._func = method
            self._class = None

    def __call__(self):
        """
            Return a new bound-method like the original, or the original function if refers just to
            a function or unbound method.

            @return:
                None if the original object doesn't exist anymore.
        """
        if self.is_dead():
            return None
        if self._obj is not None:
            # we have an instance: return a bound method
            return MethodType(self._func, self._obj())
        else:
            # we don't have an instance: return just the function
            return self._func

    def is_dead(self):
        """Returns True if the referenced callable was a bound method and
        the instance no longer exists. Otherwise, return False.
        """
        return self._obj is not None and self._obj() is None

    def __eq__(self, other):
        try:
            return type(self) is type(other) and self() == other()
        except:
            return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        if not hasattr(self, "_hash"):
            # The hash should be immutable (must be calculated once and never changed -- otherwise
            # we won't be able to get it when the object dies)
            self._hash = hash(WeakMethodRef.__call__(self))

        return self._hash

    def __repr__(self):
        func_name = getattr(self._func, "__name__", str(self._func))
        if self._obj is not None:
            obj = self._obj()
            if obj is None:
                obj_str = "<dead>"
            else:
                obj_str = "%X" % id(obj)
            msg = "<WeakMethodRef to %s.%s for object %s>"
            return msg % (self._class.__name__, func_name, obj_str)
        else:
            return "<WeakMethodRef to %s>" % func_name


# ===================================================================================================
# WeakMethodProxy
# ===================================================================================================
class WeakMethodProxy(WeakMethodRef):
    """
        Like ref, but calling it will cause the referent method to be called with the same
        arguments. If the referent's object no longer lives, ReferenceError is raised.
    """

    def GetWrappedFunction(self):
        return WeakMethodRef.__call__(self)

    def __call__(self, *args, **kwargs):
        func = WeakMethodRef.__call__(self)
        if func is None:
            raise ReferenceError("Object is dead. Was of class: {}".format(self._class))
        else:
            return func(*args, **kwargs)

    def __eq__(self, other):
        try:
            func1 = WeakMethodRef.__call__(self)
            func2 = WeakMethodRef.__call__(other)
            return type(self) == type(other) and func1 == func2
        except:
            return False


# ===================================================================================================
# WeakSet
# ===================================================================================================
class WeakSet:
    """
    Just like `weakref.WeakSet`, but supports adding methods (the standard `weakref.WeakSet` can't
    add methods, this feature comes from `oop_ext.foundation.weak_ref.GetWeakRef`, see `testWeakSet2`).

    It does not contain the whole set interface (but can be extended as needed).

    ..see:: oop_ext.foundation.weak_ref.GetWeakRef
    ..see:: weakref.WeakSet
    """

    def __init__(self):
        self.data = set()

    def add(self, item):
        self.data.add(GetWeakRef(item))

    def clear(self):
        self.data.clear()

    def __iter__(self):
        # iterate in a copy
        for ref in self.data.copy():
            d = ref()
            if d is None:
                self.data.remove(ref)
            else:
                yield d

    def remove(self, item):
        """
        Remove an item from the available data.

        :param object item:
            The object to be removed.
        """
        self.data.remove(GetWeakRef(item))

    def union(self, another_set):
        result = WeakSet()
        result.data = self.data.copy()
        for i in another_set:
            result.add(i)
        return result

    def __sub__(self, another_set):
        result = WeakSet()
        result.data = self.data.copy()
        for i in another_set:
            result.discard(i)
        return result

    def __rsub__(self, another_set):
        result = another_set.copy()
        for i in self:
            result.discard(i)
        return result

    def discard(self, item):
        try:
            self.remove(item)
        except KeyError:
            pass

    def __len__(self):
        i = 0
        for _k in self:  # we make an iteration to remove dead references...
            i += 1
        return i

    def __str__(self):
        return "\n".join(str(x) for x in self)


# ===================================================================================================
# IsWeakProxy
# ===================================================================================================
def IsWeakProxy(obj):
    """
    Returns whether the given object is a weak-proxy
    """
    return isinstance(obj, (weakref.ProxyType, WeakMethodProxy))


# ===================================================================================================
# IsWeakRef
# ===================================================================================================
def IsWeakRef(obj):
    """
        Returns wheter ths given object is a weak-reference.
    """
    return isinstance(obj, (weakref.ReferenceType, WeakMethodRef)) and not isinstance(
        obj, WeakMethodProxy
    )


# ===================================================================================================
# IsWeakObj
# ===================================================================================================
def IsWeakObj(obj):
    """
    Returns whether the given object is a weak object. Either a weak-proxy or a weak-reference.

    :param  obj: The object that may be a weak reference or proxy
    :return bool: True if it is a proxy or a weak reference.
    """
    return IsWeakProxy(obj) or IsWeakRef(obj)


# ===================================================================================================
# GetRealObj
# ===================================================================================================
def GetRealObj(obj):
    """
    Returns the real-object from a weakref, or the object itself otherwise.
    """
    if IsWeakRef(obj):
        return obj()
    if isinstance(obj, LambdaType):
        return obj()
    return obj


# ===================================================================================================
# GetWeakProxy
# ===================================================================================================
def GetWeakProxy(obj):
    """
    :param obj: This is the object we want to get as a proxy
    :return:
        Returns the object as a proxy (if it is still not already a proxy or a weak ref, in which case the passed object
        is returned itself)
    """
    if obj is None:
        return None

    if not IsWeakProxy(obj):

        if IsWeakRef(obj):
            obj = obj()

        # for methods we cannot create regular weak-refs
        if inspect.ismethod(obj):
            return WeakMethodProxy(obj)

        return weakref.proxy(obj)

    return obj


# Keep the same lambda for weak-refs (to be reused among all places that use GetWeakRef(None)
_EMPTY_LAMBDA = lambda: None


# ===================================================================================================
# GetWeakRef
# ===================================================================================================
def GetWeakRef(obj):
    """
    :type obj: this is the object we want to get as a weak ref
    :param obj:
    @return the object as a proxy (if it is still not already a proxy or a weak ref, in which case the passed
                                   object is returned itself)
    """
    if obj is None:
        return _EMPTY_LAMBDA

    if IsWeakProxy(obj):
        raise RuntimeError("Unable to get weak ref for proxy.")

    if not IsWeakRef(obj):

        # for methods we cannot create regular weak-refs
        if inspect.ismethod(obj):
            return WeakMethodRef(obj)

        return weakref.ref(obj)
    return obj


# ===================================================================================================
# IsSame
# ===================================================================================================
def IsSame(o1, o2):
    """
        This checks for the identity even if one of the parameters is a weak reference

        :param  o1:
            first object to compare

        :param  o2:
            second object to compare

        @raise
            RuntimeError if both of the passed parameters are weak references
    """
    # get rid of weak refs (we only need special treatment for proxys)
    if IsWeakRef(o1):
        o1 = o1()
    if IsWeakRef(o2):
        o2 = o2()

    # simple case (no weak objects)
    if not IsWeakObj(o1) and not IsWeakObj(o2):
        return o1 is o2

    # all weak proxys
    if IsWeakProxy(o1) and IsWeakProxy(o2):
        if not o1 == o2:
            # if they are not equal, we know they're not the same
            return False

        # but we cannot say anything if they are the same if they are equal
        raise ReferenceError(
            "Cannot check if object is same if both arguments passed are weak objects"
        )

    # one is weak and the other is not
    if IsWeakObj(o1):
        weak = o1
        original = o2
    else:
        weak = o2
        original = o1

    weaks = weakref.getweakrefs(original)
    for w in weaks:
        if w is weak:  # check the weak object identity
            return True

    return False
