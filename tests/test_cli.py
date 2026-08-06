"""The command CI runs.

Its job is to fail loudly. A catalog that quietly drops an unreadable entry, or that picks one of
two disagreeing declarations, is worse than no catalog — it disagrees with the code that raises,
which is the thing the whole projection exists to avoid (``this.i`` @tjs63f).
"""

import json

import pytest

from bakobo.errors.cli import main

MANIFEST = """
[[repo]]
name = "pkg"
url = "https://example.com/pkg"
include = ["src/**/*.py"]
"""

GOOD = '''
from bakobo.errors import ErrorCode

NO_SIG = ErrorCode("e.input.missing.sig.f", "The request carries no signature to check.")
STALE = ErrorCode("e.state.missing.kel.r", "The evidence doesn't reach that far.")
'''

UNREADABLE = '''
from bakobo.errors import ErrorCode

HINT = "Shared advice."
SHARED = ErrorCode("e.input.format.sig.f", "A title.", hint=HINT)
'''


@pytest.fixture
def corpus(tmp_path):
    """A checkouts directory holding one repo, plus the manifest that names it."""
    (tmp_path / "corpus.toml").write_text(MANIFEST)
    source = tmp_path / "checkouts" / "pkg" / "src" / "pkg"
    source.mkdir(parents=True)
    (source / "errors.py").write_text(GOOD)
    return tmp_path


def run(corpus, *extra):
    return main([
        "index",
        "--corpus", str(corpus / "corpus.toml"),
        "--checkouts", str(corpus / "checkouts"),
        "--out", str(corpus / "index.json"),
        *extra,
    ])


def test_a_clean_corpus_exits_zero_and_writes_the_index(corpus, capsys):
    assert run(corpus) == 0
    index = json.loads((corpus / "index.json").read_text())
    assert [c["code"] for c in index["codes"]] == [
        "e.input.missing.sig.f", "e.state.missing.kel.r",
    ]
    assert "2 codes" in capsys.readouterr().out


def test_the_index_is_written_as_stable_json_so_a_rebuild_is_a_no_op(corpus):
    run(corpus)
    first = (corpus / "index.json").read_bytes()
    run(corpus)
    assert (corpus / "index.json").read_bytes() == first


def test_an_unreadable_entry_fails_the_run_and_says_where_it_is(corpus, capsys):
    (corpus / "checkouts" / "pkg" / "src" / "pkg" / "more.py").write_text(UNREADABLE)
    assert run(corpus) == 1
    reported = capsys.readouterr().err
    assert "src/pkg/more.py:5" in reported
    assert "SHARED" in reported


def test_a_failed_run_does_not_leave_a_stale_index_behind(corpus):
    (corpus / "checkouts" / "pkg" / "src" / "pkg" / "more.py").write_text(UNREADABLE)
    run(corpus)
    assert not (corpus / "index.json").exists()


def test_a_fatal_collision_fails_the_run(corpus, capsys):
    (corpus / "checkouts" / "pkg" / "src" / "pkg" / "more.py").write_text(
        'from bakobo.errors import ErrorCode\n'
        'AGAIN = ErrorCode("e.input.missing.sig.f", "A different title.")\n'
    )
    assert run(corpus) == 1
    assert "e.input.missing.sig.f" in capsys.readouterr().err


def test_prose_divergence_is_reported_but_the_run_still_succeeds(corpus, capsys):
    (corpus / "checkouts" / "pkg" / "src" / "pkg" / "more.py").write_text(
        'from bakobo.errors import ErrorCode\n'
        'AGAIN = ErrorCode("e.input.missing.sig.f", '
        '"The request carries no signature to check.", hint="Sign it.")\n'
    )
    assert run(corpus) == 0
    assert "hint" in capsys.readouterr().out


def test_a_missing_checkout_fails_with_the_repo_named(corpus, capsys):
    assert main([
        "index",
        "--corpus", str(corpus / "corpus.toml"),
        "--checkouts", str(corpus / "nowhere"),
        "--out", str(corpus / "index.json"),
    ]) == 1
    assert "pkg" in capsys.readouterr().err


def test_check_validates_without_writing_anything(corpus):
    assert main([
        "check",
        "--corpus", str(corpus / "corpus.toml"),
        "--checkouts", str(corpus / "checkouts"),
    ]) == 0
    assert not (corpus / "index.json").exists()


def test_check_fails_on_the_same_things_index_does(corpus):
    (corpus / "checkouts" / "pkg" / "src" / "pkg" / "more.py").write_text(UNREADABLE)
    assert main([
        "check",
        "--corpus", str(corpus / "corpus.toml"),
        "--checkouts", str(corpus / "checkouts"),
    ]) == 1
