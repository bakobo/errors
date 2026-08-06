"""Fixtures shared across the suite."""

from pathlib import Path

import pytest

STANDARD = Path(__file__).resolve().parents[2] / "dev" / "standards" / "error-codes.md"


@pytest.fixture
def standard_text():
    """The real text of ``error-codes.md``, from the sibling ``bakobo/dev`` checkout.

    Skipped when ``dev`` is not checked out beside this repo, so a clone without it can still run
    the suite. That skip is a convenience and not the enforcement: CI checks out ``dev`` and runs
    ``bakobo-errors reconcile``, which fails hard.
    """
    if not STANDARD.is_file():
        pytest.skip(
            f"No standard at {STANDARD}. Clone bakobo/dev beside this repo to check the taxonomy "
            f"data against it; CI does this and fails on a mismatch."
        )
    return STANDARD.read_text()
