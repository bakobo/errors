"""The error-code machinery: code matching, registry entries, and the exception that carries them.

Grades against ``dev/standards/error-codes.md``: a static title and detail template per code, positional args on the wire, and a length cap so an untrusted value can never be
echoed unbounded into a message. Ported from ``heti``'s ``tests/test_errors.py``, the module this
package was lifted from (``this.i`` @niawr3).

Fixture codes here use the leaf ``fixture``, which no repo will ever mint. Borrowing a code another
repo owns for real is the mistake that makes a genuine duplicate indistinguishable from noise
(@gvn2k2), and a package that refuses illegal codes has no business modelling it in its own suite.
"""

import pytest

from bakobo.errors import ARG_CAP, BakoboError, ErrorCode

_NO_ARGS = ErrorCode(
    "e.input.missing.fixture.f",
    "The request carries no signature to check.",
)
_WITH_ARGS = ErrorCode(
    "e.input.format.fixture.f",
    "The signature names a key I can't read.",
    detail='The keyid "{keyid}" isn\'t a base64url-encoded {size}-byte Ed25519 public key.',
    args=("keyid", "size"),
    hint="Send the raw public key, base64url-encoded, as the JWK x value.",
)
_RETRYABLE = ErrorCode("e.env.fixture.r", "I couldn't reach a service I depend on.")


def test_raising_a_code_with_no_args_uses_the_title_as_the_detail():
    err = _NO_ARGS()
    assert isinstance(err, BakoboError)
    assert err.code == "e.input.missing.fixture.f"
    assert err.title == "The request carries no signature to check."
    assert err.detail == err.title
    assert err.code_args == ()
    assert err.hint is None


def test_raising_a_code_with_args_interpolates_the_detail_and_keeps_args_positional():
    err = _WITH_ARGS(keyid="AAAA", size=32)
    assert err.title == "The signature names a key I can't read."
    assert err.detail == 'The keyid "AAAA" isn\'t a base64url-encoded 32-byte Ed25519 public key.'
    assert err.code_args == ("AAAA", 32)  # declaration order, not call order
    assert err.hint == "Send the raw public key, base64url-encoded, as the JWK x value."


def test_the_exception_message_carries_the_sentence_and_the_code():
    err = _WITH_ARGS(size=32, keyid="AAAA")
    assert str(err) == (
        'The keyid "AAAA" isn\'t a base64url-encoded 32-byte Ed25519 public key. '
        "[e.input.format.fixture.f]"
    )


@pytest.mark.parametrize(
    "values",
    [
        {"keyid": "AAAA"},                              # missing one
        {"keyid": "AAAA", "size": 32, "extra": "no"},   # one too many
        {},                                             # none at all
    ],
)
def test_raising_a_code_with_the_wrong_args_is_a_programming_error(values):
    with pytest.raises(ValueError, match="e.input.format.fixture.f"):
        _WITH_ARGS(**values)


def test_a_long_string_arg_is_capped_before_it_reaches_the_message():
    err = _WITH_ARGS(keyid="A" * 5000, size=32)
    assert len(err.code_args[0]) == ARG_CAP
    assert "…" in err.code_args[0]
    assert err.code_args[0] in err.detail


def test_the_cap_is_a_flood_guard_rather_than_a_legibility_rule():
    """The number, stated as a row, because it is the whole of the decision.

    It was 80 for years and the figure was never argued: both rubrics in ``error-handling.md``
    say an interpolated value must be *capped* and neither says how tightly. Eighty is short
    enough to cut a sentence an application wrote itself, which is how heti ended up with
    sixteen refusals that stopped mid-clause, usually just before the part naming the remedy.

    What this bound is for is a value from the wire, in a message that may be logged: nothing
    may make a message unbounded. What it is *not* for is deciding what reads well on a screen.
    That is the display layer's, which knows its own geometry — heti bounds a field at 200 for
    two and a half rows of an eighty-column terminal — and a caller with no display bound of its
    own is better served by a generous guard than by a tight one it did not choose.
    """
    assert ARG_CAP >= 512
    assert ARG_CAP <= 4096


def test_a_capped_value_keeps_its_end_as_well_as_its_beginning():
    """Head-truncation drops the part that identifies a path.

    ``/home/somebody/very/long/.../grant.cesr`` cut at the cap names a directory and hides the
    filename, which is the one thing the reader needed. Eliding the middle keeps both ends, and
    it is right for every kind of value rather than only for paths: an identifier is
    distinguished at both ends, and a sentence that has to be cut reads better with its
    conclusion than without it.
    """
    err = _WITH_ARGS(keyid="/start/" + "x" * 5000 + "/grant.cesr", size=32)
    capped = err.code_args[0]

    assert len(capped) == ARG_CAP
    assert capped.startswith("/start/")
    assert capped.endswith("/grant.cesr")
    assert "…" in capped


def test_a_value_only_just_over_the_cap_is_still_readable():
    """The elision has to leave something on both sides at every length, not only for the
    enormous case — a value one character over must not come back as mostly ellipsis."""
    err = _WITH_ARGS(keyid="a" * (ARG_CAP + 1), size=32)
    capped = err.code_args[0]

    assert len(capped) == ARG_CAP
    assert capped.startswith("aaaa")
    assert capped.endswith("aaaa")


def test_a_short_string_arg_and_a_non_string_arg_survive_untouched():
    err = _WITH_ARGS(keyid="AAAA", size=32)
    assert err.code_args == ("AAAA", 32)


def test_retryability_is_read_off_the_disposition_token():
    assert _RETRYABLE().retryable is True
    assert _NO_ARGS().retryable is False


def test_the_entry_that_raised_is_reachable_from_the_exception():
    err = _NO_ARGS()
    assert err.entry is _NO_ARGS
