---
name: a-wait-runs-in-the-background
description: A wait for CI is a Bash run_in_background or a Monitor, never a foreground sleep or gh run watch, so the session stays idle; gh run watch inside it polls at --interval 60
metadata:
  type: feedback
---

# A wait runs in the background

Waiting for a workflow run, or for anything else that takes minutes, is done
with `Bash` and `run_in_background: true`, which notifies once when the command
exits, or with `Monitor`, which notifies once per event; never with a foreground
`sleep`, `gh run watch` or polling loop in the session's own shell.

**Why:** a cron reminder fires only while the session is idle. A foreground wait
holds the session busy for the whole run, and the user cannot type while a push is in
flight. The sibling 10U-Labs repositories hold the same rule for the same reason.

**How to apply:** start the wait in the background, end the turn, and act on the
notification. `gh run watch <id> --exit-status --interval 60` is fine inside the
background command; it is the foreground that is the problem.

The interval is there because `gh run watch` polls every 3 seconds by default,
and over a long run that trips GitHub's secondary rate limit. Once it has
tripped, the watch and every `gh` call after it answer HTTP 403 while `gh api
rate_limit` still shows every bucket full, and the limit clears only after
several minutes without a call. So when a `gh` call answers 403 that way, the
next one waits behind a background `sleep` rather than retrying at once, since
each retry keeps the limit tripped.

Find the run per [[find-a-run-by-the-full-hash]].
