"""Render the catalog as the pages it publishes.

One page per code, at exactly the path that code's ``type`` URI names — that is a wire contract this
repo inherits rather than chooses (``this.i`` @6h5db4). One page per prefix as well, which the
grammar gives away for free and which is what makes the category-versus-code distinction visible to
a human: ``e.proof.`` has a page saying it is a pattern, and no page pretending it is a code.

The published pages name the repo that declares a code and not the file it sits in. The catalog is
public and the repos it reads are not, so a path and a line number are for the build, not for the
web.
"""

from __future__ import annotations

import json

from .taxonomy import DESCRIPTORS, DISPOSITIONS, GRAMMAR, SORTERS

DISPOSITION_SENTENCE = {
    "f": "Retrying the same thing changes nothing.",
    "r": "Retrying may succeed — this one is worth another attempt.",
}

GRAMMAR_LESSON = f"""A Bakobo error code reads left to right, growing more specific:

```
{GRAMMAR}
```

The **sorter** is `e` for an error, whose consequences are clear, or `w` for a warning, whose
consequences need someone's judgment. The **descriptor** says what the obstacle was, and comes from
a closed set of ten. The **disposition** is the last token, `f` if retrying changes nothing and `r`
if it might help — last, so that `e.state.` matches every target-condition failure whichever way it
disposes.

A first descriptor is a category, never a code. `e.proof.` names a kind of obstacle rather than one
condition, so every code carries at least one sub-descriptor and a bare descriptor appears only as
a pattern to match against.
"""


def _link(code: str) -> str:
    return f"[`{code}`](/{code}/)"


def _origins(document: dict) -> str:
    repos = sorted({origin["repo"] for origin in document["origins"]})
    return " and ".join(f"**{repo}**" for repo in repos)


def _code_page(document: dict) -> str:
    code = document["code"]
    descriptor = document["descriptor"]
    lines = [
        f"# `{code}`",
        "",
        document["title"],
        "",
        DISPOSITION_SENTENCE[document["disposition"]],
        "",
    ]

    if document["detail"]:
        lines += [
            "## What a response says",
            "",
            "```",
            document["detail"],
            "```",
            "",
        ]
        if document["args"]:
            named = ", ".join(f"`{name}`" for name in document["args"])
            lines += [
                f"The placeholders are filled from {named}, which travel positionally in the "
                f"`args` member of the response.",
                "",
            ]

    if document["hint"]:
        lines += ["## What to do", "", document["hint"], ""]

    lines += [
        "## Where it sits",
        "",
        "| | |",
        "|---|---|",
        f"| Sorter | `{document['sorter']}` — {SORTERS[document['sorter']]} |",
        f"| Obstacle | [`e.{descriptor}.`](/e.{descriptor}./) — {DESCRIPTORS[descriptor].obstacle} |",
        f"| Disposition | `{document['disposition']}` — "
        f"{DISPOSITIONS[document['disposition']]} |",
        "",
        "A handler can match this code exactly, or by any prefix above it: "
        + ", ".join(
            f"[`{prefix}`](/{prefix}/)"
            for prefix in document["prefixes"]
            if prefix.count(".") > 1  # `e.` is a real pattern, but its page is the home page
        )
        + ".",
        "",
        f"Declared in {_origins(document)}.",
        "",
    ]
    return "\n".join(lines)


def _prefix_page(prefix: str, documents: list[dict]) -> str:
    descriptor = prefix.split(".")[1]
    lines = [
        f"# `{prefix}`",
        "",
        f"`{prefix}` is a match pattern, never a code. It selects every code below it, including "
        f"ones minted after your handler was written.",
        "",
    ]
    if prefix.count(".") == 2:
        lines += [f"**The obstacle:** {DESCRIPTORS[descriptor].obstacle}.", ""]
        standard = DESCRIPTORS[descriptor].subs
        if standard:
            named = ", ".join(f"`{sub}`" for sub in standard)
            lines += [
                f"The standard sub-descriptors under this obstacle are {named}. A repo mints "
                f"deeper leaves of its own without asking; it may not add a first descriptor.",
                "",
            ]
        else:
            lines += [
                "This obstacle has no standard sub-descriptors, so every leaf under it is one a "
                "repo minted for itself.",
                "",
            ]

    lines += ["## Codes under this prefix", ""]
    if documents:
        lines += [
            f"- {_link(d['code'])} — {d['title']}" for d in documents
        ]
    else:
        lines.append("No codes have been minted under this prefix yet.")
    lines.append("")
    return "\n".join(lines)


def _home_page(documents: list[dict]) -> str:
    lines = [
        "# Bakobo error codes",
        "",
        "Every error Bakobo reports carries a stable symbolic code, and every code has a page "
        "here. If you arrived from the `type` member of a problem+json response, the page you "
        "want is the code itself.",
        "",
        "## How to read a code",
        "",
        GRAMMAR_LESSON,
        "## The ten obstacles",
        "",
        "| Descriptor | The obstacle |",
        "|---|---|",
    ]
    lines += [
        f"| [`e.{name}.`](/e.{name}./) | {DESCRIPTORS[name].obstacle} |" for name in DESCRIPTORS
    ]
    lines += ["", f"## Every code ({len(documents)})", "", "| Code | Title |", "|---|---|"]
    lines += [f"| {_link(d['code'])} | {d['title']} |" for d in documents]
    lines.append("")
    return "\n".join(lines)


def _not_found_page() -> str:
    return "\n".join([
        "# No page for that code",
        "",
        "Nothing here answers to that path. Either the code has not been minted, or it was "
        "mistyped, or it is a match pattern rather than a code — a pattern ends in a dot.",
        "",
        "## How to read a code",
        "",
        GRAMMAR_LESSON,
        "Start from [the full list](/) if you are looking for something specific.",
        "",
    ])


def _published(index: dict) -> str:
    """The machine-readable catalog, with the build's file paths and line numbers left out."""
    codes = []
    for document in index["codes"]:
        published = {key: value for key, value in document.items() if key != "origins"}
        published["repos"] = sorted({origin["repo"] for origin in document["origins"]})
        codes.append(published)
    return json.dumps({"codes": codes}, indent=2) + "\n"


def render(index: dict) -> dict[str, str]:
    """Every page the site is built from, keyed by its path under the docs root."""
    documents = index["codes"]
    pages = {document["code"] + ".md": _code_page(document) for document in documents}

    prefixes: dict[str, list[dict]] = {f"e.{name}.": [] for name in DESCRIPTORS}
    prefixes.update({f"w.{name}.": [] for name in DESCRIPTORS})
    for document in documents:
        for prefix in document["prefixes"]:
            prefixes.setdefault(prefix, []).append(document)

    for prefix, under in prefixes.items():
        if prefix.count(".") == 1:  # the sorter alone, `e.`, which the home page already is
            continue
        if not under and prefix.startswith("w."):  # only show a warning branch someone uses
            continue
        pages[prefix + ".md"] = _prefix_page(prefix, under)

    pages["index.md"] = _home_page(documents)
    pages["404.md"] = _not_found_page()
    pages["catalog.json"] = _published(index)
    return pages
