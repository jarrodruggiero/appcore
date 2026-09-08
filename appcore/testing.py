"""A provider to test federation against.

Shipped rather than copied. Every application built on this needs one, and four
hand-written fakes would disagree about what a provider does long before anyone
noticed.

`FakeIdp` **really signs**: an RSA key generated in the test, and tokens
verified by the same code that verifies a real provider's. A stub returning
claims directly would agree that an unsigned token was fine, which is the one
thing worth checking.

Nothing here reaches the network — `install()` redirects both the discovery
fetch and the key lookup, and the suite that uses it should fail any test that
tries to open a socket.

    def test_a_signed_token_is_accepted(monkeypatch):
        idp = FakeIdp()
        idp.install(monkeypatch)
        provider = oidc.Provider(issuer=idp.issuer, client_id=idp.client_id,
                                 client_secret="s", redirect_uri=REDIRECT)
        url, pending = oidc.begin(provider)
        idp.claims = {"nonce": pending["nonce"]}
        identity = oidc.complete(provider, code="c", pending=pending)
"""

from __future__ import annotations

import base64
import datetime as dt
import json
from typing import Any

DEFAULT_ISSUER = "https://idp.example.test"
DEFAULT_CLIENT_ID = "an-application"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


class FakeIdp:
    """An identity provider: one key, a discovery document, and a token
    endpoint that mints whatever the test asks for.

    Set `claims` to override what the ID token says — a wrong `aud`, an expired
    `exp`, a `nonce` from somebody else's attempt. That is how the refusals are
    tested, and they are most of what matters.
    """

    def __init__(self, issuer: str = DEFAULT_ISSUER,
                 client_id: str = DEFAULT_CLIENT_ID):
        from cryptography.hazmat.primitives.asymmetric import rsa

        self.issuer = issuer
        self.client_id = client_id
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = "test-key"
        self.claims: dict[str, Any] = {}
        # What actually reached the token endpoint, rather than what the caller
        # meant to send. `token_auth` is how a public client proves it sent no
        # credentials at all.
        self.token_requests: list[dict] = []
        self.token_auth: list[tuple[str, str] | None] = []
        self.omit_id_token = False
        self.omit_end_session = False

    # -- what the provider publishes ---------------------------------------- #

    def discovery(self) -> dict:
        document = {
            "issuer": self.issuer,
            "authorization_endpoint": f"{self.issuer}/authorize",
            "token_endpoint": f"{self.issuer}/token",
            "jwks_uri": f"{self.issuer}/jwks",
            "id_token_signing_alg_values_supported": ["RS256"],
        }
        if not self.omit_end_session:
            document["end_session_endpoint"] = f"{self.issuer}/end-session"
        return document

    def id_token(self, **overrides) -> str:
        import jwt

        now = dt.datetime.now(dt.UTC)
        claims = {
            "iss": self.issuer,
            "sub": "idp-subject-1",
            "aud": self.client_id,
            "iat": now,
            "exp": now + dt.timedelta(minutes=5),
            "email": "member@example.test",
            "email_verified": True,
            "name": "A Member",
            **self.claims,
            **overrides,
        }
        return jwt.encode(claims, self.key, algorithm="RS256",
                          headers={"kid": self.kid})

    # -- the stubs that stand in for the network ---------------------------- #

    def fetch(self, url: str, data: dict | None = None,
              auth: tuple[str, str] | None = None) -> dict:
        if url.endswith("/.well-known/openid-configuration"):
            return self.discovery()
        if url.endswith("/token"):
            self.token_requests.append(dict(data or {}))
            self.token_auth.append(auth)
            if self.omit_id_token:
                return {"access_token": "x"}
            return {"access_token": "x", "id_token": self.id_token()}
        raise AssertionError(f"unexpected request to {url}")

    def signing_key(self, token: str):  # noqa: ARG002 - matches PyJWKClient's
        """The public half, in the shape PyJWT's key lookup returns.

        Patched in place of `PyJWKClient.get_signing_key_from_jwt`, which would
        otherwise fetch the key set over HTTPS. The verification it wraps is
        left alone — that is the part worth exercising.
        """
        from jwt import PyJWK

        numbers = self.key.public_key().public_numbers()

        def b64(value: int) -> str:
            raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
            return base64.urlsafe_b64encode(raw).decode().rstrip("=")

        return PyJWK.from_dict({"kty": "RSA", "kid": self.kid, "alg": "RS256",
                                "use": "sig", "n": b64(numbers.n),
                                "e": b64(numbers.e)})

    def install(self, monkeypatch) -> FakeIdp:
        """Point appcore's OIDC client at this provider instead of the network."""
        from jwt import PyJWKClient

        from . import oidc

        monkeypatch.setattr(oidc, "_fetch", self.fetch)
        monkeypatch.setattr(PyJWKClient, "get_signing_key_from_jwt",
                            lambda _self, token: self.signing_key(token))
        return self


def as_browser_sends(credential: dict) -> str:
    """A WebAuthn-style credential encoded the way a browser posts it.

    Buffers base64url'd, `id` left alone — it is ALREADY the base64url text of
    `rawId`, and encoding it again produces "id and raw_id were not
    equivalent". Here because more than one application will need it.
    """
    def encode(value):
        if isinstance(value, bytes):
            return _b64(value)
        if isinstance(value, dict):
            return {k: (v.decode().rstrip("=") if k == "id" and isinstance(v, bytes)
                        else encode(v))
                    for k, v in value.items()}
        return value

    return json.dumps(encode(credential))
