# conftest resolves the sibling bakobo/dev checkout from the repo root's parent, so a run inside .worktrees/<topic> looks for <repo>/.worktrees/dev, does not find it, and silently skips the three tests that grade the taxonomy data against the standard. Worktrees are the default working posture, so that is most local runs. Fix: walk past a .worktrees/<topic> root before taking the parent.
kind: todo
created: 2026-09-21T19:05Z

