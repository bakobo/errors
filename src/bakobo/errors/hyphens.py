"""Catch the level a hyphen deleted.

``error-codes.md`` says a hyphen joins words into one name and a dot separates levels of meaning, so
a leaf whose halves are things in a containment relation is two levels wrongly spelled as one:
``record-head`` should be ``record.head``, and ``e.state.conflict.record.`` should gather every
problem a record can have.

That rule cannot be decided mechanically — ``trans-aid`` is one concept and ``record-head`` is two —
so this reports at three confidences rather than pretending to judge. Two are evidence: a half that
already stands as its own level somewhere in the corpus is *proven*, and a half shared by two or more
codes is a *family* whose common prefix does not work. The third is the important one: every
remaining hyphen must be justified in writing, which does not decide the question but makes
hyphenating a deliberate act instead of the path of least resistance. That is the whole intervention
— the antipattern spread because compounding two nouns is what English does for free.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

ALLOWLIST = Path(__file__).resolve().parents[3] / "hyphens.toml"
"""Where the justified hyphens live, when running from a source checkout."""


@dataclass(frozen=True)
class Suspicion:
    """One hyphenated leaf the check is not willing to pass silently."""

    code: str
    token: str
    confidence: str
    reason: str
    repair: str

    def __str__(self) -> str:
        left, right = self.token.split("-", 1)
        return (
            f"{self.code} — {self.reason} Suggested: {self.repair}, subject before predicate. "
            f"Invert it if {right!r} is the subject rather than {left!r} — it usually is when the "
            f"left half qualifies the right, as in a delegated AID or a covered component."
        )


def read_allowlist(path=ALLOWLIST) -> set[str]:
    """Read the hyphens a human has justified in writing.

    A bare token with no justification is refused rather than honoured: an allowlist that accepts
    silence is a list of hyphens nobody thought about, which is the state this check exists to end.
    """
    path = Path(path)
    if not path.is_file():
        return set()
    declared = tomllib.loads(path.read_text())
    for token, justification in declared.items():
        if not str(justification).strip():
            raise ValueError(
                f"The hyphen {token!r} is allowed in {path} with no justification. Say in one line "
                f"why both halves are one concept rather than two levels, or re-mint the code."
            )
    return set(declared)


def _levels(entries) -> dict[str, set[str]]:
    """Every sub-descriptor that stands as a level of its own, keyed by the parent it sits under.

    Keyed by parent because a level only proves something about its own siblings: ``comp`` under
    ``e.feature.unsupported.`` says nothing about ``covered-comp`` under ``e.input.missing.``. The
    first descriptor is never itself a level here — it is one in every code by construction.
    """
    found: dict[str, set[str]] = {}
    for entry in entries:
        tokens = entry.code.split(".")
        for depth, token in enumerate(tokens[2:-1], start=2):
            if "-" not in token:
                found.setdefault(".".join(tokens[:depth]), set()).add(token)
    return found


def _repair(code: str, token: str, head: str) -> str:
    """The same code with the hyphen turned into a dot, parent first."""
    left, right = token.split("-", 1)
    ordered = f"{left}.{right}" if head == left else f"{right}.{left}"
    return code.replace(token, ordered)



def suspicions(entries, allowed=None) -> list[Suspicion]:
    """Every hyphenated leaf in the corpus that looks like a missing level."""
    allowed = read_allowlist() if allowed is None else allowed
    levels = _levels(entries)

    halves: dict[str, set[str]] = {}
    for entry in entries:
        for token in entry.code.split(".")[1:-1]:
            if "-" in token:
                left, right = token.split("-", 1)
                halves.setdefault(left, set()).add(entry.code)
                halves.setdefault(right, set()).add(entry.code)

    def parent(left: str, right: str) -> str:
        """The left half — the subject, under the standard's subject-before-predicate default.

        Counting which half organises more codes was tried and rejected: it measures frequency in
        today's corpus, not effect on what a recipient does, which is the axis the standard orders
        by. It got ``record.head`` right by luck and ``endorsement-sig`` backwards on principle,
        proposing ``sig.endorsement`` when the endorsement is the subject.
        """
        return left

    found = []
    for entry in entries:
        tokens = entry.code.split(".")
        for depth, token in enumerate(tokens[1:-1], start=1):
            if "-" not in token or token in allowed:
                continue
            left, right = token.split("-", 1)
            beside = levels.get(".".join(tokens[:depth]), set())
            proof = left if left in beside else right if right in beside else None
            if proof is not None:
                found.append(Suspicion(
                    entry.code, token, "proven",
                    f"{proof!r} already stands as its own level beside it, so {token!r} is that "
                    f"level with a dot missing.",
                    _repair(entry.code, token, parent(left, right)),
                ))
            elif len(halves.get(left, ())) > 1 or len(halves.get(right, ())) > 1:
                head = left if len(halves.get(left, ())) > 1 else right
                found.append(Suspicion(
                    entry.code, token, "family",
                    f"{head!r} is shared by {len(halves[head])} codes, so they are a family whose "
                    f"common prefix does not work.",
                    _repair(entry.code, token, parent(left, right)),
                ))
            else:
                found.append(Suspicion(
                    entry.code, token, "undeclared",
                    f"{token!r} is hyphenated and unjustified.",
                    _repair(entry.code, token, left),
                ))
    return sorted(set(found), key=lambda s: (s.code, s.token))


ALLOWED = read_allowlist()
"""The justified hyphens, read once at import."""
