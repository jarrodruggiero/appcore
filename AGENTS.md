# Notes for AI assistants

`appcore` is a library, not an application. Everything in it is used by more
than one codebase, which changes what "correct" means: a change here is a
change everywhere, and nothing can be justified by what one consumer happens to
need.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing anything — it is
short, and it records the rules that are easy to break without noticing.

## The rule that catches people out

**No module here names an application's configuration keys.** An error saying
"set `auth.oidc.client_secret`" is wrong the moment a different application
calls that setting something else, and it is wrong in the way nothing fails on,
because the sentence still reads perfectly.

Describe the *condition*; leave the key names to the caller, which is the only
place that knows them. `tests/test_oidc.py` enforces this by reading the source.

## What lives here, and what does not

[`docs/what-belongs-here.md`](docs/what-belongs-here.md) is the answer, and it
is the document to read before adding anything. The short version:

> **appcore may not know what the application is for.**

The split is not about size. `oidc.py` returns a verified `Identity` and stops —
storage, linking and provisioning are the caller's, because those are decisions
about an application's users rather than about the protocol. Duplication across
applications is sometimes the right answer, and that page says when.

## Working on it

```sh
uv sync --dev
uv run pytest          # 20 tests, no network
uv run ruff check .
```

**Test first, then break it on purpose.** A test that has never failed has not
been shown to test anything. When you add a guard, change the code so it no
longer holds and watch a named test go red.

Nothing in the suite reaches the network. `appcore.testing.FakeIdp` signs real
tokens with a key generated in the test, so verification does the work it does
in production — a stub that returned claims directly would agree that an
unsigned token was fine.

## Changing this breaks other things

Consumers pin a revision, so nothing updates by surprise. But a change that
alters behaviour rather than adding to it wants saying out loud in the commit
message: the next person to move a pin needs to know what moved.
