---
name: find-a-run-by-the-full-hash
description: gh run list --commit needs the full forty-character hash from git rev-parse HEAD; a short hash lists nothing
metadata:
  type: feedback
---

# Find a run by the full hash

Find the run by the full forty-character hash from `git rev-parse HEAD`.

**Why:** `gh run list --commit` returns an empty list for the short hash `git
log --oneline` prints, which is indistinguishable from a run that has not
started.

**How to apply:** a push starts one workflow or both, depending on what it
touched, and the change is done when each run that started is green rather than
when the first one is.
