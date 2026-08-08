"""One verb per question, over a code that is a path in an IS-A tree.

``e.state.conflict.record.head.f`` IS-A ``e.state.conflict.record.``, which IS-A
``e.state.conflict.`` — so a handler written against any of them keeps being right about leaves
minted later, in repos it has never heard of (``this.i`` @hf4yes). These tests pin the three
questions apart, and pin the two places the old single verb answered the wrong one silently: a
forgotten trailing dot, and a disposition smuggled into a class test.
"""

import pytest

from bakobo.errors import ErrorCode, is_a, is_like

DEEP = ErrorCode("e.state.conflict.record.head.f", "Another writer moved the head.")
SHALLOW = ErrorCode("e.env.db.r", "The database did not answer.")
RETRYABLE = ErrorCode("e.env.db.timeout.r", "The database did not answer in time.")
FINAL = ErrorCode("e.env.db.corrupt.f", "The database is unreadable.")


# --- is_a: the class test -------------------------------------------------------------------

@pytest.mark.parametrize("branch", [
    "e.state.conflict.record",       # the immediate parent
    "e.state.conflict",              # a grandparent
    "e.state",                       # the descriptor
    "e.state.conflict.record.head",  # every ancestor, named without its disposition
])
def test_a_code_is_a_member_of_every_class_above_it(branch):
    assert DEEP().is_a(branch)


def test_is_a_is_indifferent_to_a_trailing_dot():
    """The old matcher made this the difference between a prefix and an exact test (tick 3p7x)."""
    assert DEEP().is_a("e.state.conflict.record") is DEEP().is_a("e.state.conflict.record.")


def test_is_a_is_reflexive_like_instanceof():
    assert DEEP().is_a("e.state.conflict.record.head.f".removesuffix(".f"))


def test_a_code_is_not_a_member_of_a_sibling_class():
    assert not DEEP().is_a("e.state.missing")
    assert not DEEP().is_a("e.state.conflict.entry")


def test_a_class_is_not_matched_by_a_token_that_merely_starts_the_same_way():
    """`record` must not gather `recording`; the dot is what anchors the boundary."""
    assert not ErrorCode("e.state.conflict.recording.f", "x")().is_a("e.state.conflict.record")


def test_the_disposition_never_fragments_a_class():
    """The point of parking it last: both dispositions stay in the same branch."""
    assert RETRYABLE().is_a("e.env.db")
    assert FINAL().is_a("e.env.db")


def test_is_a_refuses_a_branch_carrying_a_disposition():
    """It would read as a class test and behave as a leaf test; nothing can live beneath `.r`."""
    with pytest.raises(ValueError, match="is_exactly"):
        RETRYABLE().is_a("e.env.db.timeout.r")


def test_is_a_refuses_a_bare_disposition_too():
    with pytest.raises(ValueError):
        RETRYABLE().is_a("e.env.db.r")


def test_retryability_is_a_property_rather_than_a_pattern():
    """`is_a(...) and retryable` is how you ask for the retryable half of a class."""
    assert RETRYABLE().is_a("e.env.db") and RETRYABLE().retryable
    assert FINAL().is_a("e.env.db") and not FINAL().retryable


# --- is_exactly: the leaf test --------------------------------------------------------------

def test_is_exactly_takes_the_registry_entry_so_a_deleted_constant_is_an_import_error():
    assert DEEP().is_exactly(DEEP)
    assert not DEEP().is_exactly(SHALLOW)


def test_is_exactly_also_accepts_the_code_as_a_string():
    assert DEEP().is_exactly("e.state.conflict.record.head.f")


def test_is_exactly_does_not_match_a_descendant():
    """This is the brittleness that makes it honest: refining a leaf is a retire-and-replace."""
    assert not ErrorCode("e.state.conflict.record.head.moved.f", "x")().is_exactly(DEEP)


# --- is_like: the wildcard test -------------------------------------------------------------

def test_one_star_matches_exactly_one_segment():
    assert is_like("e.proof.event.sig.f", "e.proof.*.sig.f")
    assert not is_like("e.proof.sig.f", "e.proof.*.sig.f")          # zero segments
    assert not is_like("e.proof.a.b.sig.f", "e.proof.*.sig.f")      # two segments


def test_two_stars_match_zero_or_more_segments():
    assert is_like("e.proof.sig.f", "e.proof.**.sig.f")             # zero, as gitignore's a/**/b
    assert is_like("e.proof.event.sig.f", "e.proof.**.sig.f")
    assert is_like("e.proof.a.b.sig.f", "e.proof.**.sig.f")


def test_two_stars_sweep_a_disposition_across_every_obstacle():
    assert is_like("e.env.db.timeout.r", "e.**.r")
    assert is_like("e.state.pending.escrow.r", "e.**.r")
    assert not is_like("e.env.db.corrupt.f", "e.**.r")


def test_a_wildcard_is_a_whole_segment_and_cannot_reach_inside_a_token():
    """What makes 'a hyphen forfeits a query' true by construction rather than by luck."""
    with pytest.raises(ValueError, match="whole segment"):
        is_like("e.input.format.sig-label.f", "e.input.format.sig-*")


def test_a_trailing_single_star_is_refused_because_it_can_match_nothing_legal():
    """Every legal code has four tokens or more, so `e.env.*` reads like a branch and is empty."""
    with pytest.raises(ValueError, match="is_a"):
        is_like("e.env.db.r", "e.env.*")


def test_a_trailing_double_star_is_allowed_and_means_the_branch():
    assert is_like("e.env.db.r", "e.env.**")
    assert not is_like("e.state.pending.escrow.r", "e.env.**")


def test_a_pattern_with_no_wildcard_at_all_is_refused():
    with pytest.raises(ValueError, match="is_exactly"):
        is_like("e.env.db.r", "e.env.db.r")


def test_is_like_is_reachable_from_the_error_too():
    assert RETRYABLE().is_like("e.**.r")


# --- the old verb is gone -------------------------------------------------------------------

def test_the_single_inferring_verb_is_retired():
    """Leaving it would leave the teaching material in place, which is why the codes moved too."""
    import bakobo.errors as errors
    assert not hasattr(errors, "matches")
    assert not hasattr(RETRYABLE(), "matches")
