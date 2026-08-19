# A collision is only caught by the publish gate, days after the merge that made it
kind: todo
created: 2026-08-19T21:56Z

- 2026-08-19T21:56Z Second occurrence. @uf47pf records the first: two days of no deploys while heti and tefa merged re-mints. This one ran four days (2026-08-15 to 08-19), from heti minting e.state.missing.schema.f on top of tefa's. Both times the minting author had already merged and moved on, and the only thing that noticed was errors' scheduled Pages run in a third repo. What is missing is a check where the author is: heti and tefa can run bakobo-errors check against their sibling checkouts in their own CI, or a pre-mint lookup against the published index. The catalog cannot be the first detector without also being the thing that goes red.
