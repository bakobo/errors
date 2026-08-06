"""The pages the catalog publishes.

The URL shape is a wire contract this repo inherits rather than chooses: every problem+json response
carries ``"type": "https://errors.bakobo.com/<code>"`` (``this.i`` @6h5db4), so a page must exist at
exactly that path for every code. Prefix and category pages are free from the grammar, and they are
what makes the category-versus-code distinction visible to a human — the thing ``error-codes.md``
spends a whole section teaching.
"""

import re

import pytest

from bakobo.errors.catalog import build_index
from bakobo.errors.extract import Entry
from bakobo.errors.site import render


def entry(code, title="A title.", *, repo="heti", args=(), detail=None, hint=None):
    return Entry(
        code=code, title=title, repo=repo, path=f"src/{repo}/errors.py", line=1,
        symbol="X", detail=detail, args=args, hint=hint,
    )


@pytest.fixture
def pages():
    return render(build_index([
        entry(
            "e.proof.credential-sig.f",
            "The authority evidence carries a signature that does not verify.",
            detail="The signature on credential {credential} does not verify.",
            args=("credential",),
            hint="Confirm the credential was issued by the AID you expect.",
        ),
        entry("e.state.pending.escrow.r", "The event is waiting in escrow.", repo="heti"),
        entry("e.state.pending.witness.r", "The event is waiting on witnesses.", repo="tefa"),
    ]))


def test_every_code_gets_a_page_at_the_path_its_type_uri_names(pages):
    assert "e.proof.credential-sig.f.md" in pages
    assert "e.state.pending.escrow.r.md" in pages


def test_a_code_page_carries_the_code_the_title_and_the_hint(pages):
    page = pages["e.proof.credential-sig.f.md"]
    assert "e.proof.credential-sig.f" in page
    assert "The authority evidence carries a signature that does not verify." in page
    assert "Confirm the credential was issued by the AID you expect." in page


def test_a_code_page_shows_the_detail_template_and_names_its_args(pages):
    page = pages["e.proof.credential-sig.f.md"]
    assert "The signature on credential {credential} does not verify." in page
    assert "credential" in page


def test_a_code_page_says_whether_retrying_could_help(pages):
    assert "Retrying" in pages["e.state.pending.escrow.r.md"]
    assert "Retrying" in pages["e.proof.credential-sig.f.md"]


def test_a_code_page_links_to_every_prefix_above_it(pages):
    page = pages["e.state.pending.escrow.r.md"]
    assert "(/e.state./)" in page
    assert "(/e.state.pending./)" in page


def test_a_code_page_names_the_repo_that_declares_it_without_leaking_its_paths(pages):
    page = pages["e.proof.credential-sig.f.md"]
    assert "heti" in page
    assert "src/heti/errors.py" not in page


def test_every_prefix_that_appears_gets_a_page_listing_its_leaves(pages):
    page = pages["e.state.pending..md"]
    assert "e.state.pending.escrow.r" in page
    assert "e.state.pending.witness.r" in page
    assert "e.proof.credential-sig.f" not in page


def test_a_prefix_page_says_it_is_a_pattern_and_never_a_code(pages):
    assert "match pattern" in pages["e.proof..md"]


def test_every_first_descriptor_gets_a_page_even_with_no_codes_under_it(pages):
    for descriptor in ("input", "id", "grant", "feature", "proof", "party", "state", "env",
                       "self", "rule"):
        assert f"e.{descriptor}..md" in pages
    assert "A norm we enforce" in pages["e.rule..md"]


def test_a_descriptor_page_with_no_codes_says_so_rather_than_looking_broken(pages):
    assert "No codes" in pages["e.rule..md"]


def test_the_home_page_lists_every_code(pages):
    home = pages["index.md"]
    assert "e.proof.credential-sig.f" in home
    assert "e.state.pending.witness.r" in home


def test_the_home_page_teaches_the_grammar(pages):
    assert "<sorter>.<descriptor>" in pages["index.md"]


def test_the_404_page_teaches_the_grammar_to_someone_who_landed_wrong(pages):
    assert "<sorter>.<descriptor>" in pages["404.md"]
    assert "e." in pages["404.md"]


def test_the_published_index_carries_no_file_paths_or_line_numbers(pages):
    published = pages["catalog.json"]
    assert "e.proof.credential-sig.f" in published
    assert "src/heti/errors.py" not in published
    assert '"line"' not in published


def test_two_repos_declaring_one_code_are_both_named_on_its_page():
    pages = render(build_index([
        entry("e.proof.said.f", repo="heti"), entry("e.proof.said.f", repo="tefa"),
    ]))
    page = pages["e.proof.said.f.md"]
    assert "heti" in page
    assert "tefa" in page


def test_every_internal_link_points_at_a_page_that_exists(pages):
    """The renderer resolves markdown links, not absolute ones, so nothing else checks these."""
    available = {name.removesuffix(".md") + "/" for name in pages if name.endswith(".md")}
    available.add("index/")
    for name, page in pages.items():
        for target in re.findall(r"\]\((/[^)]*)\)", page):
            assert target.removeprefix("/") in available or target == "/", (
                f"{name} links to {target}, which no page answers"
            )


def test_a_detail_that_interpolates_nothing_names_no_args():
    pages = render(build_index([
        entry("e.party.refused.f", "The other party refused.",
              detail="The other party declined, and gave no reason."),
    ]))
    page = pages["e.party.refused.f.md"]
    assert "The other party declined, and gave no reason." in page
    assert "travel positionally" not in page


def test_a_code_with_no_detail_or_hint_still_renders():
    pages = render(build_index([entry("e.party.refused.f", "The other party refused.")]))
    assert "e.party.refused.f" in pages["e.party.refused.f.md"]
