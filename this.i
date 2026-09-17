# errors — Intent Tree (this.i)
#
# Source of truth for this repo's intentions and the decisions that follow from them
# (dev/methodology.md). Code and docs are derived from this tree. Each consequential decision is
# recorded here, in its own commit, before the code that implements it. IDs are opaque base32
# [a-z2-7]{6,12} and survive renames.
#
# The normative document this repo serves is dev/standards/error-codes.md; the wire binding that
# freezes its published URL is dev/standards/http-errors.md. Where a node here and those standards
# disagree, the standards win on what a code *means* and this file wins on what this repo *builds*.

Publish every Bakobo error code as a catalog derived from source = goal:
  id: v44abn
  why: >
    Every Bakobo problem+json response already carries "type": "https://errors.bakobo.com/<code>"
    (http-errors.md), and codes are being emitted in real services today, so those URLs are landing
    in logs before anything answers them. This repo exists to make them answer — a published catalog
    of every code Bakobo defines, generated from the registries that already exist in source. Chose a
    published artifact derived from source over Provenant's design, which put error definitions in a
    database that services read at request time; that was rejected deliberately, because it turns a
    static fact into a runtime dependency on the request path and makes an error report unreadable
    exactly when the lookup service is the thing that is down. Tradeoff accepted: the catalog can lag
    the registries between builds, and a code is live on the wire before its page exists.
  children:

    The registry in source is the source of truth; the catalog is a projection = ++projection decision:
      id: tjs63f
      why: >
        Codes are declared as module-scope literals in the repos that raise them, and everything this
        repo produces — index.json, the site, the uniqueness check — is derived from those literals by
        static analysis. Chose extraction over a registration API or a hand-maintained master list,
        both rejected because they can disagree with the code that actually raises, and a catalog that
        disagrees with the raise site is worse than no catalog. Tradeoff: extraction can only see what
        static analysis can see, which is why error-codes.md forbids assembling a code from variables,
        f-strings, loops, or factories — the restriction exists to make this projection possible, so
        this repo enforces it rather than working around it.
      children:

        No runtime lookup path exists = --runtime-lookup constraint:
          id: vnu3rr
          why: >
            The full code travels on the wire, so nothing needs a lookup to be understood. A read API
            over the index would be cheap to add and is refused on purpose: the moment one exists,
            some service will call it on the error path, and the catalog becomes a dependency of
            reporting failure. RFC 9457 already forbids clients from automatically dereferencing
            `type`, so the published page is for a human reading a log, not for a machine on a
            request path.

    The shared package is heti's module lifted, not a rewrite = decision:
      id: niawr3
      why: >
        heti's src/heti/errors.py says in its own docstring that nothing in it is heti-specific except
        the exception class name, that it is "the local stand-in for the shared bakobo.errors package
        the standard names," and that it is "meant to be lifted there whole once a second repo needs
        it." tefa then vendored it verbatim and booked the debt (tefa this.i @6wojnr, tick ~4iuf).
        Both repos predicted this package. Chose a substantially verbatim lift over a fresh
        implementation because a second spelling of the matcher would disagree with the first at
        exactly the edge cases that decide handling, and because the lift collects a debt two repos
        already recorded rather than correcting a mistake. Tradeoff: the package inherits heti's
        shape, including decisions a greenfield design might have made differently.
      children:

        ARG_CAP bounds every string arg at 80 characters = constraint:
          id: jfbx5i
          why: >
            Args arrive from the wire and a rendered message may be logged, so no arg is ever echoed
            unbounded (error-handling.md rubric #7). Carried over from heti unchanged, and recorded
            here because it is load-bearing and under-documented in the standard: it is the
            unbounded-value-echo rule enforced structurally rather than by good intentions.

          children:
            ARG_CAP is a flood guard at 1024, and the middle of a long value is what goes = decision:
              nid: 0rch3720
              why: >-
                @jfbx5i states the constraint as 'bounds every string arg at 80 characters', and the REASON it gives is right while the NUMBER never was. Both rubrics it cites -- error-handling.md #2 and #7 -- say an interpolated value must be capped and neither says how tightly, so 80 came from whoever lifted the module out of heti rather than from any argument. Daniel said so on 2026-08-25: it was arbitrarily chosen and he never agreed to it. THE CAP IS A FLOOD GUARD AND NOT A LEGIBILITY RULE, and that is what fixes the size. Nothing may make a message unbounded, because a value arrives from the wire and a message may be logged; deciding what reads well on a screen is a different job belonging to a layer that knows its own geometry. heti already does that job properly, clipping a field at 200 for two and a half rows of an eighty-column terminal, with the number argued in place -- so on a heti screen there were two bounds, the reasoned one was looser, and the arbitrary one upstream meant it never bit. Raised to 1024. WHAT THE TIGHT CAP COST, measured rather than supposed: sixteen refusals in heti exceeded it, up to 165 characters, so each stopped mid-clause -- usually just before the part naming the remedy, which is the half a reader needs. One of them told somebody that a departing member cannot carry a weight and never reached the sentence saying to pass a weights list with 0 for the leaver. It also made a coded refusal unable to name two 44-character identifiers at once (heti tick 6m7x), which is the shape of half the interesting conflicts in a KERI system. THE MIDDLE IS ELIDED, NOT THE TAIL. Head-truncation drops the part that identifies a path: a long path cut at the cap names a directory and hides the filename (heti tick 4nes). Keeping both ends is right for every kind of value rather than only for paths -- an identifier is distinguished at both ends, and a sentence that must be cut reads better with its conclusion than without it. Rejected 255, which Daniel floated: it fixes heti's longest offender by luck, leaves a 300-character sentence cut just as silently, and makes an attacker-chosen value three times worse on any consumer that has no display bound of its own. Rejected removing the cap, which is the unbounded-value-echo anti-pattern the standard names. Rejected marking which args carry an application's own words so only the others are capped: it is the right shape if the cap must stay tight, and once the cap is a flood guard there is nothing left for it to buy. TRADEOFF: a consumer with no display bound of its own can now put a kilobyte on one line. That is the correct division of labour rather than a regression -- input-handling.md asks every destination to bound for itself -- and it is why this raise ships with that standard.
        Misuse of this library's own API raises ValueError, not an error code = decision:
          id: guzldf
          why: >
            Raising a code with the wrong argument names is a programmer contract violation, not an
            obstacle in the taxonomy's sense — nobody's intentions were defeated by the world, the
            call site is simply wrong. Chose ValueError over minting something under e.self. because
            a code is a thing a *recipient* classifies and handles, and no recipient ever sees this;
            it fails in the caller's own test suite. Carried over from heti (@cohnne).

    One verb per question, and a code is a path in an IS-A tree = ++selectors decision:
      id: hf4yes
      why: >
        A code is a path in an IS-A tree and selecting by prefix is instanceof, which is the
        guarantee the whole grammar exists to provide: a handler written against e.state.conflict.
        keeps being right about leaves minted later, in repos it has never heard of. The lifted
        matches() hid that behind one verb whose mode is inferred from the pattern's punctuation, so
        the choice between "is this within that class" and "is this that one condition" was made by
        a trailing dot nobody could see — and forgetting the dot silently asked the other question
        and answered no forever (tick 3p7x). Three verbs make the question explicit at the call
        site: is_a for an interior node, is_exactly for a leaf, is_like for a wildcard shape.
        is_a is reflexive and punctuation-free — code == x or code startswith x + "." — so
        is_a("e.proof.event") and is_a("e.proof.event.") ask the same thing and the footgun closes
        by construction. It REFUSES an argument carrying a disposition, which looks pedantic and is
        the point: nothing can ever live beneath .r, so is_a("e.env.db.timeout.r") would read as a
        class test and behave as a leaf test, which is precisely the brittleness is_a exists to
        prevent. Chose ValueError there over a silent exact match, on @guzldf's rule that misuse of
        this library's own API is a programmer contract violation rather than an obstacle.
        Wildcards get segment semantics rather than fnmatch's character semantics: * is exactly one
        segment, ** is zero or more so e.proof.**.sig.f includes e.proof.sig.f the way gitignore's
        a/**/b matches a/b, and both are whole segments. Rejected keeping fnmatch's sig-* form,
        because a wildcard that reaches inside a token is what made "a hyphen forfeits a query"
        false; forbidding it makes that claim true by construction and closes the escape hatch that
        would let a hyphenated family survive by being globbed instead of re-minted.
        Evidence this is not theoretical: of the sixteen patterns in the corpus, seven are prefix
        questions wearing glob syntax (e.input.*, e.input.format.*, e.input.missing.*), written that
        way because matches() offered one verb. Tradeoff: every call site migrates, and matches()
        is retired rather than kept as an alias, because leaving it would leave the teaching
        material in place — the same reason the hyphenated codes are being re-minted rather than
        tolerated.

    An illegal code cannot be declared = ++refuse decision:
      id: 3fg2dn
      why: >
        ErrorCode validates its code at construction and raises ValueError on anything the grammar
        forbids — an unknown first descriptor, a bare descriptor with no sub-descriptor, a missing or
        misplaced disposition, `f` or `r` used as a descriptor. Because registry entries are
        module-scope literals, this fires at import, so an illegal code cannot reach a test run, let
        alone the wire. Chose refusing over describing — a lint, or validation deferred to the
        extractor — because the strongest available enforcement tier wins, and a check that runs in
        this repo's CI cannot stop a code being raised in a repo that has not adopted the check yet.
        Two tradeoffs accepted: adding a first descriptor now requires every repo to upgrade the
        package before it can use the new descriptor, which is friction we want, since the closed set
        is what makes prefixes stable enough to build handlers on; and adoption breaks the existing
        bare-descriptor test fixtures in heti and tefa (e.env.r, e.proof.f), which the standard
        already forbids and which must be fixed as part of adopting.
      children:

        The closed descriptor set ships as data, not prose = decision:
          id: gzkwg6
          why: >
            The ten first descriptors and their standard sub-descriptors are a data file in this
            package, which is what the validator reads and what the site's category pages are
            generated from. Chose data-in-the-package with CI reconciling it against the table in
            error-codes.md over parsing the standard's markdown at build time: the standard's table
            carries the *why* for each descriptor and is written for humans, and a build that depends
            on its formatting would make an editorial change to a sentence able to break a release.
            Tradeoff: two artifacts that can drift, so the reconciliation check is not optional — it
            is the thing that makes the split safe rather than merely convenient.

    Extraction is scoped by shipped-source globs, never by registry filename = decision:
      id: gvn2k2
      why: >
        Each repo in the corpus declares include globs (default src/**/*.py) and tests are excluded.
        Chose globs over a convention that registries live in one module per repo, because tefa
        already spreads ErrorCode literals across eight modules under src/tefa/, and because
        error-codes.md's actual rule is a property — a module-scope literal — not a place. Excluding
        tests is load-bearing rather than tidiness: heti and tefa both construct ErrorCode in their
        tests, tefa's fixtures reuse e.env.watcher-timeout.r which heti owns for real, and witness's
        contract test names three heti codes it does not own. An extractor that walked tests would
        report phantom duplicates on its first run, and a real duplicate would then be
        indistinguishable from noise. Tradeoff: a repo that puts a real registry outside its globs is
        silently absent from the catalog, so the manifest is reviewed when a repo is added.

    A hyphenated leaf must be justified in writing or re-minted = decision:
      id: uf47pf
      why: >
        error-codes.md says a hyphen joins words into one name and a dot separates levels, so a leaf
        whose halves stand in a containment relation is a level deleted: e.state.conflict.record.
        gathers nothing while record-head and record-busy are two unrelated strings. The rule cannot
        be decided mechanically — trans-aid is one concept and record-head is two — so this check
        reports evidence at two confidences and makes the residue deliberate at a third. A half that
        already stands as its own level BESIDE IT, under the same parent, is *proven* — scoped that
        way because a level speaks only for its own siblings, and an earlier version compared across
        the whole corpus and then reported that `covered` was a level when the level was `comp`,
        under a different parent entirely: a false claim inside a diagnostic, which is worse than a
        missing one. A half shared by two or more codes is a
        *family* whose common prefix does not work; everything else must appear in hyphens.toml with
        a written justification, and an entry with no justification is refused. Chose the allowlist
        over either extreme: refusing every hyphen would forbid trans-aid and not-an-object, which
        are genuinely one name, and warning without a gate reproduces the state that let 64 of 107
        codes acquire the defect. The allowlist excuses any justified hyphen, including one the
        check can prove is a level. That rule was the other way round at first, on the reasoning
        that an escape hatch swallowing the finding is worse than no check, and it was wrong: the
        check rules on whether a dot is LEGAL and only a person can rule on whether it would be
        USEFUL. duplicate-key is the case that proved it — both halves are levels under one parent,
        so the check is right that e.input.format.key. is available, and heti already owns
        e.input.format.key.f for a signature keyid, so that class would hold a malformed keyid and a
        JSON object key appearing twice. The safeguard is the required justification, not a veto. A suspicion is REPORTED everywhere and FATAL only under `lint`, which is the
        correction of a real defect rather than a nicety: wiring it into the publish gate stopped
        errors.bakobo.com deploying for two days because heti and tefa had not yet merged their
        re-mints, so a naming preference withheld pages from URLs already sitting in logs. The line
        is whether a finding makes the catalog WRONG. An unreadable declaration and a fatal
        collision do, and refuse to publish; a badly spelled leaf does not, and the page is correct
        either way. @gazetr's fatal/reported split had already drawn that line for collisions and
        this failed to follow it. `lint` is what a minting repo runs, where the author is.
        The suggested repair puts the subject first, per error-codes.md's ordering
        rule, and says how to invert it rather than pretending to be a ruling. Counting which half
        organises more codes was tried and rejected: it measures frequency in today's corpus rather
        than effect on what a recipient does, which got endorsement-sig backwards. Evidence that the
        check beats hand judgment either way: twelve allowlist entries were drafted by hand before it
        ran, and it disproved four of them.

    A duplicate code whose titles differ fails the build = ++uniqueness decision:
      id: gazetr
      why: >
        error-codes.md says the namespace is global across Bakobo — one code, one meaning, one title,
        everywhere — and until an index exists that is a rule nobody can check. This is the single
        highest-value thing the pipeline buys, and heti has already hit the collision once in real
        work. Chose failing on differing titles over failing on any repeated code, because two repos
        importing or restating the same entry with the same title is agreement, not collision, and a
        check that cannot tell those apart gets suppressed.
      children:

        Args divergence is fatal too; detail and hint divergence is reported = decision:
          id: wklkoj
          why: >
            The commission named titles. Args belong with them: error-codes.md says a code's args
            signature never changes once shipped, and args travel positionally on the wire, so two
            declarations of one code with different args produce a problem+json body whose values
            mean different things by position — a wire defect, not a wording defect. Chose to leave
            detail and hint non-fatal because they are prose that two repos may reasonably word
            differently while agreeing completely, and a check that fails on rewording is a check
            that gets suppressed. Tradeoff: prose drift between two declarations of one code is
            reported and can be ignored, so it can persist.

    The published URL is frozen at https://errors.bakobo.com/<code> = ++frozen-url constraint:
      id: 6h5db4
      why: >
        http-errors.md derives `type` mechanically from `code`, and services are emitting it now, so
        the site's URL shape is a wire contract this repo inherits and cannot renegotiate. Pages are
        therefore generated as <code>/index.html, which serves at /<code>/ and redirects from
        /<code>; a bare file named for the code would be served without a content type a browser
        renders.

    The site publishes now, from a public repo = decision:
      id: vrdqup
      why: >
        Daniel's call, 2026-08-06: publishing commits Bakobo publicly to documenting its errors well,
        and a private catalog lets us off that hook. Chose publishing now over the deferral the
        standard explicitly permits — http-errors.md records that `type` is safe to emit before the
        catalog exists, precisely so the site can arrive late and start working retroactively for
        errors already in logs. Tradeoff accepted: the catalog exposes the full error surface of heti
        and tefa, which are private repos for an unlaunched product, and GitHub Pages on the free org
        plan requires this repo to be public for that to work.

    Zensical renders the site = decision:
      id: 5fi4fd
      why: >
        Chose Zensical over the hand-authored HTML that bakobo.com uses and over Material for MkDocs.
        Hand-authoring is right for bakobo.com's single page and wrong here, where every one of ~65
        code pages plus prefix and category pages is generated from index.json. MkDocs is a supply
        chain risk — unmaintained since 2024, and Material for MkDocs reaches end of life on
        2026-11-05 — so starting there would be adopting a dependency with a known expiry date.
        Tradeoff: Zensical is 0.0.x, so the renderer is young and its config may move under us; the
        mitigation is that our own contribution is markdown plus a generator, and the pages are
        regenerable against a different renderer.

    Registry prose is escaped where it becomes markup, never on the way in = ++escaping decision:
      id: twdcue2y
      why: >
        title, detail and hint are literals lifted from every repo in the corpus and interpolated
        straight into the published markdown, and the renderer passes raw HTML through, so a <script>
        in any of them ran on errors.bakobo.com. That is stored XSS reachable by anyone who can land
        an error code anywhere in the fleet, and the blast radius is the whole public catalog, not
        the one page. Chose escaping at each sink over sanitising entries as they are extracted:
        @tjs63f makes the catalog a projection of what the registries literally say, and a value
        rewritten on the way in would make the catalog disagree with the code that raises, which is
        the one thing this repo exists to avoid. A title may legitimately contain `<`, `&` or a
        quote — "Use < instead of >" is a real title this must still display correctly. Rejected a
        sanitising pass over the rendered HTML too, which would put a second parser and an allowlist
        into the build to undo damage this generator need not do in the first place. Each sink is
        escaped for what it actually is, because one escape is wrong in at least one of them: prose
        and table cells are HTML-escaped and then backslash-escaped for the markdown this site's
        extension set makes dangerous (attr_list turns a trailing `{: onclick="…" }` into an event
        handler on the cell, `[x](javascript:…)` is a live link, and a bare `|` truncates a row);
        detail keeps its fenced block, whose contents the renderer already escapes, and gets a fence
        longer than any backtick run inside it, since HTML-escaping there would double-escape and
        show a reader `&lt;` where the template says `<`; arg names get a code span delimited the
        same way. Tradeoff accepted, and visible on 42 of 532 pages today: a registry's prose is no
        longer read as markdown, so a hint that writes `witness <url>` now shows its backticks
        instead of setting the span in code. That is the right way round — the hint is a literal a
        CLI also prints, where the backticks are characters and not formatting, and the site was
        interpreting them by accident — but it is a change to what a reader sees, not only to the
        generated source. The other cost is standing: every future interpolation in site.py is a
        sink someone has to remember, which is why the escaping tests render each page through the
        real extension set read from zensical.toml rather than asserting on the markdown. And this
        closes the injection, not the class: the site still serves no Content-Security-Policy, so a
        sink that escapes wrong has nothing behind it (tick ~3mcl).

    The package targets Python 3.14 = constraint:
      id: gjt4y3
      why: >
        A shared package must import under the lower of its consumers' floors. That floor was tefa's
        >=3.12.6 while heti was already at >=3.14, but tefa moved to >=3.14 when it took a dependency
        on bakobo/keripy, which requires ~=3.14.0. So the 3.12 target now has no consumer, and the CI
        leg enforcing it was exercising an interpreter nothing in the stack runs. Chose to track
        keripy's floor rather than hold a lower one speculatively: the whole Bakobo stack sits on
        keri, so a floor beneath keripy's cannot be reached by anything that ships, and maintaining
        it costs a matrix leg and a syntax ban for no reader. The constraint is still worth recording
        because it moves with keripy, not with this repo's toolchain, and it stays invisible until a
        consumer's CI fails. Tradeoff accepted: an outside consumer pinned below 3.14 is now excluded,
        which is free today because there is none.
