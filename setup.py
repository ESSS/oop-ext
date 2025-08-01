#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""
import io
from setuptools import find_packages
from setuptools import setup

with io.open("README.rst", encoding="UTF-8") as readme_file:
    readme = readme_file.read()

with io.open("CHANGELOG.rst", encoding="UTF-8") as changelog_file:
    history = changelog_file.read()

requirements = ["attrs"]
extras_require = {
    "docs": ["sphinx >= 1.4", "sphinx_rtd_theme", "sphinx-autodoc-typehints"],
    "testing": [
        "codecov",
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pre-commit",
        "tox",
        "mypy",
    ],
}
setup(
    author="ESSS",
    author_email="foss@esss.co",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    description="OOP Extensions is a set of utilities for object oriented programming not found on Python's standard library.",
    extras_require=extras_require,
    install_requires=requirements,
    license="MIT license",
    long_description_content_type="text/x-rst",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    python_requires=">=3.10",
    keywords="oop_ext",
    name="oop-ext",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    url="http://github.com/ESSS/oop-ext",
    zip_safe=False,
)
