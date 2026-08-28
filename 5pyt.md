# e.feature.unsupported.alg.f has a detail template hard-wired to Ed25519
kind: todo
created: 2026-08-28T18:43Z

- 2026-08-28T18:43Z Raised from bakobo/mdoc-interop 2026-08-28, where it was filed as tick 3dls. Relocated here because the shipped code lives in heti and its registry entry is this repo's business.

index.json records:

  e.feature.unsupported.alg.f
  title:  'The signature uses an algorithm I don't verify.'
  detail: 'This request is signed with "{alg}", but I verify only ed25519 signatures.'

The title is general; the detail is not. It names Ed25519, so the code cannot describe a verifier that verifies ECDSA and not Ed25519 -- which is exactly mdoc-interop's case, ISO 18013-5 issuerAuth being ES256/384/512. error-codes.md says a code's meaning and args signature never change once shipped, and that titles and detail templates are static per code, so widening heti's detail is not available.

mdoc-interop therefore minted e.feature.unsupported.alg.cose.f, one level deeper, so a handler matching the prefix e.feature.unsupported.alg. still catches both. That is the standard's own escape hatch ('deeper leaves are free') and costs nothing at the call site, so nothing is broken and nothing needs fixing urgently.

Recorded because the same collision will happen to the next non-Ed25519 repo, and because the real fix -- generalising heti's detail template, or deprecating the code with a named successor -- belongs here and in heti rather than in a consumer. Note the same pattern recurs: mdoc-interop also went one level deeper past tefa's e.feature.unsupported.digest.f for the same reason.
