# Decisions

Choices that look wrong until you know why. Referenced from the code by number;
add to the end and never renumber.

**1. `appcore` is a separate repository, pinned by revision.** It was vendored
into each application while it was a config loader and a session factory —
small, and one consumer. It grew an OIDC client, and four copies of an auth
implementation is where drift stops being untidy and starts being dangerous.

Pinned rather than published: a released version buys a release cycle for every
change, and the consumers are all in one hand. Applications move their pin
deliberately, so nothing updates by surprise.

**2. Nothing here names an application's configuration keys.** An error saying
"set `auth.oidc.client_secret`" is correct for exactly one consumer and wrong
for the rest — and it fails silently, because the sentence still reads well.
The protocol layer names the condition; the caller names the setting, being the
only one that knows what it is called. Enforced by a test that reads the source
rather than by discipline.

**3. `Identity` carries five claims and stops.** Subject, issuer, email,
verified-flag and name. Reading groups and mapping them to roles is a
materially bigger promise than authenticating somebody — it makes this library
responsible for an application's authorisation model. A consumer that wants it
can ask the provider itself.

**4. A missing `email_verified` claim means not verified.** Absence is not
consent. Treating it as true is how an address a directory was simply *told*
becomes trusted enough to match an existing account.

**5. PKCE is unconditional.** The specification makes it optional for
confidential clients. It costs one hash, removes a class of code-interception
bug, and is the only proof a public client has.

**6. The test double signs.** `FakeIdp` generates a key and produces real
tokens, verified by the code that verifies a provider's. A double that returned
claims directly would agree an unsigned token was fine, which is the single
thing these tests exist to catch.
