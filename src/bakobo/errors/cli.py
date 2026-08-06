"""The command CI runs.

Everything here fails loudly. A catalog that quietly drops an entry it could not read, or that
picks one of two disagreeing declarations, disagrees with the code that raises — which is the one
thing the projection exists to avoid (``this.i`` @tjs63f).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .catalog import build_index, collisions
from .corpus import extract_repo, read_corpus
from .reconcile import disagreements, parse_standard
from .site import render

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
        ("pages", "extract every registry and write the markdown the site is built from"),
        ("finalize", "put the built site's own 404 page where a web server will look for it"),
        ("reconcile", "check the taxonomy data against the table in the standard"),
    ]:
        command = commands.add_parser(name, help=help_text)
        if name == "finalize":
            command.add_argument("--site", default=HERE / "site", type=Path,
                                 help="the built site")
            continue
        if name == "reconcile":
            command.add_argument(
                "--standard", type=Path,
                default=HERE.parent / "dev" / "standards" / "error-codes.md",
                help="the standard whose taxonomy table the data must match",
            )
            continue
        command.add_argument("--corpus", default=HERE / "corpus.toml", type=Path,
                             help="the manifest naming the repos to read")
        command.add_argument("--checkouts", default=HERE.parent, type=Path,
                             help="the directory holding a checkout of each repo")
        if name == "index":
            command.add_argument("--out", default=HERE / "index.json", type=Path,
                                 help="where to write the index")
        if name == "pages":
            command.add_argument("--out", default=HERE / "build" / "docs", type=Path,
                                 help="the docs root to write the generated pages into")
            command.add_argument("--static", default=HERE / "static", type=Path,
                                 help="hand-written files copied in alongside the generated pages")
    return parser


def _finalize(site: Path) -> int:
    """Replace the renderer's stock 404 with the one that teaches the grammar.

    Zensical renders ``404.md`` to ``404/index.html`` like any other page, and separately writes a
    bare ``404.html`` at the root — which is the only one a web server ever serves. Someone who
    searched for a code and landed wrong is exactly the reader the grammar lesson is for, so the
    real page is promoted over the stock one. Its asset URLs are absolute, so it works from the
    root unchanged.
    """
    rendered = site / "404" / "index.html"
    if not rendered.is_file():
        print(f"There is no built 404 page at {rendered}; build the site first.", file=sys.stderr)
        return 1
    shutil.copyfile(rendered, site / "404.html")
    print(f"Promoted {rendered} to {site / '404.html'}.")
    return 0


def _reconcile(standard: Path) -> int:
    """Fail if the taxonomy data and the standard's table have drifted apart."""
    if not standard.is_file():
        print(
            f"There is no standard at {standard}. Check out bakobo/dev beside this repo, or pass "
            f"--standard.",
            file=sys.stderr,
        )
        return 1
    found = disagreements(parse_standard(standard.read_text()))
    for line in found:
        print(line, file=sys.stderr)
    if found:
        print(
            "The standard is right and taxonomy.py is the defect; adding a first descriptor is a "
            "change to the standard, not to a data file.",
            file=sys.stderr,
        )
        return 1
    print(f"The taxonomy data matches {standard}.")
    return 0


def main(argv=None) -> int:
    """Build or check the catalog; return the process exit status."""
    options = _parser().parse_args(argv)
    if options.command == "finalize":
        return _finalize(options.site)
    if options.command == "reconcile":
        return _reconcile(options.standard)

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
    if options.command == "pages":
        pages = render(index)
        if options.out.exists():
            shutil.rmtree(options.out)
        options.out.mkdir(parents=True)
        if options.static.is_dir():
            shutil.copytree(options.static, options.out, dirs_exist_ok=True)
        for name, content in pages.items():
            (options.out / name).write_text(content)
        print(f"Wrote {len(pages)} pages into {options.out}.")
    return 0
