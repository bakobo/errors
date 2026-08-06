"""The closed taxonomy, and the refusal that makes it binding.

``error-codes.md`` closes the set of first descriptors and forbids a bare one from ever being a
code. Those are rules a repo can only follow, not check — so this package refuses an illegal code at
``ErrorCode`` construction, which is import time for a module-scope literal (``this.i`` @3fg2dn).
What the validator deliberately does *not* police is the leaf: deeper sub-descriptors are free to
mint, and only first descriptors are closed.
"""

import pytest

from bakobo.errors import DESCRIPTORS, ErrorCode, validate_code

LEGAL = [
    "e.input.missing.f",                # the shortest legal shape: one sub-descriptor
    "e.input.format.sig-input.f",
    "w.feature.deprecated.f",           # the warning sorter
    "e.env.watcher-timeout.r",          # a leaf minted under a descriptor with no standard subs
    "e.self.config.machine-cell.f",     # two sub-descriptors
    "e.state.conflict.record-busy.r",
    "e.proof.sha2-256.f",               # digits are fine inside a leaf
    "e.rule.jurisdiction.f",
    "e.party.refused.f",
    "e.grant.scope.f",
    "e.id.expired.f",
]

ILLEGAL = [
    ("", "empty"),
    ("e", "one token"),
    ("e.input", "two tokens"),
    ("e.input.f", "a bare descriptor, which is a match pattern and never a code"),
    ("e.proof.f", "a bare descriptor under a descriptor with no standard subs"),
    ("e.input.missing", "no disposition"),
    ("x.input.missing.f", "an unknown sorter"),
    ("e.bogus.missing.f", "a first descriptor outside the closed set"),
    ("e.input.missing.x", "an unknown disposition"),
    ("e.input.r.sig.f", "the reserved token r used as a sub-descriptor"),
    ("e.input.f.sig.f", "the reserved token f used as a sub-descriptor"),
    ("E.INPUT.MISSING.F", "upper case"),
    ("e.Input.missing.f", "an upper-case descriptor"),
    ("e.input..missing.f", "an empty token"),
    ("e.input.missing.f.", "a trailing dot, which is a prefix pattern"),
    (".input.missing.f", "a leading dot"),
    ("e.input.missing.*", "a star, which is a glob pattern"),
    ("e.input.missing_sig.f", "an underscore instead of a hyphen"),
    ("e.input.-sig.f", "a leading hyphen in a token"),
    ("e.input.sig-.f", "a trailing hyphen in a token"),
    ("e.input.sig sig.f", "a space in a token"),
]


@pytest.mark.parametrize("code", LEGAL)
def test_a_legal_code_validates(code):
    validate_code(code)


@pytest.mark.parametrize("code,why", ILLEGAL, ids=[why for _, why in ILLEGAL])
def test_an_illegal_code_is_refused(code, why):
    with pytest.raises(ValueError):
        validate_code(code)


def test_the_refusal_names_the_code_it_refused():
    with pytest.raises(ValueError, match="e.bogus.missing.f"):
        validate_code("e.bogus.missing.f")


def test_something_that_is_not_a_string_is_refused_rather_than_crashing():
    with pytest.raises(ValueError):
        validate_code(None)


def test_declaring_a_registry_entry_with_an_illegal_code_fails_at_construction():
    with pytest.raises(ValueError, match="e.proof.f"):
        ErrorCode("e.proof.f", "A bare descriptor is a category, never a code.")


def test_declaring_a_registry_entry_with_a_legal_code_succeeds():
    entry = ErrorCode("e.proof.said.f", "The SAID does not match the content it names.")
    assert entry.code == "e.proof.said.f"


def test_every_first_descriptor_in_the_standard_is_carried_as_data():
    assert set(DESCRIPTORS) == {
        "input", "id", "grant", "feature", "proof",
        "party", "state", "env", "self", "rule",
    }


def test_each_descriptor_carries_its_obstacle_and_its_standard_sub_descriptors():
    assert DESCRIPTORS["input"].obstacle == "What you sent"
    assert DESCRIPTORS["input"].subs == ("missing", "format", "range", "multi")
    assert DESCRIPTORS["state"].subs == ("conflict", "missing", "pending")
    assert DESCRIPTORS["env"].subs == ()  # no standard subs; a repo mints its own


def test_no_descriptor_collides_with_a_reserved_disposition_token():
    assert "f" not in DESCRIPTORS
    assert "r" not in DESCRIPTORS


@pytest.mark.parametrize("descriptor", sorted(DESCRIPTORS))
def test_every_standard_sub_descriptor_forms_a_legal_code(descriptor):
    for sub in DESCRIPTORS[descriptor].subs:
        validate_code(f"e.{descriptor}.{sub}.f")
