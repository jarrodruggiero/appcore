# Security policy

## Supported versions

appcore has no releases: applications pin a revision. A fix lands on `main`
and is not backported to older revisions, so moving the pin forward is how an
application gets it. Past fixes are listed under
[Security advisories](https://github.com/jarrodruggiero/appcore/security/advisories).

## Reporting a vulnerability

Please report it privately, not in a public issue: use **Report a
vulnerability** on the
[Security tab](https://github.com/jarrodruggiero/appcore/security/advisories/new).
If you found it through an application built on appcore and are not sure which
repository the code is in, report it on that application instead. Either
reaches me.

What happens next:

- I reply in the report, and work out the fix with you there.
- The fix is written in a private fork, so nothing public describes the problem
  before a fix exists.
- When the applications that pin appcore have released the fix, I publish the
  advisory and credit you, unless you would rather not be named. Publishing
  sooner would describe a hole in those applications that their users could
  not yet close.

Please give me a reasonable window to fix it before disclosing it anywhere
else.

## What counts

A flaw in what appcore does: loading settings, opening and migrating the
database, building the web application, and verifying a sign-in with an
identity provider. For example, an ID token accepted despite a bad signature,
the wrong issuer or audience, an expiry in the past, or a nonce that does not
match.

Two things are not appcore's:

- What an application does with a verified identity: storing it, linking it to
  an account, deciding what that account may do. That code is the
  application's, so please report it there.
- `appcore.testing`, a test double that signs tokens with a key it generates
  itself. It is not meant to run in production.
