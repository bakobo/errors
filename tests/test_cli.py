"""The command CI runs.

Its job is to fail loudly. A catalog that quietly drops an unreadable entry, or that picks one of
two disagreeing declarations, is worse than no catalog — it disagrees with the code that raises,
which is the thing the whole projection exists to avoid (``this.i`` @tjs63f).

``reconcile`` is covered twice over, deliberately. The tests taking ``standard_text`` read the real
``error-codes.md`` and skip where ``bakobo/dev`` is not checked out beside this repo, which is the
case in CI; the ones taking the synthetic table do not skip anywhere. No line may be reachable only
by a skippable test, or the 100% gate passes here and fails in CI on coverage rather than on a
defect.
"""

import json
import textwrap

import pytest

from bakobo.errors.cli import main
from test_reconcile import STANDARD as SYNTHETIC_STANDARD

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


def pages(corpus):
    return main([
        "pages",
        "--corpus", str(corpus / "corpus.toml"),
        "--checkouts", str(corpus / "checkouts"),
        "--out", str(corpus / "build" / "docs"),
        "--static", str(corpus / "static"),
    ])


def test_pages_writes_a_page_for_every_code_and_the_pages_above_it(corpus):
    assert pages(corpus) == 0
    written = {path.name for path in (corpus / "build" / "docs").iterdir()}
    assert "e.input.missing.sig.f.md" in written
    assert "e.input.missing..md" in written
    assert {"index.md", "404.md", "catalog.json"} <= written


def test_pages_copies_hand_written_static_files_in_alongside(corpus):
    (corpus / "static" / "assets").mkdir(parents=True)
    (corpus / "static" / "CNAME").write_text("errors.example.com\n")
    (corpus / "static" / "assets" / "brand.css").write_text("/* brand */\n")
    assert pages(corpus) == 0
    assert (corpus / "build" / "docs" / "CNAME").read_text() == "errors.example.com\n"
    assert (corpus / "build" / "docs" / "assets" / "brand.css").exists()


def test_a_rebuild_removes_the_page_of_a_code_that_was_retired(corpus):
    assert pages(corpus) == 0
    stale = corpus / "build" / "docs" / "e.party.gone.f.md"
    stale.write_text("# a code that no longer exists")
    assert pages(corpus) == 0
    assert not stale.exists()


def test_finalize_promotes_the_built_404_over_the_renderers_stock_one(tmp_path):
    built = tmp_path / "site"
    (built / "404").mkdir(parents=True)
    (built / "404" / "index.html").write_text("<h1>How to read a code</h1>")
    (built / "404.html").write_text("<h1>404 - Not found</h1>")
    assert main(["finalize", "--site", str(built)]) == 0
    assert (built / "404.html").read_text() == "<h1>How to read a code</h1>"


def test_finalize_fails_rather_than_silently_leaving_the_stock_404(tmp_path, capsys):
    assert main(["finalize", "--site", str(tmp_path / "site")]) == 1
    assert "build the site first" in capsys.readouterr().err


def test_reconcile_exits_zero_when_the_table_and_the_data_agree(tmp_path):
    standard = tmp_path / "error-codes.md"
    standard.write_text(textwrap.dedent(SYNTHETIC_STANDARD))
    assert main(["reconcile", "--standard", str(standard)]) == 0


def test_reconcile_names_every_disagreement_and_says_which_artifact_is_wrong(tmp_path, capsys):
    standard = tmp_path / "error-codes.md"
    standard.write_text(textwrap.dedent(SYNTHETIC_STANDARD).replace("| `rule` |", "| `norm` |"))
    assert main(["reconcile", "--standard", str(standard)]) == 1
    reported = capsys.readouterr().err
    assert "norm" in reported
    assert "taxonomy.py is the defect" in reported


def test_reconcile_passes_against_the_real_standard(tmp_path, standard_text):
    standard = tmp_path / "error-codes.md"
    standard.write_text(standard_text)
    assert main(["reconcile", "--standard", str(standard)]) == 0


def test_reconcile_fails_when_the_standard_and_the_data_have_drifted(tmp_path, standard_text,
                                                                     capsys):
    standard = tmp_path / "error-codes.md"
    standard.write_text(standard_text.replace("| `rule` |", "| `norm` |"))
    assert main(["reconcile", "--standard", str(standard)]) == 1
    reported = capsys.readouterr().err
    assert "norm" in reported
    assert "rule" in reported


def test_reconcile_fails_rather_than_passing_when_the_standard_is_absent(tmp_path, capsys):
    assert main(["reconcile", "--standard", str(tmp_path / "nowhere.md")]) == 1
    assert "no standard" in capsys.readouterr().err


def test_check_fails_on_the_same_things_index_does(corpus):
    (corpus / "checkouts" / "pkg" / "src" / "pkg" / "more.py").write_text(UNREADABLE)
    assert main([
        "check",
        "--corpus", str(corpus / "corpus.toml"),
        "--checkouts", str(corpus / "checkouts"),
    ]) == 1
