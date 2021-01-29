from oop_ext.foundation.is_frozen import (
    IsDevelopment,
    IsFrozen,
    SetIsDevelopment,
    SetIsFrozen,
)


def testIsFrozenIsDevelopment() -> None:
    # Note: this test is checking if we're always running tests while not in frozen mode,
    # still, we have to do a try..finally to make sure we restore things to the proper state.
    was_frozen = IsFrozen()
    try:
        assert IsFrozen() == False
        assert IsDevelopment() == True

        SetIsDevelopment(False)
        assert IsFrozen() == False
        assert IsDevelopment() == False

        SetIsDevelopment(True)
        assert IsFrozen() == False
        assert IsDevelopment() == True

        SetIsFrozen(True)
        assert IsFrozen() == True
        assert IsDevelopment() == True

        SetIsFrozen(False)
        assert IsFrozen() == False
        assert IsDevelopment() == True
    finally:
        SetIsFrozen(was_frozen)
