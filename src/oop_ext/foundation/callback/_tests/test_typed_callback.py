import re
from typing import Tuple

import pytest

from oop_ext._type_checker_fixture import TypeCheckerFixture


def testCallback0(type_checker: TypeCheckerFixture) -> None:
    type_checker.make_file(
        """
        from oop_ext.foundation.callback import Callback0

        c = Callback0()
        c(10)

        def fail(x): pass
        c.Register(fail)
        """
    )
    result = type_checker.run()
    result.assert_errors(
        [
            'Too many arguments for "__call__"',
            re.escape('incompatible type "Callable[[Any], Any]"'),
        ]
    )

    type_checker.make_file(
        """
        from oop_ext.foundation.callback import Callback0

        c = Callback0()
        c()

        def ok(): pass
        c.Register(ok)
        """
    )
    result = type_checker.run()
    result.assert_ok()


def testCallback1(type_checker: TypeCheckerFixture) -> None:
    type_checker.make_file(
        """
        from oop_ext.foundation.callback import Callback1

        c = Callback1[int]()
        c()
        c(10, 10)

        def fail(): pass
        c.Register(fail)

        def fail2(x: str): pass
        c.Register(fail2)
        """
    )
    result = type_checker.run()
    result.assert_errors(
        [
            "Missing positional argument",
            'Too many arguments for "__call__" of "Callback1"',
            re.escape(
                'Argument 1 to "Register" of "Callback1" has incompatible type "Callable[[], Any]"'
            ),
            re.escape(
                'Argument 1 to "Register" of "Callback1" has incompatible type "Callable[[str], Any]"'
            ),
        ]
    )

    type_checker.make_file(
        """
        from oop_ext.foundation.callback import Callback1

        c = Callback1[int]()
        c(10)

        def ok(x: int): pass
        c.Register(ok)
        """
    )
    result = type_checker.run()
    result.assert_ok()


@pytest.mark.parametrize("args_count", [1, 2, 3, 4, 5])
def testAllCallbacksSmokeTest(
    args_count: int, type_checker: TypeCheckerFixture
) -> None:
    """
    Parametrized test to do basic checking over all Callbacks (except Callback0).

    We generate functions with too much arguments, too few, and correct number, and check
    that the errors are as expected.

    This should be enough to catch copy/paste errors when declaring the
    Callback overloads.
    """

    def gen_signature_and_args(count: int) -> Tuple[str, str, str]:
        # Generates "v1: int, v2: int" etc
        signature = ", ".join(f"v{i}: int" for i in range(count))
        # Generates "10, 20" etc
        args = ", ".join(f"{i+1}0" for i in range(count))
        # Generates "int, int" etc
        types = ", ".join("int" for _ in range(count))
        return signature, args, types

    sig_too_few, args_too_few, types_too_few = gen_signature_and_args(args_count - 1)
    sig_too_many, args_too_many, types_too_many = gen_signature_and_args(args_count + 1)
    sig_ok, args_ok, types_ok = gen_signature_and_args(args_count)

    type_checker.make_file(
        f"""
        from oop_ext.foundation.callback import Callback{args_count}

        c = Callback{args_count}[{types_ok}]()

        def too_few_func({sig_too_few}) -> None: ...
        c.Register(too_few_func)
        c({args_too_few})

        def too_many_func({sig_too_many}) -> None: ...
        c.Register(too_many_func)
        c({args_too_many})

        def ok_func({sig_ok}) -> None: ...
        c.Register(ok_func)
        c({args_ok})
        """
    )
    result = type_checker.run()
    result.assert_errors(
        [
            "has incompatible type",
            "Missing positional argument",
            "has incompatible type",
            "Too many arguments",
        ]
    )
