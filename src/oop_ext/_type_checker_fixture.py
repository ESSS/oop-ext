# mypy: disallow-untyped-defs
# mypy: disallow-any-decorated
import os
import re
from textwrap import dedent

import mypy.api
from pathlib import Path
from typing import List, Tuple

import attr
import pytest


@attr.s(auto_attribs=True)
class _Result:
    """
    Encapsulates the result of a call to ``mypy.api``, providing helpful functions to check
    that output.
    """

    output: Tuple[str, str, int]

    def assert_errors(self, messages: List[str]) -> None:
        assert self.error_report == ""
        lines = self.report_lines
        assert len(lines) == len(
            messages
        ), f"Expected {len(messages)} failures, got {len(lines)}:\n" + "\n".join(lines)
        for index, (obtained, expected) in enumerate(zip(lines, messages)):
            m = re.search(expected, obtained)
            assert m is not None, (
                f"Expected regex at index {index}:\n"
                f"  {expected}\n"
                f"did not match:\n"
                f"  {obtained}\n"
                f"(note: use re.escape() to escape regex special characters)"
            )

    def assert_ok(self) -> None:
        assert len(self.report_lines) == 0, "Expected no errors, got:\n " + "\n".join(
            self.report_lines
        )
        assert self.exit_status == 0

    @property
    def normal_report(self) -> str:
        return self.output[0]

    @property
    def error_report(self) -> str:
        return self.output[1]

    @property
    def exit_status(self) -> int:
        return self.output[2]

    @property
    def report_lines(self) -> List[str]:
        lines = [x.strip() for x in self.normal_report.split("\n") if x.strip()]
        # Drop last line (summary).
        return lines[:-1]


@attr.s(auto_attribs=True)
class TypeCheckerFixture:
    """
    Fixture to help running mypy in source code and checking for success/specific errors.

    This fixture is useful for libraries which provide type checking, allowing them
    to ensure the type support is working as intended.
    """

    path: Path
    request: pytest.FixtureRequest

    def make_file(self, source: str) -> None:
        name = self.request.node.name + ".py"
        self.path.joinpath(name).write_text(dedent(source))

    def run(self) -> _Result:
        # Change current directory so error messages show only the relative
        # path to the files.
        cwd = os.getcwd()
        try:
            os.chdir(self.path)
            x = mypy.api.run(["."])
            return _Result(x)
        finally:
            os.chdir(cwd)
