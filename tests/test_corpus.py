"""Reading the manifest, and walking each repo's shipped source.

Extraction is scoped by declared globs rather than by a registry-filename convention, because tefa
already spreads its literals across eight modules (``this.i`` @gvn2k2). Excluding tests is the
load-bearing half: heti and tefa both construct ``ErrorCode`` in their suites, and a fixture that
borrows a code another repo owns would otherwise arrive as a phantom duplicate.
"""

import pytest

from bakobo.errors.corpus import Repo, extract_repo, read_corpus

MANIFEST = """
[[repo]]
name = "heti"
url = "https://github.com/bakobo/heti"
include = ["src/**/*.py"]

[[repo]]
name = "tefa"
url = "https://github.com/bakobo/tefa"
include = ["src/**/*.py", "extras/*.py"]
"""

ENTRY = '''
from bakobo.errors import ErrorCode

NO_SIG = ErrorCode("e.input.missing.sig.f", "The request carries no signature to check.")
'''


def write(root, relative, text=ENTRY):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_the_manifest_reads_into_repos(tmp_path):
    manifest = tmp_path / "corpus.toml"
    manifest.write_text(MANIFEST)
    heti, tefa = read_corpus(manifest)
    assert heti == Repo(name="heti", url="https://github.com/bakobo/heti", include=("src/**/*.py",))
    assert tefa.include == ("src/**/*.py", "extras/*.py")


def test_a_repo_without_a_name_is_refused_rather_than_skipped(tmp_path):
    manifest = tmp_path / "corpus.toml"
    manifest.write_text('[[repo]]\nurl = "https://example.com"\n')
    with pytest.raises(ValueError, match="name"):
        read_corpus(manifest)


def test_a_repo_without_includes_is_refused_because_silence_would_mean_no_codes(tmp_path):
    manifest = tmp_path / "corpus.toml"
    manifest.write_text('[[repo]]\nname = "heti"\nurl = "https://example.com"\n')
    with pytest.raises(ValueError, match="include"):
        read_corpus(manifest)


def test_walking_a_repo_finds_entries_under_every_declared_glob(tmp_path):
    write(tmp_path, "src/pkg/errors.py")
    write(tmp_path, "src/pkg/deep/more.py")
    entries, problems = extract_repo(tmp_path, Repo("pkg", "u", ("src/**/*.py",)))
    assert problems == []
    assert {e.path for e in entries} == {"src/pkg/errors.py", "src/pkg/deep/more.py"}


def test_paths_are_recorded_relative_to_the_repo_root_so_they_link(tmp_path):
    write(tmp_path, "src/pkg/errors.py")
    entries, _ = extract_repo(tmp_path, Repo("pkg", "u", ("src/**/*.py",)))
    assert entries[0].path == "src/pkg/errors.py"
    assert entries[0].repo == "pkg"


def test_tests_are_never_walked_even_when_a_glob_would_reach_them(tmp_path):
    write(tmp_path, "src/pkg/errors.py")
    write(tmp_path, "tests/test_errors.py")
    write(tmp_path, "src/pkg/tests/test_inner.py")
    entries, problems = extract_repo(tmp_path, Repo("pkg", "u", ("**/*.py",)))
    assert [e.path for e in entries] == ["src/pkg/errors.py"]
    assert problems == []


def test_a_repo_that_is_not_checked_out_is_an_error_rather_than_an_empty_result(tmp_path):
    with pytest.raises(FileNotFoundError, match="pkg"):
        extract_repo(tmp_path / "absent", Repo("pkg", "u", ("src/**/*.py",)))


def test_a_glob_that_matches_nothing_is_reported_as_a_problem(tmp_path):
    write(tmp_path, "src/pkg/errors.py")
    _, problems = extract_repo(tmp_path, Repo("pkg", "u", ("src/**/*.py", "nowhere/*.py")))
    assert "nowhere/*.py" in problems[0].reason


def test_the_walk_is_sorted_so_two_runs_produce_the_same_index(tmp_path):
    for name in ("zeta.py", "alpha.py", "mid.py"):
        write(tmp_path, f"src/pkg/{name}")
    entries, _ = extract_repo(tmp_path, Repo("pkg", "u", ("src/**/*.py",)))
    assert [e.path for e in entries] == [
        "src/pkg/alpha.py", "src/pkg/mid.py", "src/pkg/zeta.py",
    ]


def test_one_file_matched_by_two_globs_is_only_walked_once(tmp_path):
    write(tmp_path, "src/pkg/errors.py")
    entries, _ = extract_repo(tmp_path, Repo("pkg", "u", ("src/**/*.py", "src/pkg/*.py")))
    assert len(entries) == 1
