# bakobo/errors

[![CI](https://github.com/bakobo/errors/actions/workflows/ci.yml/badge.svg)](https://github.com/bakobo/errors/actions/workflows/ci.yml)
[![Pages](https://github.com/bakobo/errors/actions/workflows/pages.yml/badge.svg)](https://github.com/bakobo/errors/actions/workflows/pages.yml)

The shared error-code machinery every Bakobo repo imports, and the catalog extracted from every
registry that uses it — published at **https://errors.bakobo.com/**.

Every Bakobo problem+json response carries `"type": "https://errors.bakobo.com/<code>"`, so those
URLs are already landing in logs. This repo is what answers them. The registries in source code are
the source of truth; the catalog is a projection of them, built by static analysis, and nothing here
is ever on a request path.

## What's in it

| Path | Contents |
|------|----------|
| `src/bakobo/errors/` | the package: `ErrorCode`, `BakoboError`, `matches()`, and the closed taxonomy as data |
| `this.i` | the intent tree — why this repo is built the way it is (read it before designing) |

Two standards govern this repo, and both live in the sibling [`bakobo/dev`](../dev):
[`error-codes.md`](../dev/standards/error-codes.md) for what a code means, and
[`http-errors.md`](../dev/standards/http-errors.md) for the URL shape it publishes under.

## Using the package

```python
from bakobo.errors import ErrorCode

SIG_INVALID = ErrorCode(
    "e.proof.credential-sig.f",
    "The authority evidence carries a signature that does not verify.",
    detail="The signature on credential {credential} does not verify against the key "
           "in the KEL of {issuer} at sequence number {seq}.",
    args=("credential", "issuer", "seq"),   # named here, positional on the wire
    hint="Confirm the credential was issued by the AID you expect, and that its "
         "issuer's KEL is current.",
)

raise SIG_INVALID(credential=said, issuer=aid, seq=4)
```

Entries are declared as literals at module scope, never assembled from variables, f-strings, loops,
or factories — that restriction is what lets the catalog be extracted by static analysis, so this
package enforces it rather than working around it.

An illegal code raises `ValueError` where it is declared. Because a registry entry is a module-scope
literal, that is import time: a code outside the closed taxonomy, or a bare descriptor like
`e.proof.f`, cannot reach a test run.

## Fresh clone → passing tests

With [uv](https://docs.astral.sh/uv/):

```bash
uv run pytest
```

Coverage is enforced at 100% branch coverage; the run fails below it.
