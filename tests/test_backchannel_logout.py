"""Verifying a back-channel logout token — the protocol half only.

A provider that ends a session notifies each relying party by POSTing a signed
`logout_token` to a registered endpoint. This module's job stops at deciding
whether that token is genuine and what it names. **Which sessions to end is the
application's**, because appcore does not know what a session is here — the
same line `complete()` draws when it returns an `Identity` and stops.

Two things make this worth verifying carefully rather than trusting.

**The signature IS the authentication.** There is no client authentication on
this endpoint — the spec is explicit that the signed token exists "to prevent
denial of service attacks by enabling the RP to verify that the logout request
is coming from a legitimate party". So an installation using a PUBLIC client
can implement this fully, and every check below is load-bearing rather than
belt-and-braces.

**A logout token must not be an ID token.** The spec forbids a `nonce` claim
for exactly that reason, and requires an `events` claim naming back-channel
logout. Without both checks, an ID token captured at sign-in would be accepted
as an instruction to log somebody out — and, worse, an ID token is the one
token an attacker is most likely to have seen.
"""

from __future__ import annotations

import datetime as dt

import pytest

from appcore import oidc
from appcore.testing import FakeIdp

ISSUER = FakeIdp().issuer
CLIENT_ID = "an-application"
REDIRECT = "https://app.example.test/login/oidc/callback"
EVENT = "http://schemas.openid.net/event/backchannel-logout"


@pytest.fixture
def idp(monkeypatch) -> FakeIdp:
    return FakeIdp(client_id=CLIENT_ID).install(monkeypatch)


@pytest.fixture
def provider() -> oidc.Provider:
    return oidc.Provider(issuer=ISSUER, client_id=CLIENT_ID,
                         client_secret="a-secret", redirect_uri=REDIRECT)


# --------------------------------------------------------------------------- #
# Capturing the session id at sign-in
# --------------------------------------------------------------------------- #
# The half that is easy to forget, because nothing fails without it until a
# logout token arrives naming a session the application never recorded. A
# `sid`-keyed logout is only as good as the `sid` stored when the person
# signed in.

def test_the_session_id_is_carried_out_of_the_id_token(idp, provider):
    _url, pending = oidc.begin(provider)
    idp.claims = {"nonce": pending["nonce"], "sid": "sess-7"}

    identity = oidc.complete(provider, code="c", pending=pending)

    assert identity.session_id == "sess-7"


def test_a_provider_that_issues_no_session_id_still_signs_in(idp, provider):
    """`sid` is optional. An application keying on it falls back to `sub`, and
    that decision is the application's — this just reports the absence."""
    _url, pending = oidc.begin(provider)
    idp.claims = {"nonce": pending["nonce"]}

    identity = oidc.complete(provider, code="c", pending=pending)

    assert identity.session_id is None
    assert identity.subject == "idp-subject-1"


# --------------------------------------------------------------------------- #
# What it accepts
# --------------------------------------------------------------------------- #

def test_a_signed_token_names_the_session_to_end(idp, provider):
    notice = oidc.verify_logout_token(provider, idp.logout_token(sid="sess-1"))

    assert notice.session_id == "sess-1"
    assert notice.subject == "idp-subject-1"
    assert notice.issuer == ISSUER


def test_a_token_with_only_a_subject_is_accepted(idp, provider):
    """`sub` alone is legal, and means every session for that identity.

    Less precise than `sid` — it ends more than the provider may have meant —
    so the caller is told which it got rather than being handed one shape.
    """
    notice = oidc.verify_logout_token(provider, idp.logout_token(sid=None))

    assert notice.session_id is None
    assert notice.subject == "idp-subject-1"


# --------------------------------------------------------------------------- #
# What it refuses, and why each one matters
# --------------------------------------------------------------------------- #

def test_an_unsigned_token_is_refused(idp, provider):
    """The whole authentication. There is no client secret on this endpoint."""
    import jwt

    unsigned = jwt.encode({"iss": ISSUER, "aud": CLIENT_ID, "sid": "sess-1",
                           "jti": "j1", "iat": dt.datetime.now(dt.UTC),
                           "events": {EVENT: {}}}, key="", algorithm="none")

    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, unsigned)


def test_a_token_signed_by_somebody_else_is_refused(provider, monkeypatch):
    other = FakeIdp(client_id=CLIENT_ID)
    FakeIdp(client_id=CLIENT_ID).install(monkeypatch)   # our keys, their token

    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, other.logout_token(sid="sess-1"))


def test_a_token_for_another_client_is_refused(idp, provider):
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, idp.logout_token(aud="somebody-else"))


def test_a_token_from_another_issuer_is_refused(idp, provider):
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(
            provider, idp.logout_token(iss="https://elsewhere.example.test"))


def test_an_id_token_is_not_a_logout_instruction(idp, provider):
    """The attack the `events` check exists for.

    An ID token is signed by the same key, names the same issuer and audience,
    and is the one token most likely to have been seen by somebody. Without
    this check it would be a valid instruction to end a session.
    """
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, idp.id_token(sid="sess-1"))


def test_a_token_carrying_a_nonce_is_refused(idp, provider):
    """Forbidden by the spec for the same reason as above: a `nonce` is what an
    ID token has, so its presence means this is one wearing a costume."""
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, idp.logout_token(nonce="n-1"))


def test_a_token_with_the_wrong_event_is_refused(idp, provider):
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(
            provider, idp.logout_token(events={"http://example.test/other": {}}))


def test_a_token_naming_neither_a_session_nor_a_subject_is_refused(idp, provider):
    """One or the other is required — a token naming nobody instructs nothing,
    and accepting it would invite ending sessions on a guess."""
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, idp.logout_token(sid=None, sub=None))


def test_a_token_without_a_jti_is_refused(idp, provider):
    """Required by the spec. Not stored — see `verify_logout_token` for why
    replay of a LOGOUT token is not the same risk as replay of an ID token —
    but a token missing it is not a conforming one."""
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(provider, idp.logout_token(jti=None))


def test_an_expired_token_is_refused(idp, provider):
    with pytest.raises(oidc.OidcError):
        oidc.verify_logout_token(
            provider,
            idp.logout_token(exp=dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)))
