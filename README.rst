======================================================================
OOP Extensions
======================================================================


.. image:: https://img.shields.io/pypi/v/oop-ext.svg
    :target: https://pypi.python.org/pypi/oop-ext

.. image:: https://img.shields.io/pypi/pyversions/oop-ext.svg
    :target: https://pypi.org/project/oop-ext

.. image:: https://img.shields.io/travis/ESSS/oop-ext.svg
    :target: https://travis-ci.org/ESSS/oop-ext

.. image:: https://ci.appveyor.com/api/projects/status/github/ESSS/oop-ext?branch=master
    :target: https://ci.appveyor.com/project/ESSS/oop-ext/?branch=master&svg=true

.. image:: https://codecov.io/gh/ESSS/oop-ext/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ESSS/oop-ext

.. image:: https://img.shields.io/readthedocs/pip.svg
    :target: https://oop-ext.readthedocs.io/en/latest/

What is OOP Extensions ?
================================================================================

OOP Extensions is a set of utilities for object oriented programming which is missing on Python core libraries.


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
