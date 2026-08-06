"""Merging every repo's entries into one index, and refusing to publish a collision.

Global uniqueness — one code, one meaning, everywhere — is the rule ``error-codes.md`` states and
that nobody could check until an index existed (``this.i`` @gazetr). Two repos declaring the same
code identically are agreeing, and the catalog records both origins. Two declaring it differently
are colliding, and the difference decides whether that is fatal (@wklkoj).
"""

import pytest

from bakobo.errors.catalog import Collision, build_index, collisions
from bakobo.errors.extract import Entry


def entry(code, title="A title.", *, repo="heti", args=(), detail=None, hint=None, symbol="X"):
    return Entry(
        code=code, title=title, repo=repo, path=f"src/{repo}/errors.py", line=1,
        symbol=symbol, detail=detail, args=args, hint=hint,
    )


def test_one_code_declared_once_produces_one_indexed_entry():
    index = build_index([entry("e.proof.said.f")])
    (found,) = index["codes"]
    assert found["code"] == "e.proof.said.f"
    assert found["title"] == "A title."
    assert found["origins"] == [
        {"repo": "heti", "path": "src/heti/errors.py", "line": 1, "symbol": "X"}
    ]


def test_the_index_decomposes_a_code_into_the_parts_a_reader_navigates_by():
    index = build_index([entry("e.state.pending.escrow.r")])
    (found,) = index["codes"]
    assert found["sorter"] == "e"
    assert found["descriptor"] == "state"
    assert found["subs"] == ["pending", "escrow"]
    assert found["disposition"] == "r"
    assert found["retryable"] is True
    assert found["prefixes"] == ["e.", "e.state.", "e.state.pending.", "e.state.pending.escrow."]


def test_the_index_is_sorted_by_code_so_a_rebuild_produces_the_same_bytes():
    index = build_index([entry("e.state.missing.kel.r"), entry("e.input.missing.sig.f")])
    assert [c["code"] for c in index["codes"]] == [
        "e.input.missing.sig.f", "e.state.missing.kel.r",
    ]


def test_two_repos_declaring_one_code_identically_are_agreeing_not_colliding():
    entries = [entry("e.proof.said.f", repo="heti"), entry("e.proof.said.f", repo="tefa")]
    assert collisions(entries) == []
    (found,) = build_index(entries)["codes"]
    assert [origin["repo"] for origin in found["origins"]] == ["heti", "tefa"]


def test_two_repos_declaring_one_code_with_different_titles_collide_fatally():
    entries = [
        entry("e.proof.said.f", "The SAID does not match.", repo="heti"),
        entry("e.proof.said.f", "Something else entirely.", repo="tefa"),
    ]
    (collision,) = collisions(entries)
    assert collision.code == "e.proof.said.f"
    assert collision.fatal is True
    assert "title" in collision.differs
    assert {origin.repo for origin in collision.entries} == {"heti", "tefa"}


def test_different_args_for_one_code_collide_fatally_because_args_are_positional():
    entries = [
        entry("e.proof.said.f", args=("said",), repo="heti"),
        entry("e.proof.said.f", args=("said", "issuer"), repo="tefa"),
    ]
    (collision,) = collisions(entries)
    assert collision.fatal is True
    assert "args" in collision.differs


def test_different_prose_for_one_code_is_reported_without_failing_the_build():
    entries = [
        entry("e.proof.said.f", hint="Check the digest.", repo="heti"),
        entry("e.proof.said.f", hint="Recompute the digest.", repo="tefa"),
    ]
    (collision,) = collisions(entries)
    assert collision.fatal is False
    assert collision.differs == ("hint",)


def test_a_collision_names_every_field_that_differs():
    entries = [
        entry("e.proof.said.f", "One title.", args=("a",), detail="One.", repo="heti"),
        entry("e.proof.said.f", "Another title.", args=("b",), detail="Two.", repo="tefa"),
    ]
    (collision,) = collisions(entries)
    assert collision.differs == ("title", "detail", "args")


def test_three_declarations_of_one_code_are_a_single_collision():
    entries = [entry("e.proof.said.f", f"Title {n}.", repo=f"r{n}") for n in range(3)]
    (collision,) = collisions(entries)
    assert len(collision.entries) == 3


def test_a_collision_renders_as_a_sentence_that_names_where_to_look():
    entries = [
        entry("e.proof.said.f", "One title.", repo="heti"),
        entry("e.proof.said.f", "Another title.", repo="tefa"),
    ]
    rendered = str(collisions(entries)[0])
    assert "e.proof.said.f" in rendered
    assert "src/heti/errors.py:1" in rendered
    assert "src/tefa/errors.py:1" in rendered


def test_building_an_index_over_a_fatal_collision_refuses_rather_than_picking_one():
    entries = [
        entry("e.proof.said.f", "One title.", repo="heti"),
        entry("e.proof.said.f", "Another title.", repo="tefa"),
    ]
    with pytest.raises(Collision):
        build_index(entries)


def test_building_an_index_over_prose_divergence_keeps_the_first_declaration():
    entries = [
        entry("e.proof.said.f", hint="Check the digest.", repo="heti"),
        entry("e.proof.said.f", hint="Recompute the digest.", repo="tefa"),
    ]
    (found,) = build_index(entries)["codes"]
    assert found["hint"] == "Check the digest."
    assert len(found["origins"]) == 2
