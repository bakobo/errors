"""The pages the catalog publishes.

The URL shape is a wire contract this repo inherits rather than chooses: every problem+json response
carries ``"type": "https://errors.bakobo.com/<code>"`` (``this.i`` @6h5db4), so a page must exist at
exactly that path for every code. Prefix and category pages are free from the grammar, and they are
what makes the category-versus-code distinction visible to a human — the thing ``error-codes.md``
spends a whole section teaching.

The escaping tests at the foot of this file render each page through the real extension set, read
out of ``zensical.toml``, rather than asserting on the markdown. A registry entry is prose lifted
from another repo, the renderer passes raw HTML through, and what matters is what reaches a reader's
browser — so the oracle has to be the rendered page (``this.i`` @twdcue2y).
"""

import html as htmllib
import json
import re
import tomllib
from pathlib import Path

import markdown
import pytest

from bakobo.errors.catalog import build_index
from bakobo.errors.extract import Entry
from bakobo.errors.site import render

ROOT = Path(__file__).resolve().parents[1]


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


# --- Escaping: what a registry's prose may do to the published page --------------------------------
#
# Every title, detail and hint is a literal lifted out of another repo's source, so anything that can
# land an error code anywhere in the corpus can put characters on errors.bakobo.com. The renderer
# passes raw HTML through, which makes an unescaped title a stored-XSS sink (``this.i`` @twdcue2y).

SCRIPT = "<script>alert('xss')</script>"
IMAGE = "<img src=x onerror=alert('xss')>"
HANDLER = 'a title {: onclick="alert(1)" }'
JS_LINK = "[click me](javascript:alert(1))"

BLOCK_MARKERS = (
    "---", "-----", "***", "___", "===",  # thematic breaks, and a setext rule
    "# h", "#h", "###### h6", "######h6",  # headings: python-markdown wants no space after the hash
    "> quote", ": def", "+ plus", "- dash", "-dash",  # blockquote, definition, bullets
    "1. one", "2) two", "|cell", "~~~", "~~~~",  # ordered lists, a table cell, superfences
    '!!! danger "boom"', '??? note "x"',  # admonition and details
    "    indented", "<!-- c -->", "* star", "_under_",
)
"""Every way a line can open and stop being the line it was.

Enumerated rather than reasoned about, because reasoning about it is what got this wrong once:
``---`` renders as a thematic break and the title disappears, and ``#h`` is a heading even though
python-markdown is usually described as wanting a space after the hash.
"""

FENCE_MARKERS = ("---", "~~~", "```", "````", "   ```", "~~~~~~", "a\n```\nb")
"""Bodies that are themselves a fence or a block marker, for the sinks that build a delimiter."""


def _extensions(table, prefix=""):
    """The markdown extensions ``zensical.toml`` turns on, as python-markdown names.

    TOML nests ``pymdownx.superfences`` as a sub-table; python-markdown wants the dotted name back.
    A table whose every value is itself a non-empty table is a namespace, and anything else is one
    extension's config.
    """
    names = []
    for key, value in table.items():
        full = f"{prefix}{key}"
        if isinstance(value, dict) and value and all(isinstance(v, dict) for v in value.values()):
            names += _extensions(value, f"{full}.")
        else:
            names.append(full)
    return names


@pytest.fixture(scope="module")
def to_html():
    """Render a generated page the way the site does, with the real config's extensions."""
    config = tomllib.loads((ROOT / "zensical.toml").read_text())
    renderer = markdown.Markdown(extensions=_extensions(config["project"]["markdown_extensions"]))

    def render_page(page):
        renderer.reset()
        return renderer.convert(page)

    return render_page


def reading(rendered):
    """The characters a reader sees, with the markup taken away."""
    return htmllib.unescape(re.sub(r"<[^>]+>", "", rendered))


def markup(rendered):
    """The tags alone, with every text node taken away.

    A payload that survived escaping still reads back as ``onclick=`` or ``javascript:`` inside a
    text node, which is exactly where it is harmless. What must not contain either is a tag.
    """
    return re.sub(r"(?s)>[^<]*<", "><", rendered)


def pages_for(**fields):
    return render(build_index([entry("e.input.format.f", **fields)]))


def showing_the_title(pages):
    """Every page that puts a title on the screen: its own, its prefix's, and the index."""
    return [pages["e.input.format.f.md"], pages["e.input..md"], pages["index.md"]]


def test_a_script_in_a_title_is_inert_on_every_page_that_shows_a_title(to_html):
    for page in showing_the_title(pages_for(title=SCRIPT)):
        rendered = to_html(page)
        assert "<script" not in rendered
        assert SCRIPT in reading(rendered)


def test_an_image_handler_in_a_title_is_inert_on_every_page_that_shows_a_title(to_html):
    for page in showing_the_title(pages_for(title=IMAGE)):
        rendered = to_html(page)
        assert "<img" not in rendered


def test_a_script_in_a_detail_cannot_break_out_of_its_code_block(to_html):
    detail = f"A template.\n```\n{SCRIPT}\n```\nstill inside"
    rendered = to_html(pages_for(title="A title.", detail=detail)["e.input.format.f.md"])
    assert "<script" not in rendered
    assert reading(rendered).count(SCRIPT) == 1


def test_a_detail_with_no_backticks_still_renders_as_a_code_block(to_html):
    rendered = to_html(
        pages_for(title="A title.", detail="The signature on {credential} does not verify.")["e.input.format.f.md"]
    )
    assert "<code>" in rendered
    assert "The signature on {credential} does not verify." in reading(rendered)


def test_a_script_in_a_hint_is_inert(to_html):
    rendered = to_html(pages_for(title="A title.", hint=f"Try {SCRIPT} again.")["e.input.format.f.md"])
    assert "<script" not in rendered
    assert SCRIPT in reading(rendered)


def test_a_pipe_in_a_title_neither_breaks_a_table_row_nor_injects_a_cell(to_html):
    rendered = to_html(pages_for(title="Use | or ||, never |||.")["index.md"])
    row = re.search(r"<tr>\s*<td><a href=\"/e\.input\.format\.f/\">.*?</tr>", rendered, re.S).group()
    assert row.count("<td") == 2
    assert "Use | or ||, never |||." in reading(row)


def test_a_pipe_in_a_title_survives_the_prefix_page_that_lists_it(to_html):
    rendered = to_html(pages_for(title="Use | or bust.")["e.input..md"])
    assert "Use | or bust." in reading(rendered)


def test_an_attr_list_suffix_in_a_title_cannot_attach_an_event_handler(to_html):
    for page in showing_the_title(pages_for(title=HANDLER)):
        rendered = to_html(page)
        assert "onclick" not in markup(rendered)
        assert HANDLER in reading(rendered)


def test_a_markdown_link_in_a_title_cannot_become_a_javascript_url(to_html):
    for page in showing_the_title(pages_for(title=JS_LINK)):
        rendered = to_html(page)
        assert "javascript:" not in markup(rendered)
        assert JS_LINK in reading(rendered)


def folded(text):
    """What a reader should see once the escaping has folded the whitespace."""
    return " ".join(text.split())


def test_a_title_that_opens_with_a_block_marker_stays_a_title(to_html):
    """A title is prose in a paragraph, and must not become the block its first character names.

    The code's own heading is the only heading a code page has, and the page carries no rule, no
    list and no definition, so any of those appearing means a title stopped being a title.
    """
    for title in BLOCK_MARKERS:
        rendered = to_html(pages_for(title=title)["e.input.format.f.md"])
        assert rendered.count("<h1") == 1, title
        for structure in ("<hr", "<ul>", "<ol>", "<dl>", "<blockquote"):
            assert structure not in rendered, f"{title!r} became {structure}"
        assert folded(title) in reading(rendered), title


def test_a_title_that_is_only_a_horizontal_rule_does_not_become_one(to_html):
    """The case that got away: ``---`` rendered as a thematic break and the title vanished."""
    rendered = to_html(pages_for(title="---")["e.input.format.f.md"])
    assert "<hr" not in rendered
    assert "---" in reading(rendered)


def test_a_hint_that_opens_with_a_block_marker_stays_a_hint(to_html):
    """A hint sits in a paragraph of its own too, so it is the same sink with the same exposure."""
    for hint in BLOCK_MARKERS:
        rendered = to_html(pages_for(title="A title.", hint=hint)["e.input.format.f.md"])
        assert rendered.count("<h1") == 1, hint
        for structure in ("<hr", "<ul>", "<ol>", "<dl>", "<blockquote"):
            assert structure not in rendered, f"{hint!r} became {structure}"
        assert folded(hint) in reading(rendered), hint


def test_a_block_marker_title_reads_the_same_in_the_table_cell_and_the_prefix_list(to_html):
    """A leading marker is inert mid-line, but the escaping still has to display it unchanged."""
    for title in BLOCK_MARKERS:
        for page in (pages_for(title=title)["index.md"], pages_for(title=title)["e.input..md"]):
            assert folded(title) in reading(to_html(page)), title


def test_an_empty_title_renders_the_page_rather_than_failing(to_html):
    rendered = to_html(pages_for(title="")["e.input.format.f.md"])
    assert "Declared in" in reading(rendered)


def test_a_backtick_in_an_arg_name_cannot_escape_its_code_span(to_html):
    arg = 'a`{: onclick="alert(1)"}'
    rendered = to_html(
        pages_for(title="A title.", detail="Uses {a}.", args=(arg,))["e.input.format.f.md"]
    )
    assert "onclick" not in markup(rendered)
    assert arg in reading(rendered)


def test_a_repo_name_is_escaped_where_the_page_names_it(to_html):
    pages = render(build_index([entry("e.input.format.f", "A title.", repo=SCRIPT)]))
    rendered = to_html(pages["e.input.format.f.md"])
    assert "<script" not in rendered
    assert SCRIPT in reading(rendered)


def test_escaping_still_displays_the_characters_the_registry_wrote(to_html):
    """Escaping that mangles legitimate prose is its own bug: these are all real title material."""
    title = "Use < instead of >, and \"quote\" it — 100% & a*b_c, {x}, [y], `z`, back\\slash."
    for page in showing_the_title(pages_for(title=title)):
        assert title in reading(to_html(page))


def test_catalog_json_stays_valid_json_and_round_trips_what_the_registry_wrote():
    pages = pages_for(title=SCRIPT, detail=f"{SCRIPT}\n```", hint=IMAGE, args=("a`b",))
    document = json.loads(pages["catalog.json"])["codes"][0]
    assert document["title"] == SCRIPT
    assert document["hint"] == IMAGE
    assert document["args"] == ["a`b"]


def test_catalog_json_carries_no_markup_a_browser_could_be_talked_into_running():
    """A JSON payload is only inert while it is read as JSON; keep the tag characters escaped."""
    published = pages_for(title=SCRIPT, hint=IMAGE)["catalog.json"]
    for character in ("<", ">", "&"):
        assert character not in published


def test_a_detail_that_is_itself_a_fence_marker_cannot_break_out_of_its_block(to_html):
    """The delimiter-length argument, checked rather than asserted.

    A fence ends only on a longer run of the same character, so a ``~~~`` in the body of a backtick
    fence is content and an inner ``` is outrun. A block marker in there is inert for a different
    reason again: nothing inside a code block is parsed as markdown at all.
    """
    for body in FENCE_MARKERS:
        detail = f"{body}\n{SCRIPT}\n{body}"
        rendered = to_html(pages_for(title="A title.", detail=detail)["e.input.format.f.md"])
        assert "<script" not in rendered, body
        assert "<hr" not in rendered, body
        assert SCRIPT in reading(rendered), body
        assert "Declared in" in reading(rendered), body


def test_an_arg_name_that_is_itself_a_fence_marker_cannot_break_out_of_its_span(to_html):
    for name in FENCE_MARKERS + (SCRIPT, "", "`"):
        rendered = to_html(
            pages_for(title="A title.", detail="Uses {a}.", args=(name,))["e.input.format.f.md"]
        )
        assert "<script" not in rendered, name
        assert "onclick" not in markup(rendered), name
        assert "Declared in" in reading(rendered), name


def test_an_arg_name_is_kept_on_the_line_the_sentence_around_it_assumes(to_html):
    """A newline in an arg name would otherwise split the sentence that names the placeholders."""
    rendered = to_html(
        pages_for(title="A title.", detail="Uses {a}.", args=("two\nlines",))["e.input.format.f.md"]
    )
    assert "two lines" in reading(rendered)
