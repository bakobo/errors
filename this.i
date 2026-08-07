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

        Misuse of this library's own API raises ValueError, not an error code = decision:
          id: guzldf
          why: >
            Raising a code with the wrong argument names is a programmer contract violation, not an
            obstacle in the taxonomy's sense — nobody's intentions were defeated by the world, the
            call site is simply wrong. Chose ValueError over minting something under e.self. because
            a code is a thing a *recipient* classifies and handles, and no recipient ever sees this;
            it fails in the caller's own test suite. Carried over from heti (@cohnne).

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
