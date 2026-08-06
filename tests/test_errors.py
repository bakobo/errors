"""The error-code machinery: code matching, registry entries, and the exception that carries them.

Grades against ``dev/standards/error-codes.md``: the three matching modes, a static title and detail
template per code, positional args on the wire, and a length cap so an untrusted value can never be
echoed unbounded into a message. Ported from ``heti``'s ``tests/test_errors.py``, the module this
package was lifted from (``this.i`` @niawr3).

Fixture codes here use the leaf ``fixture``, which no repo will ever mint. Borrowing a code another
repo owns for real is the mistake that makes a genuine duplicate indistinguishable from noise
(@gvn2k2), and a package that refuses illegal codes has no business modelling it in its own suite.
"""

import pytest

from bakobo.errors import ARG_CAP, BakoboError, ErrorCode, matches

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


def test_a_pattern_without_a_wildcard_or_trailing_dot_matches_exactly():
    assert matches("e.input.missing.sig.f", "e.input.missing.sig.f")
    assert not matches("e.input.missing.sig.f", "e.input.missing")
    assert not matches("e.input.missing.sig.f", "e.input.missing.sig-input.f")


def test_a_pattern_ending_in_a_dot_matches_by_prefix():
    assert matches("e.input.missing.sig.f", "e.input.")
    assert matches("e.input.missing.sig.f", "e.input.missing.")
    assert not matches("e.proof.said.f", "e.input.")


def test_a_pattern_containing_a_star_matches_as_a_glob():
    assert matches("e.input.format.key.f", "e.input.format.*")
    assert matches("e.input.format.key.f", "e.input.*")
    assert not matches("e.proof.said.f", "e.input.*")


def test_a_glob_can_select_a_disposition_across_every_descriptor():
    assert matches("e.env.watcher-timeout.r", "*.r")
    assert matches("e.state.pending.escrow.r", "*.r")
    assert not matches("e.input.missing.sig.f", "*.r")


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
    err = _WITH_ARGS(keyid="A" * 500, size=32)
    assert len(err.code_args[0]) == ARG_CAP
    assert err.code_args[0].endswith("…")
    assert err.code_args[0] in err.detail


def test_a_short_string_arg_and_a_non_string_arg_survive_untouched():
    err = _WITH_ARGS(keyid="AAAA", size=32)
    assert err.code_args == ("AAAA", 32)


def test_retryability_is_read_off_the_disposition_token():
    assert _RETRYABLE().retryable is True
    assert _NO_ARGS().retryable is False


def test_an_error_matches_patterns_against_its_own_code():
    err = _NO_ARGS()
    assert err.matches("e.input.")
    assert err.matches("e.input.missing.fixture.f")
    assert not err.matches("e.proof.said.f")


def test_the_entry_that_raised_is_reachable_from_the_exception():
    err = _NO_ARGS()
    assert err.entry is _NO_ARGS
