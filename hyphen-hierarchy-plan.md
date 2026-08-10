# The hyphenated-leaf antipattern: why it keeps happening, and how to stop it

*Written 2026-08-06, against the corpus at that date. **Nothing here is decided.** The rule in §2 is
a proposal for `bakobo/dev`, and until it lands in `error-codes.md` the re-minting in §4 has no
authority behind it.*

---

## 1. The diagnosis

Codes are being minted as `e.<descriptor>.<sub>.<noun1>-<noun2>.<disposition>`, where the two nouns
stand in a containment relation — an entity and one of its parts, or an entity and one of its
problems. `e.env.witness-db.r`, `e.state.conflict.record-head.f`, `e.input.format.entry-kind.f`.

This defeats the hierarchy the grammar exists to provide. A recipient can match `e.state.conflict.`
but cannot match "every problem with a record", because `e.state.conflict.record.` matches nothing —
prefix matching is string-prefix matching, and `record-head` is one token. The specificity is
present but unreachable.

### The measurements

Across `heti`, `tefa` and `witness`, excluding test fixtures:

| | |
|---|---|
| Distinct codes | 107 |
| Codes containing a hyphenated token | **64** |
| Codes with no hyphen at all | 35 |
| Codes at 4 tokens | 19 |
| Codes at 5 tokens | 73 |
| **Codes at 6 tokens** | **0** |

That last row is the finding. **Not one code in the entire corpus has ever used a second
sub-descriptor level.** Every code is `sorter.descriptor.sub.disposition` or
`sorter.descriptor.sub.leaf.disposition`, and everything more specific than one leaf has gone into a
hyphen. The ceiling is not a coincidence; it is what the document teaches.

Eight families are already large enough that the lost prefix is a real loss:

| Shared noun | Codes | The prefix that does not work |
|---|---|---|
| `entry` | 9 | `e.input.format.entry.` |
| `record` | 8 | `e.state.conflict.record.` |
| `floor` | 7 | `e.input.format.floor.` |
| `sig` | 5 | `e.input.format.sig.` |
| `machine` | 4 | `e.self.config.machine.` |
| `anchor`, `effect`, `queue` | 2 each | — |

And one family where the shared noun is the **suffix**, which is the same defect mirrored:
`e.proof.endorsement-sig.f`, `e.proof.event-sig.f`, `e.proof.receipt-sig.f`,
`e.proof.request-sig.f`. Four codes about signature verification, and `e.proof.sig.` matches none of
them — while `e.proof.sig.f` exists separately as a fifth.

Thirteen cases are mechanically provable rather than a matter of taste: the left half of the hyphen
already exists as a standalone token elsewhere in the corpus. `sig` is a token, and so is
`sig-input`. `floor` is a token, and so is `floor-fact`. `witness` is a token, and so is
`witness-db`.

## 2. Why it keeps happening

Seven causes, in descending order of force. The first is sufficient on its own.

**2.1 — The standard's only worked example of minting a leaf is itself the antipattern.**
`e.env.watcher-timeout.r` is the most repeated code string in `error-codes.md`, four times, and it
appears at precisely the two places that teach a reader how to mint:

> Where the table above shows `—`, the descriptor has no *standard* sub-descriptors and a repo mints
> its own (`e.env.watcher-timeout.r`)

> **Deeper leaves are free.** Repos mint sub-descriptors below the standard set without asking
> (`e.env.watcher-timeout.r`).

A session asking "how do I name my leaf?" is answered, twice, with `watcher` + `timeout` — an entity
and one of its problems, joined by a hyphen. The registry example does it a second time:
`e.proof.credential-sig.f`. **Both worked examples in the standard are the thing we are trying to
stop.** No prose rule will outrun two exemplars.

**2.2 — The abbreviation rule legitimises hyphens two paragraphs away, and never distinguishes the
two uses.** *"`sig` for signature, `alg` for algorithm, `comp` for component, `trans-aid` for a
transferable AID"* — `trans-aid` is a correctly hyphenated single concept, sitting beside
`watcher-timeout`, which is two levels. Nothing in the document marks the difference, so a reader
concludes hyphens are simply normal inside leaves.

**2.3 — There is no depth rule at all.** The standard says *when* a sub-descriptor earns its place —
"someone would diagnose, document, or count the condition separately" — and never says *where it
goes*. "Deeper leaves are free" reads as permission to add specificity, not as an instruction about
which axis to add it on. Nothing anywhere says *prefer a level over a hyphen*.

**2.4 — The taxonomy table renders sub-descriptors as one flat list per descriptor,** which anchors
a four-token shape. The zero-codes-at-six-tokens measurement is that anchor made visible.

**2.5 — Every matching example in the standard matches at depth one.** `e.state.`, `e.input.`,
`e.*.r`. A session never sees a mid-level prefix like `e.proof.sig.` earn its keep, so it never
experiences the capability it is destroying.

**2.6 — Nothing checks it.** `bakobo.errors` refuses an illegal code at construction, but a hyphen
is legal in any token, so this whole class passes validation silently. The guidance is prompt-tier
and the enforcement is absent — the weakest arrangement available.

**2.7 — The corpus is now the dominant teacher, and it teaches the antipattern.** 64 of 107 codes
carry a hyphenated token. A session reads the neighbouring codes before it reads the standard,
because coherence with the corpus is the cheaper signal — this is reverence for inherited artifacts,
and here it is self-reinforcing: every new session widens the corpus and strengthens the wrong
pattern. **This is why amending the prose alone will not work.** As long as 64 examples say
otherwise, the document is outvoted.

Underneath all seven is a model failure worth naming plainly. English compounds nouns freely, so "the
record's head is wrong" names itself `record-head` without anyone deciding anything. Producing one
descriptive label is a single act; deciding *which noun is the parent* is a second act, and nothing
in the standard forces it. Absent a rule that demands the second act, the compound wins every time.

## 3. The proposed rule (an edit to `error-codes.md`)

> **A hyphen joins words into one name; a dot separates levels of meaning.**
>
> Before hyphenating a leaf, ask whether both halves name things that exist independently in the
> model, with one containing, owning, or being a property of the other. If so they are two levels and
> the separator is a dot: not `record-head` but `record.head`, not `witness-db` but `witness.db`, not
> `endorsement-sig` but `sig.endorsement`.
>
> **The test: could the left-hand thing have a different problem?** A record can be busy, missing, or
> at the wrong position, so `record` is a level and everything after it is a leaf beneath it. A
> transferable AID has no sub-problems — it is one concept whose English name happens to be two
> words — so `trans-aid` is one token.
>
> Getting this wrong is not cosmetic. `e.state.conflict.record.` selects every problem with a record,
> including ones minted after your handler was written; `record-head` and `record-busy` are two
> unrelated strings that no pattern can gather. **The hierarchy is the whole product; a hyphen in the
> wrong place is a level deleted.**

Three supporting edits, without which the rule is outvoted by its neighbours:

- **Replace `e.env.watcher-timeout.r` with `e.env.watcher.timeout.r` at all four occurrences** in
  `error-codes.md`, and both in `http-errors.md`. Replace `e.proof.credential-sig.f` with
  `e.proof.sig.credential.f` in the registry example. The exemplars are the lesson.
- **Add a matching example at depth**, so the payoff is visible: `e.proof.sig.` gathers every
  signature failure whatever its kind.
- **Rewrite the abbreviation bullet** to contrast the two uses explicitly, rather than listing
  `trans-aid` among abbreviations as if hyphenation were merely a spelling question.

## 4. The corrective plan

Sequenced so that each step makes the next one checkable.

**Step 1 — Amend `error-codes.md`** with §3. Nothing else can be justified until the rule exists.

**Step 2 — Build the lint in `bakobo/errors`,** and this is the step that actually stops recurrence,
because it moves the rule from prompt tier to a gate. Three checks, in descending confidence:

1. **Provable.** A hyphenated token where either half already appears as a standalone token anywhere
   in the corpus. 13 hits today, near-zero false positives.
2. **Strong.** A hyphenated token whose left or right half is shared by two or more codes — a family
   with a missing level. Eight families today.
3. **Deliberate.** Every remaining hyphenated token must appear in an allowlist carrying a one-line
   justification. This is the important one: it does not decide the question, it makes hyphenating a
   *deliberate act* instead of the path of least resistance. `trans-aid` earns its line; `witness-db`
   cannot be written without someone noticing they are writing it.

**Step 3 — Re-mint the corpus,** one PR per repo, driven by the lint going green. Roughly 64 codes.
No deprecation ceremony and no successor records: everything is pre-1.0, nothing external consumes
these, and the catalog is a projection that rebuilds itself. The window for doing this cheaply is
open now and closes at the first external consumer.

**Step 4 — Regenerate the catalog.** The payoff is visible rather than theoretical: `e.proof.sig.`,
`e.state.conflict.record.` and `e.input.format.entry.` become real pages with their leaves listed
under them, which is exactly the navigation the prefix pages were built to provide and cannot
provide today.

### The families, and what they become

Indicative rather than final — each repo's session applies the rule with its own domain knowledge.

| Today | Proposed |
|---|---|
| `e.proof.{endorsement,event,receipt,request}-sig.f` | `e.proof.{endorsement,event,receipt,request}.sig.f` — **corrected 2026-08-06**; the subject is the artifact and `sig` is what failed about it. `e.proof.*.sig.f` still gathers every signature. |
| `e.input.format.entry-{at,body,kind,missing,schema,unknown,version}.f` | `e.input.format.entry.{…}.f` |
| `e.input.range.entry-{depth,size}.f` | `e.input.range.entry.{depth,size}.f` |
| `e.state.conflict.record-{busy,exists,genesis,head,position}.…` | `e.state.conflict.record.{…}.…` |
| `e.self.config.machine-{action,cell,declaration,guard}.f` | `e.self.config.machine.{…}.f` |
| `e.input.format.floor-{fact,precondition,entry-id,…}.f` | `e.input.format.floor.{fact,precondition,entry.id,…}.f` |
| `e.input.{format,missing}.sig-{input,label,value}.f` | `e.input.{format,missing}.sig.{input,label,value}.f` |
| `e.proof.anchor-{chain,head}.f` | `e.proof.anchor.{chain,head}.f` |
| `e.self.corrupt.queue-{claim,item}.f` | `e.self.corrupt.queue.{claim,item}.f` |
| `e.env.watcher-timeout.r` | `e.env.watcher.timeout.r` |
| `e.env.witness-db.r` | `e.env.witness.db.r` |
| `e.env.faculty-unreachable.r` | `e.env.faculty.unreachable.r` |

Hyphens that survive, as single concepts: `trans-aid`, `deleg-aid`, `time-addressing`,
`trusted-time`, `not-an-object`, `second-writer`. Each earns an allowlist line.

## 5. Settled after this was written, and what still is not

**The ordering question is now decided in the standard, against this document's first answer.** This
plan originally put the mechanism above the instance — `e.proof.sig.endorsement.f` — and left the
choice to whoever owned the codes. A heti session pushed back the same day, having independently
minted `e.proof.event.sig.f` from the same prefix-matching argument, and it was right.
`error-codes.md` now carries the rule: order levels by descending effect on what a recipient does,
which in practice means **subject before predicate**. The other axis is served by a glob —
`e.proof.*.sig.f` gathers every signature failure — so nesting subject-first costs nothing. The
table above is corrected accordingly, and the lint suggests subject-first rather than guessing from
corpus frequency.

Still unsettled: whether the standard should cap depth at all: nothing here
argues for a limit, but nothing has tested six tokens either.
