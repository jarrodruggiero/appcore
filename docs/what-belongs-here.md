# What belongs in appcore, and what belongs in an application

The line is not about size, and it is not about how many applications happen to
want something today. It is this:

> **appcore may not know what the application is for.**

If a module here would have to learn about portfolios, budgets, households or
trades to do its job, it is in the wrong repository — however much duplication
that leaves behind.

## The test to apply

Ask: *could a second application, doing something completely different, use
this unchanged?*

- **Yes** → it belongs here.
- **Only if I add a hook for its models** → it belongs in the application.
- **Only if I rename its settings** → it belongs in the application.

The third case is the one that catches people. A function that works fine
except that its error message says `auth.oidc.client_secret` is not reusable —
it is specific to one application and merely *looks* general.

## Worked example: OIDC

This is the split done properly, and it is worth copying.

| appcore | The application |
| --- | --- |
| Discovery, PKCE, the code exchange | Which account an identity signs in as |
| Verifying an ID token — signature, issuer, audience, expiry, nonce | Whether an unknown subject may create an account |
| Returning an `Identity` | Storing it, linking it, provisioning it |
| A provider to test against | Fixtures about that application's users |

`oidc.complete()` returns a verified `Identity` and **stops**. Everything after
that point is a decision about an application's users:

- **Matching** — an application decides an identity belongs to an account. That
  it matches on `(issuer, subject)` and never on email is a rule about *its*
  account model, so it lives with the account model.
- **Provisioning** — off, invite-only or open is a statement about who a
  household's directory contains. appcore has no opinion.
- **Sessions** — appcore does not know what a session is here.

The tell: none of `models`, `User`, `Session` or any application's settings
class appears anywhere in this repository.

## What is here now

| Module | Why it qualifies |
| --- | --- |
| `config` | Layered settings. Knows the *shape* of configuration, never a key |
| `db` | Engine, session factory, the pragmas SQLite and Postgres each need |
| `migrate` | Runs Alembic to head. Knows nothing about the migrations themselves |
| `app` | FastAPI factory: templates, static files, health endpoints |
| `oidc` | The protocol, and nothing beyond it |
| `testing` | A provider that really signs, for testing federation |

## Things that look shared and are not

**Authentication.** Sessions, passwords, CSRF, lockout and second factors live
in the application. They are inseparable from its user model, its tables and
its idea of a tenant. Only the *protocol* half of federation is portable — and
notice that even there, the account-linking half stayed behind.

**Anything with a table.** A model here would mean an application inheriting a
migration it did not write, into a database it owns. If two applications need
the same table, they can each write it; a diverging column is a smaller problem
than a shared migration history.

**Anything user-facing.** Templates, copy, navigation and styling belong to the
application. A shared component would have to be configurable enough to suit
every consumer, at which point it is harder to use than writing it twice.

**Anything with a policy in it.** "Who may sign in", "how long a session
lasts", "what counts as activity" are decisions an application makes about its
own users. appcore may provide the *mechanism* and must not choose the answer.

## Duplication is sometimes the right answer

Two applications needing the same fifteen lines is not, on its own, a reason to
move them here. Ask what happens when one of them needs the sixteenth line to
behave differently: if the answer is a flag, and then a second flag, the
abstraction was wrong and the duplication was cheaper.

The bar for moving something here is that it is the *same thing*, not that it
looks similar today.

## When it turns out to be wrong

Moving code out of appcore later is cheap — consumers pin a revision, so
nothing breaks until somebody moves a pin deliberately. Moving it *in* is what
is expensive, because every consumer then depends on a shape that was chosen
for one of them.

So when it is genuinely unclear: leave it in the application. Wait until a
second consumer needs it and see whether it needs the *same* thing.
