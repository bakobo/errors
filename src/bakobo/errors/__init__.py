"""Bakobo error codes: the registry entry, the exception that carries one, and code matching.

An error's identity is a code — ``<sorter>.<descriptor>[.<sub-descriptor>...].<disposition>``,
lower kebab-case, meaning growing more specific left to right — and recipients match it by prefix,
so a handler written against ``e.input.`` keeps handling leaves minted after it. See
``dev/standards/error-codes.md``.

This is the shared package that standard names. It is ``heti``'s ``errors`` module lifted whole, as
that module's own docstring said it was meant to be once a second repo needed it (``this.i``
@niawr3), plus one thing heti could not do alone: an illegal code is refused at construction rather
than described in prose (@3fg2dn).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .taxonomy import DESCRIPTORS, DISPOSITIONS, SORTERS, Descriptor, validate_code

__all__ = [
    "ARG_CAP",
    "DESCRIPTORS",
    "DISPOSITIONS",
    "SORTERS",
    "BakoboError",
    "Descriptor",
    "ErrorCode",
    "is_a",
    "is_exactly",
    "is_like",
    "validate_code",
]

ARG_CAP = 80
"""Longest string an arg may reach a message as. Values arrive from the wire; a message may be
rendered or logged, so no arg is ever echoed unbounded (``error-handling.md``, rubric #7)."""


def is_a(code: str, branch: str) -> bool:
    """Whether ``code`` belongs to the class ``branch`` names.

    This is ``instanceof`` over the dotted tree, so it is reflexive — a code is a member of its own
    class — and indifferent to a trailing dot, which the standard uses as notation and which the
    lifted matcher used as a mode switch nobody could see.

    ``branch`` may not carry a disposition. Nothing can live beneath ``.r``, so such an argument
    would read as a class test and behave as a leaf test, which is the brittleness this exists to
    prevent; that is a contract violation by the caller and raises :class:`ValueError` (@guzldf).
    """
    branch = branch.rstrip(".")
    if branch.rsplit(".", 1)[-1] in DISPOSITIONS:
        raise ValueError(
            f"{branch!r} carries a disposition, so it names one leaf rather than a class — nothing "
            f"can ever live beneath it. Use is_exactly for a leaf, or drop the disposition."
        )
    return code == branch or code.startswith(branch + ".")


def is_exactly(code: str, other) -> bool:
    """Whether ``code`` is that one condition.

    Takes the :class:`ErrorCode` itself by preference, so that retiring a code is an import error
    at the call site rather than a comparison that quietly stops being true.
    """
    return code == getattr(other, "code", other)


def _segments(pattern: str) -> list[str]:
    """The pattern's segments, refusing the shapes that cannot mean what they look like."""
    segments = pattern.split(".")
    for segment in segments:
        if "*" in segment and segment not in ("*", "**"):
            raise ValueError(
                f"{segment!r} mixes a wildcard with a token. A wildcard is a whole segment, which "
                f"is what keeps a hyphenated name unreachable by any pattern."
            )
    if not any(segment in ("*", "**") for segment in segments):
        raise ValueError(f"{pattern!r} has no wildcard in it. Use is_exactly.")
    if segments[-1] == "*":
        raise ValueError(
            f"{pattern!r} ends in a single wildcard, which matches one segment where every legal "
            f"code carries a disposition — so it selects nothing legal. Use is_a for a branch."
        )
    return segments


def _matches(code: list[str], pattern: list[str]) -> bool:
    """Match segment lists, where ``**`` consumes zero or more and ``*`` consumes exactly one."""
    if not pattern:
        return not code
    head, rest = pattern[0], pattern[1:]
    if head == "**":
        return any(_matches(code[taken:], rest) for taken in range(len(code) + 1))
    if not code:
        return False
    if head != "*" and head != code[0]:
        return False
    return _matches(code[1:], rest)


def is_like(code: str, pattern: str) -> bool:
    """Whether ``code`` matches a wildcard shape.

    ``*`` is exactly one segment and ``**`` is zero or more, so ``e.proof.**.sig.f`` gathers every
    signature failure including ``e.proof.sig.f`` — the axis the hierarchy did not nest on. Both are
    whole segments: ``sig-*`` is not a pattern.
    """
    return _matches(code.split("."), _segments(pattern))


def _cap(value):
    """Bound a string arg; leave anything else (a count, a size) as it is."""
    if not isinstance(value, str) or len(value) <= ARG_CAP:
        return value
    return value[: ARG_CAP - 1] + "…"


@dataclass(frozen=True)
class ErrorCode:
    """One registry entry, declared as a literal at module scope.

    ``title`` never varies with the occurrence, and ``detail`` is a template whose named
    placeholders are filled from ``args`` — both static per code, so a catalog can be extracted by
    static analysis and a localization catalog can key off the code. ``args`` are named at the call
    site and positional on the wire. ``hint`` is one line of remediation, kept here so troubleshooting
    advice has somewhere to live other than the message.

    The code is validated here, which for a module-scope literal is import time: an illegal code
    fails the importing repo's next test run rather than reaching a wire (@3fg2dn).
    """

    code: str
    title: str
    detail: str | None = None
    args: tuple[str, ...] = field(default_factory=tuple)
    hint: str | None = None

    def __post_init__(self) -> None:
        validate_code(self.code)

    def __call__(self, **values) -> BakoboError:
        """Raise-ready: ``raise MALFORMED_KEY(keyid=…)``."""
        return BakoboError(self, values)


class BakoboError(Exception):
    """A failure attributable to the request, identified by its :class:`ErrorCode`.

    Callers branch on :attr:`code` — exactly, by prefix, or by glob (:meth:`matches`) — never on the
    prose, which is free to be reworded, and never on the exception class, which is why there is one
    class for all of Bakobo rather than one per repo. Misuse of this library's own API is not one of
    these; that is a contract violation by the calling programmer and raises :class:`ValueError`.

    The situational values are :attr:`code_args`, positional in declaration order — the ``args``
    member of the problem+json envelope an HTTP binding builds. They can't live on ``args``, which
    Python's own ``BaseException`` owns and which drives ``str()``.
    """

    def __init__(self, entry: ErrorCode, values: dict):
        if set(values) != set(entry.args):
            raise ValueError(
                f"The error code {entry.code} takes the arguments {entry.args}, but it was "
                f"raised with {tuple(sorted(values))}."
            )
        capped = {name: _cap(values[name]) for name in entry.args}
        self.entry = entry
        self.code = entry.code
        self.title = entry.title
        self.code_args = tuple(capped[name] for name in entry.args)
        self.hint = entry.hint
        self.detail = (entry.detail or entry.title).format(**capped)
        super().__init__(f"{self.detail} [{self.code}]")

    @property
    def retryable(self) -> bool:
        """Whether trying the same thing again could help — the disposition token, not a guess."""
        return self.code.endswith(".r")

    def is_a(self, branch: str) -> bool:
        """Whether this error belongs to the class ``branch`` names; see :func:`is_a`."""
        return is_a(self.code, branch)

    def is_exactly(self, other) -> bool:
        """Whether this error is that one condition; see :func:`is_exactly`."""
        return is_exactly(self.code, other)

    def is_like(self, pattern: str) -> bool:
        """Whether this error matches a wildcard shape; see :func:`is_like`."""
        return is_like(self.code, pattern)
