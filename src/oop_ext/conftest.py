# mypy: disallow-untyped-defs
from typing import TYPE_CHECKING

import pytest
from pathlib import Path

if TYPE_CHECKING:
    from ._type_checker_fixture import TypeCheckerFixture


@pytest.fixture
def type_checker(
    request: pytest.FixtureRequest, tmp_path: Path
) -> "TypeCheckerFixture":
    """
    Fixture to help checking source code for type checking errors.

    Note: We plan to extract this to its own plugin.
    """
    from ._type_checker_fixture import TypeCheckerFixture

    return TypeCheckerFixture(tmp_path, request)
