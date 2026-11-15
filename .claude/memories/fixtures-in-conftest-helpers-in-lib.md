---
name: fixtures-in-conftest-helpers-in-lib
description: Code shared between tests goes in a fixture in its tier's conftest.py when it is a fixture, and in a package under lib/ when it is not
metadata:
  type: feedback
---

# Fixtures in conftest, helpers in lib

When tests share code, a fixture goes in the `conftest.py` of the tier that
uses it (`test/unit`, `test/integration`, `test/e2e`), and anything else, such
as a plain function, goes in its own package under `lib/`, imported by name
with `lib` on `PYTHONPATH`.

**Why:** the user set this when jscpd flagged duplicated test setup; it is the
layout the sibling 10U-Labs repositories use.

**How to apply:** tests that differ only in their assert share one fixture that
does the setup and run and returns the result, so each test is its assert.
