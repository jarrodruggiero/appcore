# Contributing

Small library, few rules, all of them learned rather than invented.

## Setup

```sh
uv sync --dev
uv run pytest
uv run ruff check .
```

Python 3.12 or newer. No network access is needed to run the tests, and none
should ever be: a test that reaches a real identity provider passes or fails on
somebody else's uptime.

## The rules

**1. Name no application's configuration keys.** This library is used by more
than one application, and they do not agree on what their settings are called.
An error naming `auth.oidc.client_secret` is wrong for any consumer that calls
it something else, and reads perfectly while being wrong. Describe the
condition; the caller names the fix.

**2. Nothing outbound happens unless it is configured.** No discovery on
import, no background refresh, no connection made because a module was loaded.
An installation that does not use a feature must make no requests for it. There
is a test that asserts exactly this, and it is worth keeping.

**3. Comments carry the why, in two or three lines.** Not what the code does —
what a reader would otherwise assume was a mistake. Longer reasoning belongs in
`docs/decisions.md` with a number, referenced from the code.

**4. Test first, then break it on purpose.** Write the failing test, make it
pass, then change the source so the rule no longer holds and confirm the same
test goes red. Several tests in this suite's history passed for the wrong
reason and only mutation revealed it.

**5. Keep the seam.** If a change needs to know something about the application
using it — a user model, a settings name, a table — it is in the wrong repo.
Return the fact and let the caller decide. Before adding anything, read
[`docs/what-belongs-here.md`](docs/what-belongs-here.md): it is the line, with
worked examples and the cases that look shared and are not.

## Pull requests

Say what changed and why, and say plainly if behaviour changed rather than
being added to: consumers pin a revision, and whoever moves that pin needs to
know what moves with it.

A pull request addressing an issue says "Towards #N" rather than "Closes #N".
The person who reported it confirms it is solved.
