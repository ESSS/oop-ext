#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import io
from setuptools import find_packages, setup

with io.open("README.rst", encoding="UTF-8") as readme_file:
    readme = readme_file.read()

with io.open("CHANGELOG.rst", encoding="UTF-8") as changelog_file:
    history = changelog_file.read()

requirements = []
extras_require = {
    "docs": ["sphinx >= 1.4", "sphinx_rtd_theme", "sphinx-autodoc-typehints"],
    "testing": ["codecov", "pytest", "pytest-cov", "pytest-mock", "pre-commit", "tox"],
}
setup(
    author="ESSS",
    author_email="foss@esss.co",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="OOP Extensions is a set of utilities for object oriented programming which is missing on Python core libraries.",
    extras_require=extras_require,
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    python_requires=">=3.6",
    keywords="oop_ext",
    name="oop-ext",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    url="http://github.com/ESSS/oop-ext",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    zip_safe=False,
)
