"""Keeping the data file and the standard's own table in step.

``taxonomy.py`` is the machine-readable form of a table that lives in prose in
``dev/standards/error-codes.md`` (``this.i`` @gzkwg6). Two artifacts saying one thing is exactly the
arrangement that drifts, so the split is only safe if something reconciles them — and that check has
to read the standard as it is actually written, not as we wish it were.
"""

import textwrap

import pytest

from bakobo.errors.reconcile import disagreements, parse_standard

STANDARD = """
Some preamble that mentions | pipes | in passing.

| Descriptor | The obstacle | Sub-descriptors |
|---|---|---|
| `input` | What you sent | `.missing` `.format` `.range` `.multi` |
| `id` | Who you are (authentication) | `.missing` `.invalid` `.expired` |
| `grant` | What you may do (delegated authority) | `.missing` `.scope` `.quota` |
| `feature` | The availability of a capability | `.unsupported` `.unlicensed` `.deprecated` |
| `proof` | Supplied material fails verification against a reference | — |
| `party` | Another actor's conduct or choice | — |
| `state` | The condition of the target | `.conflict` `.missing` `.pending` |
| `env` | A system we depend on that did not deliver | — |
| `self` | Us — our fault, or we cannot attribute it | `.resource` `.config` `.corrupt` `.unknown` |
| `rule` | A norm we enforce, neither authority nor verification | — |

Trailing prose, with | another | table | that is not the taxonomy.
"""


def parse(text=STANDARD):
    return parse_standard(textwrap.dedent(text))


def replace(parsed, name, obstacle=None, subs=None):
    original = parsed[name]
    parsed[name] = type(original)(
        obstacle if obstacle is not None else original.obstacle,
        subs if subs is not None else original.subs,
    )
    return parsed


def test_the_table_reads_into_descriptors_obstacles_and_subs():
    parsed = parse()
    assert parsed["input"].subs == ("missing", "format", "range", "multi")
    assert parsed["input"].obstacle == "What you sent"
    assert parsed["env"].subs == ()
    assert len(parsed) == 10


def test_a_standard_with_no_taxonomy_table_is_an_error_not_an_empty_result():
    with pytest.raises(ValueError, match="no taxonomy table"):
        parse("# A document with no table in it at all.\n")


def test_a_standard_that_agrees_with_the_data_reports_nothing():
    assert disagreements(parse()) == []


def test_a_descriptor_only_the_standard_has_is_reported():
    parsed = parse()
    parsed["novel"] = parsed.pop("rule")
    found = " ".join(disagreements(parsed))
    assert "novel" in found
    assert "rule" in found


def test_a_renamed_obstacle_is_reported():
    found = " ".join(disagreements(replace(parse(), "input", obstacle="Something else entirely")))
    assert "input" in found
    assert "obstacle" in found


def test_a_sub_descriptor_added_to_the_standard_alone_is_reported():
    assert "env" in " ".join(disagreements(replace(parse(), "env", subs=("timeout",))))


def test_reordered_subs_are_reported_because_the_order_is_the_documents():
    reordered = replace(parse(), "state", subs=("pending", "conflict", "missing"))
    assert disagreements(reordered) != []


def test_the_real_standard_agrees_with_the_data(standard_text):
    assert disagreements(parse_standard(standard_text)) == []
