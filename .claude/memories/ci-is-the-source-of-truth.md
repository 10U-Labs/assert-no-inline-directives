---
name: ci-is-the-source-of-truth
description: Never run tests, linters or builds locally to verify; commit, push to main and read the run, knowing a green release run publishes to PyPI
metadata:
  type: feedback
---

# CI is the source of truth

Do not run tests, linters or builds locally to verify a change: write the code
and the tests, commit, push to `main`, and read the run with `gh run list` and
`gh run view --log-failed`, waiting for it in the background per
[[a-wait-runs-in-the-background]]. Reading the code locally is still right and
cheap: `grep` and file reads are how the useful findings surface.

**Why:** the user asked to adopt this rule from the sibling 10U-Labs
repositories. The jobs between them want Python, Node, jscpd, markdownlint and
the assert-* tools, and CI checks every gate at once.

**How to apply:** a green push publishes to PyPI and force-moves `latest` by
itself, so there is no version to hold back, and a commit that should not be
published is a commit that should not be pushed. The change is done when each
run the push started is green, per [[find-a-run-by-the-full-hash]].
