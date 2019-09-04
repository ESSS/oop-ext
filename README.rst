======================================================================
OOP Extensions
======================================================================


.. image:: https://img.shields.io/pypi/v/oop-ext.svg
    :target: https://pypi.python.org/pypi/oop-ext

.. image:: https://img.shields.io/pypi/pyversions/oop-ext.svg
    :target: https://pypi.org/project/oop-ext

.. image:: https://img.shields.io/travis/ESSS/oop-ext.svg
    :target: https://travis-ci.com/ESSS/oop-ext

.. image:: https://ci.appveyor.com/api/projects/status/github/ESSS/oop-ext?branch=master
    :target: https://ci.appveyor.com/project/ESSS/oop-ext/?branch=master&svg=true

.. image:: https://codecov.io/gh/ESSS/oop-ext/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ESSS/oop-ext

.. image:: https://img.shields.io/readthedocs/pip.svg
    :target: https://oop-ext.readthedocs.io/en/latest/

What is OOP Extensions ?
================================================================================

OOP Extensions is a set of utilities for object oriented programming which is missing on Python core libraries.

Usage
================================================================================
``oop_ext`` brings a set of object oriented utilities, it supports the concept of interfaces,
abstract/overridable methods and more. ``oop_ext`` carefully checks that implementations
have the same method signatures as the interface it implements and raises exceptions otherwise.

Here's a simple example showing some nice features:

.. code-block:: python

    from oop_ext.interface import Interface, ImplementsInterface

    class IDisposable(Interface):
        def dispose(self):
            """
            Clears this object
            """
        def is_disposed(self) -> bool:
            """
            Returns True if the object has been cleared
            """


    @ImplementsInterface(IDisposable)
    class MyObject(Disposable):
        def __init__(self):
            super().__init__()
            self._data = [0] * 100
            self._is_disposed = False

        def is_disposed(self) -> bool:
            return self._is_disposed

        def dispose(self):
            self._is_disposed = True
            self._data = []


If any of the two methods in ``MyObject`` are not implemented or have differ signatures than
the ones declared in ``IDisposable``, the ``ImplementsInterface`` decorator will raise an
error during import.

Arbitrary objects can be verified if they implement a certain interface by using ``IsImplementation``:

.. code-block:: python

    from oop_ext.interface import IsImplementation

    my_object = MyObject()
    if IsImplementation(my_object, IDisposable):
        # my_object is guaranteed to implement IDisposable completely
        my_object.dispose()

Alternatively you can assert that an object implements the desired interface with ``AssertImplements``:

.. code-block:: python

    from oop_ext.interface import AssertImplements

    my_object = MyObject()
    AssertImplements(my_object, IDisposable)
    my_object.dispose()


Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to oop_ext, see the `contributing guidelines`_.

.. _contributing guidelines: https://github.com/ESSS/oop-ext/blob/master/CONTRIBUTING.rst


Release
-------
A reminder for the maintainers on how to make a new release.

Note that the VERSION should follow the semantic versioning as X.Y.Z
Ex.: v1.0.5

1. Create a ``release-VERSION`` branch from ``upstream/master``.
2. Update ``CHANGELOG.rst``.
3. Push a branch with the changes.
4. Once all builds pass, push a ``VERSION`` tag to ``upstream``.
5. Merge the PR.
