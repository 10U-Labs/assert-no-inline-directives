# Memories

- [CI is the source of truth](ci-is-the-source-of-truth.md) — never run tests, linters or builds locally; push and read the run; a green release run publishes.
- [A wait runs in the background](a-wait-runs-in-the-background.md) — a CI wait is run_in_background or Monitor, never a foreground sleep or gh run watch; a watch polls at --interval 60.
- [Find a run by the full hash](find-a-run-by-the-full-hash.md) — `gh run list --commit` lists nothing for a short hash; pass `git rev-parse HEAD`.
- [Fixtures in conftest, helpers in lib](fixtures-in-conftest-helpers-in-lib.md) — shared test fixtures go in the tier's conftest.py, everything else in a lib/ package.
- [Push to main](push-to-main.md) — commit and push straight to main, no branches or PRs
