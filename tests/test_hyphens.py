"""Catching the level that a hyphen deleted.

``error-codes.md`` says a hyphen joins words into one name and a dot separates levels of meaning, and
that a leaf whose two halves are things standing in a containment relation is two levels wrongly
spelled as one. That rule cannot be decided mechanically — ``trans-aid`` is one concept and
``record-head`` is two — but two thirds of it can, and the last third can be made *deliberate*
instead of accidental, which is the part that actually changes behaviour.
"""

import textwrap

import pytest

from bakobo.errors.extract import Entry
from bakobo.errors.hyphens import ALLOWED, Suspicion, read_allowlist, suspicions


def entry(code, repo="heti"):
    return Entry(code=code, title="A title.", repo=repo, path=f"src/{repo}/errors.py",
                 line=1, symbol="X")


def check(codes, allowed=()):
    return suspicions([entry(code) for code in codes], allowed=set(allowed))


def test_a_corpus_with_no_hyphens_raises_nothing():
    assert check(["e.proof.said.f", "e.state.conflict.record.head.f"]) == []


def test_a_hyphen_whose_left_half_is_a_level_elsewhere_is_proven():
    (found,) = check(["e.input.format.sig.f", "e.input.format.sig-label.f"])
    assert found.token == "sig-label"
    assert found.confidence == "proven"
    assert "sig" in found.reason


def test_a_hyphen_whose_right_half_is_a_level_elsewhere_is_proven():
    (found,) = check(["e.proof.sig.f", "e.proof.endorsement-sig.f"])
    assert found.token == "endorsement-sig"
    assert found.confidence == "proven"


def test_a_shared_left_half_across_two_codes_is_a_family():
    found = check(["e.state.conflict.record-head.f", "e.state.conflict.record-busy.r"])
    assert {f.token for f in found} == {"record-head", "record-busy"}
    assert {f.confidence for f in found} == {"family"}
    assert all("record" in f.reason for f in found)


def test_a_shared_right_half_across_two_codes_is_also_a_family():
    found = check(["e.proof.event-sig.f", "e.proof.receipt-sig.f"])
    assert {f.confidence for f in found} == {"family"}


def test_a_lone_hyphen_with_no_relative_is_merely_undeclared():
    (found,) = check(["e.feature.unsupported.trans-aid.f"])
    assert found.token == "trans-aid"
    assert found.confidence == "undeclared"


def test_an_allowlisted_hyphen_is_not_reported():
    assert check(["e.feature.unsupported.trans-aid.f"], allowed=["trans-aid"]) == []


def test_the_allowlist_cannot_excuse_a_proven_missing_level():
    """Otherwise the escape hatch swallows the finding the check exists for."""
    found = check(["e.input.format.sig.f", "e.input.format.sig-label.f"], allowed=["sig-label"])
    assert found[0].confidence == "proven"


def test_the_allowlist_does_not_excuse_a_family_either():
    found = check(
        ["e.state.conflict.record-head.f", "e.state.conflict.record-busy.r"],
        allowed=["record-head", "record-busy"],
    )
    assert len(found) == 2


def test_a_finding_names_the_code_and_proposes_the_repair():
    """Subject before predicate: the event is what the error is about, the signature is what failed."""
    (found,) = check(["e.proof.sig.f", "e.proof.event-sig.f"])
    rendered = str(found)
    assert "e.proof.event-sig.f" in rendered
    assert "e.proof.event.sig.f" in rendered


def test_the_suggestion_says_how_to_invert_it_rather_than_pretending_to_be_a_ruling():
    (found,) = check(["e.proof.sig.f", "e.proof.event-sig.f"])
    assert "Invert it" in str(found)
    assert "'sig'" in str(found)
    assert "covered component" in str(found)


def test_a_repair_for_a_left_shared_half_keeps_the_order():
    (found,) = check(["e.state.conflict.record.f", "e.state.conflict.record-head.f"])
    assert "e.state.conflict.record.head.f" in str(found)


def test_findings_are_sorted_so_two_runs_report_the_same_order():
    found = check([
        "e.state.conflict.record-head.f",
        "e.input.format.entry-kind.f",
        "e.input.format.entry-body.f",
    ])
    assert [f.code for f in found] == [
        "e.input.format.entry-body.f",
        "e.input.format.entry-kind.f",
        "e.state.conflict.record-head.f",
    ]


def test_a_hyphen_in_more_than_one_token_of_one_code_is_reported_once_per_token():
    found = check(["e.self.config.machine-cell.f", "e.self.config.machine-guard.f"])
    assert len(found) == 2


def test_the_allowlist_reads_a_token_and_its_justification(tmp_path):
    path = tmp_path / "hyphens.toml"
    path.write_text(textwrap.dedent('''
        "trans-aid" = "A transferable AID: one concept whose English name is two words."
        "not-an-object" = "A phrase, not a containment."
    '''))
    assert read_allowlist(path) == {"trans-aid", "not-an-object"}


def test_an_allowlist_entry_with_no_justification_is_refused(tmp_path):
    path = tmp_path / "hyphens.toml"
    path.write_text('"trans-aid" = ""\n')
    with pytest.raises(ValueError, match="trans-aid"):
        read_allowlist(path)


def test_a_missing_allowlist_is_an_empty_one_rather_than_a_crash(tmp_path):
    assert read_allowlist(tmp_path / "absent.toml") == set()


def test_the_shipped_allowlist_justifies_every_token_it_excuses():
    assert ALLOWED, "the shipped allowlist should not be empty while the corpus has phrases in it"


def test_a_suspicion_is_hashable_so_findings_can_be_deduped():
    assert len({Suspicion("e.a.b-c.f", "b-c", "family", "r", "e.a.b.c.f")}) == 1
