"""The closed first-descriptor set, as data.

``error-codes.md`` carries this table in prose, because a reader needs the *why* of each descriptor
and the five boundaries that decide most cases. This module carries the same set as literals, so the
validator and the catalog read one machine-checkable artifact instead of a markdown table whose
formatting a release would then depend on (``this.i`` @gzkwg6). The two are reconciled in CI; where
they disagree, the standard is right and this file is the defect.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Descriptor:
    """One first descriptor: the obstacle it names, and the sub-descriptors the standard defines."""

    obstacle: str
    subs: tuple[str, ...] = ()


SORTERS = {
    "e": "Error. The problem clearly defeats someone's intentions.",
    "w": "Warning. The consequences are not obvious to us; evaluating them needs judgment from a "
         "human or another system.",
}

DISPOSITIONS = {
    "f": "Final. Retrying the same thing changes nothing.",
    "r": "Retryable. Trying again may succeed.",
}

DESCRIPTORS = {
    "input": Descriptor("What you sent", ("missing", "format", "range", "multi")),
    "id": Descriptor("Who you are (authentication)", ("missing", "invalid", "expired")),
    "grant": Descriptor("What you may do (delegated authority)", ("missing", "scope", "quota")),
    "feature": Descriptor(
        "The availability of a capability", ("unsupported", "unlicensed", "deprecated")
    ),
    "proof": Descriptor("Supplied material fails verification against a reference"),
    "party": Descriptor("Another actor's conduct or choice"),
    "state": Descriptor("The condition of the target", ("conflict", "missing", "pending")),
    "env": Descriptor("A system we depend on that did not deliver"),
    "self": Descriptor(
        "Us — our fault, or we cannot attribute it",
        ("resource", "config", "corrupt", "unknown"),
    ),
    "rule": Descriptor("A norm we enforce, neither authority nor verification"),
}


GRAMMAR = "<sorter>.<descriptor>[.<sub-descriptor>...].<disposition>"

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
"""Lower kebab-case: one or more lower-case alphanumeric runs joined by single hyphens."""


def _refuse(code, problem: str) -> None:
    raise ValueError(
        f"{code!r} is not a legal Bakobo error code, because {problem}. The grammar is "
        f"{GRAMMAR}; see dev/standards/error-codes.md."
    )


def validate_code(code: str) -> None:
    """Raise ``ValueError`` unless ``code`` is a legal Bakobo error code.

    What is checked is the identity's shape and its first descriptor: the closed set the standard
    says a repo may not add to. What is not checked is the leaf — deeper sub-descriptors are a
    repo's own to mint, so ``e.env.watcher-timeout.r`` and ``e.self.record-write.f`` both pass even
    though neither leaf appears in any table.
    """
    if not isinstance(code, str):
        _refuse(code, f"an error code is a string and this is a {type(code).__name__}")

    tokens = code.split(".")
    for token in tokens:
        if not _TOKEN.match(token):
            _refuse(
                code,
                f"the token {token!r} is not lower kebab-case (a pattern ending in a dot or "
                f"containing a star is a match pattern, never a code)",
            )

    if tokens[-1] not in DISPOSITIONS:
        _refuse(
            code,
            f"it ends in {tokens[-1]!r} rather than a disposition, one of "
            f"{' or '.join(sorted(DISPOSITIONS))}",
        )
    if len(tokens) < 4:
        _refuse(
            code,
            "a first descriptor is a category rather than one condition's identity, so a code "
            "carries at least one sub-descriptor",
        )
    if tokens[0] not in SORTERS:
        _refuse(
            code,
            f"it starts with {tokens[0]!r} rather than a sorter, one of "
            f"{' or '.join(sorted(SORTERS))}",
        )
    if tokens[1] not in DESCRIPTORS:
        _refuse(
            code,
            f"{tokens[1]!r} is not one of the ten first descriptors — adding one is a change to "
            f"the standard, not a change to a registry",
        )
    for token in tokens[2:-1]:
        if token in DISPOSITIONS:
            _refuse(
                code,
                f"{token!r} is reserved for the disposition and may never be a sub-descriptor, "
                f"which is what keeps a code prefix-matchable",
            )
