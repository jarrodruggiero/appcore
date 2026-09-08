"""appcore — the scaffold the suite's applications are built on.

Config loading, the database connection, the FastAPI app factory and an OIDC
relying party. None of it knows what any particular application is *for*, which
is the whole point: an app brings its own models, routes and vocabulary, and
takes the parts that are the same every time from here.

It was vendored into each application until it grew auth. Four copies of a
config loader is untidy; four copies of an OIDC client is where drift hurts, so
it lives in one place now and applications pin a revision of it.
"""

from .app import create_app
from .config import BaseAppSettings, DatabaseSettings, load_config
from .db import (
    Base,
    JSONType,
    dialect_insert,
    ensure_utc,
    make_engine,
    make_session_factory,
    session_scope,
)
from .migrate import upgrade_to_head

__all__ = [
    "Base",
    "BaseAppSettings",
    "DatabaseSettings",
    "JSONType",
    "create_app",
    "dialect_insert",
    "ensure_utc",
    "load_config",
    "make_engine",
    "make_session_factory",
    "session_scope",
    "upgrade_to_head",
]
