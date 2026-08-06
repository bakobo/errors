"""Check the taxonomy data against the table in the standard it is a copy of.

``taxonomy.py`` exists so the validator and the catalog read a machine-checkable artifact instead of
a markdown table whose formatting a release would depend on (``this.i`` @gzkwg6). The cost of that
choice is two artifacts saying one thing, which is the arrangement that drifts. This is what makes
the split safe rather than merely convenient: the standard is right, and a difference is a defect in
the data file.
"""

from __future__ import annotations

import re

from .taxonomy import DESCRIPTORS, Descriptor

ROW = re.compile(r"^\|\s*`(?P<name>[a-z]+)`\s*\|(?P<obstacle>[^|]+)\|(?P<subs>[^|]*)\|\s*$")
SUB = re.compile(r"`\.([a-z-]+)`")


def parse_standard(text: str) -> dict[str, Descriptor]:
    """Read the taxonomy table out of ``error-codes.md``.

    Rows are recognised by their shape — a backticked bare descriptor in the first cell — rather
    than by counting tables, so prose or another table moving above this one does not silently
    change what gets read.
    """
    parsed: dict[str, Descriptor] = {}
    for line in text.splitlines():
        row = ROW.match(line.strip())
        if row:
            parsed[row["name"]] = Descriptor(
                obstacle=row["obstacle"].strip(),
                subs=tuple(SUB.findall(row["subs"])),
            )
    if not parsed:
        raise ValueError(
            "Found no taxonomy table in the standard. Either the table's shape changed or the "
            "wrong file was read; the rows this looks for are | `input` | obstacle | subs |."
        )
    return parsed


def disagreements(parsed: dict[str, Descriptor]) -> list[str]:
    """Every way the standard's table and this package's data fail to say the same thing."""
    found = []
    for name in sorted(set(parsed) | set(DESCRIPTORS)):
        if name not in DESCRIPTORS:
            found.append(
                f"{name!r} is a first descriptor in the standard and is missing from taxonomy.py."
            )
            continue
        if name not in parsed:
            found.append(
                f"{name!r} is a first descriptor in taxonomy.py and is not in the standard."
            )
            continue
        standard, data = parsed[name], DESCRIPTORS[name]
        if standard.obstacle != data.obstacle:
            found.append(
                f"{name!r} names the obstacle {standard.obstacle!r} in the standard and "
                f"{data.obstacle!r} in taxonomy.py."
            )
        if standard.subs != data.subs:
            found.append(
                f"{name!r} has the standard sub-descriptors {standard.subs} in the standard and "
                f"{data.subs} in taxonomy.py."
            )
    return found
