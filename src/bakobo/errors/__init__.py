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
from fnmatch import fnmatchcase

from .taxonomy import DESCRIPTORS, DISPOSITIONS, SORTERS, Descriptor, validate_code

__all__ = [
    "ARG_CAP",
    "DESCRIPTORS",
    "DISPOSITIONS",
    "SORTERS",
    "BakoboError",
    "Descriptor",
    "ErrorCode",
    "matches",
    "validate_code",
]

ARG_CAP = 80
"""Longest string an arg may reach a message as. Values arrive from the wire; a message may be
rendered or logged, so no arg is ever echoed unbounded (``error-handling.md``, rubric #7)."""


def matches(code: str, pattern: str) -> bool:
    """Test a code against a pattern, in one of three modes.

    A pattern containing ``*`` is a glob, where ``*`` spans the ``.`` separator, so ``e.*.r``
    selects every retryable code across every descriptor. A pattern ending in ``.`` is a prefix,
    the notation the standard itself uses (``e.state.``). Anything else matches exactly. The three
    can't collide: a code never ends in a dot and never contains a star.
    """
    if "*" in pattern:
        return fnmatchcase(code, pattern)
    if pattern.endswith("."):
        return code.startswith(pattern)
    return code == pattern


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

    def matches(self, pattern: str) -> bool:
        """Test this error's code against a pattern; see :func:`matches`.

        ~3p7x — a mistyped prefix such as ``e.stat.`` is not an error, it is a pattern that never
        matches, and nothing says so.
        """
        return matches(self.code, pattern)
