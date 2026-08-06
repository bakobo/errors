"""The manifest of repos the catalog reads, and the walk over each one's shipped source.

A repo declares which paths hold registry entries, because the standard's rule is a property — a
module-scope literal — and not a place: tefa spreads its literals across eight modules under
``src/tefa/`` (``this.i`` @gvn2k2). Tests are never read whatever the globs say. heti and tefa both
construct ``ErrorCode`` in their suites, tefa's fixtures reuse a code heti owns, and a phantom
duplicate on the first run would make a real one indistinguishable from noise.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .extract import Entry, Problem, extract_module

EXCLUDED = ("tests", "test")
"""Directory names never walked, at any depth, whatever a repo's globs say."""


@dataclass(frozen=True)
class Repo:
    """One repo in the corpus: what it is called, where it lives, and what to read in it."""

    name: str
    url: str
    include: tuple[str, ...]


def read_corpus(path) -> list[Repo]:
    """Read the corpus manifest.

    A repo missing its name or its includes is refused rather than skipped: a repo silently
    contributing nothing looks exactly like a repo that mints no codes.
    """
    manifest = tomllib.loads(Path(path).read_text())
    repos = []
    for declared in manifest.get("repo", []):
        for required in ("name", "include"):
            if not declared.get(required):
                raise ValueError(
                    f"A repo in {path} declares no {required}, and every repo in the corpus needs "
                    f"one. Got: {declared}"
                )
        repos.append(Repo(
            name=declared["name"],
            url=declared.get("url", ""),
            include=tuple(declared["include"]),
        ))
    return repos


def _is_test(path: Path) -> bool:
    return any(part in EXCLUDED for part in path.parts)


def extract_repo(root, repo: Repo) -> tuple[list[Entry], list[Problem]]:
    """Read every registry entry in one checked-out repo."""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(
            f"The corpus names the repo {repo.name}, but there is no checkout at {root}."
        )

    entries: list[Entry] = []
    problems: list[Problem] = []
    seen: set[Path] = set()
    for glob in repo.include:
        matched = False
        for path in sorted(root.glob(glob)):
            matched = True
            relative = path.relative_to(root)
            if _is_test(relative) or path in seen:
                continue
            seen.add(path)
            found, refused = extract_module(
                path.read_text(), repo=repo.name, path=relative.as_posix()
            )
            entries += found
            problems += refused
        if not matched:
            problems.append(Problem(
                repo.name, glob, 1, None,
                f"the include glob {glob!r} matches nothing in {repo.name}, so either the repo "
                f"moved its source or the corpus manifest is stale",
            ))

    entries.sort(key=lambda entry: (entry.path, entry.line))
    return entries, problems
