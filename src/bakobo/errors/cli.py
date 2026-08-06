"""The command CI runs.

Everything here fails loudly. A catalog that quietly drops an entry it could not read, or that
picks one of two disagreeing declarations, disagrees with the code that raises — which is the one
thing the projection exists to avoid (``this.i`` @tjs63f).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import build_index, collisions
from .corpus import extract_repo, read_corpus

HERE = Path(__file__).resolve().parents[3]
"""The repo root, when running from a source checkout."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bakobo-errors",
        description="Build the Bakobo error catalog from the registries in source.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [
        ("index", "extract every registry into index.json"),
        ("check", "extract every registry and report, writing nothing"),
    ]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--corpus", default=HERE / "corpus.toml", type=Path,
                             help="the manifest naming the repos to read")
        command.add_argument("--checkouts", default=HERE.parent, type=Path,
                             help="the directory holding a checkout of each repo")
        if name == "index":
            command.add_argument("--out", default=HERE / "index.json", type=Path,
                                 help="where to write the index")
    return parser


def main(argv=None) -> int:
    """Build or check the catalog; return the process exit status."""
    options = _parser().parse_args(argv)

    entries, problems = [], []
    for repo in read_corpus(options.corpus):
        try:
            found, refused = extract_repo(Path(options.checkouts) / repo.name, repo)
        except FileNotFoundError as absent:
            print(absent, file=sys.stderr)
            return 1
        entries += found
        problems += refused

    for problem in problems:
        where = f"{problem.repo} {problem.path}:{problem.line}"
        symbol = f" {problem.symbol}" if problem.symbol else ""
        print(f"{where}{symbol} — {problem.reason}", file=sys.stderr)

    reported = collisions(entries)
    for collision in reported:
        print(collision, file=sys.stderr if collision.fatal else sys.stdout)

    if problems or any(collision.fatal for collision in reported):
        print(
            f"Refused to publish: {len(problems)} unreadable declaration(s) and "
            f"{sum(c.fatal for c in reported)} collision(s).",
            file=sys.stderr,
        )
        return 1

    index = build_index(entries)
    print(f"{len(index['codes'])} codes from {len({e.repo for e in entries})} repos.")
    if options.command == "index":
        options.out.write_text(json.dumps(index, indent=2, sort_keys=False) + "\n")
        print(f"Wrote {options.out}.")
    return 0
