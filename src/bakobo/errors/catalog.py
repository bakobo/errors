"""Merge every repo's entries into one index, and refuse to publish a collision.

Global uniqueness is stated in ``error-codes.md`` — one code, one meaning, everywhere — and until
this index existed it was a rule nobody could check (``this.i`` @gazetr). Two repos declaring one
code identically are agreeing, and both origins are recorded. Two declaring it differently are
colliding, and which fields differ decides whether the build stops (@wklkoj).
"""

from __future__ import annotations

from dataclasses import dataclass

from .extract import Entry

IDENTITY = ("title", "args")
"""Fields whose divergence is fatal: the static title, and the args that travel positionally."""

PROSE = ("detail", "hint")
"""Fields whose divergence is reported but tolerated — two repos may word one thing differently."""

COMPARED = ("title", "detail", "args", "hint")
"""Every field compared between two declarations of one code, in the order a report names them."""


@dataclass(frozen=True)
class Collision(Exception):
    """One code declared more than once, in ways that do not agree."""

    code: str
    entries: tuple[Entry, ...]
    differs: tuple[str, ...]

    @property
    def fatal(self) -> bool:
        """Whether this difference is one the catalog refuses to publish."""
        return any(name in IDENTITY for name in self.differs)

    def __str__(self) -> str:
        where = ", ".join(f"{e.repo} {e.path}:{e.line}" for e in self.entries)
        return (
            f"{self.code} is declared {len(self.entries)} times and the declarations disagree on "
            f"{', '.join(self.differs)}: {where}. A code means one thing everywhere in Bakobo; see "
            f"error-codes.md, Minting a code."
        )


def _by_code(entries) -> dict[str, list[Entry]]:
    grouped: dict[str, list[Entry]] = {}
    for entry in entries:
        grouped.setdefault(entry.code, []).append(entry)
    return grouped


def collisions(entries) -> list[Collision]:
    """Every code declared more than once with a difference between the declarations."""
    found = []
    for code, declarations in sorted(_by_code(entries).items()):
        if len(declarations) == 1:
            continue
        first = declarations[0]
        differs = tuple(
            name for name in COMPARED
            if any(getattr(d, name) != getattr(first, name) for d in declarations[1:])
        )
        if differs:
            found.append(Collision(code, tuple(declarations), differs))
    return found


def _prefixes(code: str) -> list[str]:
    """Every pattern that prefix-matches this code, shortest first — the pages above it."""
    tokens = code.split(".")[:-1]
    return [".".join(tokens[: n + 1]) + "." for n in range(len(tokens))]


def _document(entries: list[Entry]) -> dict:
    """One code's catalog record, taking prose from the first declaration."""
    first = entries[0]
    sorter, descriptor, *subs, disposition = first.code.split(".")
    return {
        "code": first.code,
        "sorter": sorter,
        "descriptor": descriptor,
        "subs": subs,
        "disposition": disposition,
        "retryable": disposition == "r",
        "prefixes": _prefixes(first.code),
        "title": first.title,
        "detail": first.detail,
        "args": list(first.args),
        "hint": first.hint,
        "origins": [
            {"repo": e.repo, "path": e.path, "line": e.line, "symbol": e.symbol} for e in entries
        ],
    }


def build_index(entries) -> dict:
    """The catalog as one JSON-ready document, sorted by code.

    Raises the first fatal :class:`Collision` rather than choosing between two declarations —
    picking one silently is how a catalog starts disagreeing with the code that raises.
    """
    for collision in collisions(entries):
        if collision.fatal:
            raise collision
    grouped = _by_code(entries)
    return {"codes": [_document(grouped[code]) for code in sorted(grouped)]}
