import pytest

from agents.validation import require_complete


def test_require_complete_accepts_full_match():
    require_complete(8, 8, "validation")


def test_require_complete_exits_nonzero_for_partial_match():
    with pytest.raises(SystemExit) as exc:
        require_complete(7, 8, "validation")

    assert exc.value.code == "validation failed: 7/8 required cases passed"
