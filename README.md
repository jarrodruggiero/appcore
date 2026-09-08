# appcore

The scaffold a small self-hosted web application needs before it can be about
anything: configuration, a database connection, a FastAPI app factory, and an
OpenID Connect relying party.

It knows nothing about what the application using it is *for*. That is the
point — an app brings its own models, routes and vocabulary, and takes the
parts that are the same every time from here.

```python
from appcore import BaseAppSettings, create_app, load_config

class Settings(BaseAppSettings):
    app_name: str = "Example"

settings = load_config(Settings)
app = create_app(settings)
```

## What is in it

| Module | What it does |
| --- | --- |
| `config` | Layered settings — file, environment, defaults — through pydantic-settings |
| `db` | Engine and session factory for SQLite or Postgres, with the pragmas each needs |
| `migrate` | Runs Alembic to head at startup, so a fresh volume builds itself |
| `app` | The FastAPI factory: templates, static files, health endpoints |
| `oidc` | Sign-in delegated to an identity provider, as a relying party |
| `testing` | A provider that really signs, for testing federation |

## Where the line is

[`docs/what-belongs-here.md`](docs/what-belongs-here.md) — what qualifies for
this repository and what stays in the application using it. Worth reading
before proposing an addition.

## Two things it is deliberate about

**Nothing outbound happens unless it is configured.** `oidc` performs no
discovery on import and keeps no background refresh: the first request to a
provider is made when somebody presses the sign-in button. An installation that
leaves it off makes no requests at all.

**It names no application's configuration keys.** An error saying "set
`auth.oidc.client_secret`" is wrong the moment a different application calls
that setting something else — so this describes the *condition*, and the caller
names the setting. That rule is enforced by a test.

## Using it

Applications pin a revision rather than a released version:

```toml
dependencies = [
    "appcore @ git+https://github.com/jarrodruggiero/appcore@<sha-or-tag>",
]
```

## Licence

AGPL-3.0-or-later, matching the applications built on it.
