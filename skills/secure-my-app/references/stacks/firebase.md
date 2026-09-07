# Firebase

The per-stack answer to the FIX column in `controls.md`. Control IDs are the anchors.

One thing about Firebase changes how you audit it. **The client SDK talks to the database directly.**
There is no server of yours in the path. So for every read and write a browser or app makes, the
security rules file is the entire server-side control. Not one layer of several. The only one. A
Firebase app with permissive rules has no authorization at all, no matter what the UI does.

---

## How to fingerprint this stack

| Marker | What it proves |
| --- | --- |
| `firebase.json` | Firebase CLI project. Read its `firestore`, `storage`, `hosting`, `functions` and `emulators` keys |
| `.firebaserc` | Names the project alias to project id mapping |
| `firestore.rules` | Firestore rules, as source. May not match what is deployed |
| `storage.rules` | Cloud Storage rules. A separate ruleset with different syntax |
| `database.rules.json` | Realtime Database, a different product with JSON rules, not the CEL-like language below |
| `firestore.indexes.json` | Firestore in use |
| `firebase` in `package.json` | Client SDK (v9+ modular) |
| `firebase-admin` in `package.json` | Admin SDK. It bypasses all rules by design. Every file importing it must be server-only |
| `firebase-functions` | Cloud Functions |
| `getFirestore`, `collection(`, `doc(`, `onSnapshot(` in client code | Direct client SDK access. Rules are the only control on these paths |
| `apiKey:` in a config object committed to the repo | Expected. A Firebase web API key is an identifier, not a secret |

```bash
cat firebase.json
rg -n 'rules_version|allow ' firestore.rules storage.rules 2>/dev/null
rg -n "require\(['\"]firebase-admin|from ['\"]firebase-admin" --glob '!node_modules'
```

---

## The exact commands

### See what is actually deployed

The local `firestore.rules` file is the source. It is not proof of what is live. Someone can edit
rules in the console and the repo never changes.

```bash
firebase use <your-alias-or-project-id>
firebase deploy --only firestore:rules --dry-run 2>/dev/null || true
```

There is no stable CLI command I could confirm that prints the currently deployed ruleset. Read the
live ruleset in the Firebase console under Firestore Database, Rules, or use the Rules REST API at
`firebaserules.googleapis.com`; verify the exact method against
<https://firebase.google.com/docs/reference/rules/rest> before scripting it. Until you have read the
live rules, a rules finding based only on the repo file is `[static]` evidence, and a mismatch between
repo and console is itself a finding worth reporting.

### Run the emulator

```bash
firebase emulators:start --only firestore,storage,auth
# or, for a one-shot test run that starts, runs, and tears down:
firebase emulators:exec "npm test"
```

The emulator enforces your rules locally with no billing and no risk to production data. This is where
every VERIFY command for a Firebase rules finding should run.

### Write and run a rules test

This is the highest-value artifact you can leave behind in this stack, and it doubles as the
two-account test from `controls.md`.

```bash
npm i -D @firebase/rules-unit-testing
```

```js
// test/rules.test.js
import { readFileSync } from 'node:fs'
import {
  initializeTestEnvironment,
  assertFails,
  assertSucceeds,
} from '@firebase/rules-unit-testing'
import { doc, getDoc, setDoc } from 'firebase/firestore'

let testEnv

beforeAll(async () => {
  testEnv = await initializeTestEnvironment({
    projectId: 'demo-project-1234',
    firestore: {
      rules: readFileSync('firestore.rules', 'utf8'),
    },
  })
})

afterAll(async () => {
  await testEnv.cleanup()
})

beforeEach(async () => {
  await testEnv.clearFirestore()
})

test('a stranger cannot read a profile', async () => {
  const unauth = testEnv.unauthenticatedContext()
  await assertFails(getDoc(doc(unauth.firestore(), 'profiles/alice')))
})

test('alice reads her own profile, bob cannot', async () => {
  // seed with rules turned off, so the fixture itself is not the thing under test
  await testEnv.withSecurityRulesDisabled(async (context) => {
    await setDoc(doc(context.firestore(), 'profiles/alice'), { owner: 'alice', email: 'a@x.test' })
  })

  const alice = testEnv.authenticatedContext('alice')
  const bob = testEnv.authenticatedContext('bob')

  await assertSucceeds(getDoc(doc(alice.firestore(), 'profiles/alice')))
  await assertFails(getDoc(doc(bob.firestore(), 'profiles/alice')))
})
```

Run it against the emulator:

```bash
firebase emulators:exec "npm test"
```

`assertFails` passing is the attacker half of the paired test. `assertSucceeds` passing is the
legitimate twin. Save the file into the project's own test suite so it keeps running after secure-my-app
is gone.

### Probe a live database

Firestore's REST API answers with the caller's credentials, so an unauthenticated request tests the
`request.auth == null` path exactly as a stranger's browser would.

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  "https://firestore.googleapis.com/v1/projects/<your-project-id>/databases/(default)/documents/<your_collection>?pageSize=1"
```

`200` with documents is a `PUBLIC` reach and a CRITICAL finding. `403` is the pass signal. Confirm the
user owns the project before running this.

---

## Fixes by control ID

Firestore rules use `rules_version = '2'`, `service cloud.firestore`, and match blocks under
`/databases/{database}/documents`.

### R1 and R2. Rules that actually restrict

Locked mode, which is Firebase's own default deny-all, verbatim:

```
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

The two patterns Firebase's own "avoid insecure rules" page names as insecure:

```
allow read, write: if true;                    // open to everyone
allow read, write: if request.auth.uid != null; // open to every account on the internet
```

The second one is the subtler failure and it is everywhere. Anyone can create an account. Logged in is
not authorized.

The owner-scoped rule, which is Firebase's documented content-owner pattern:

```
match /some_collection/{userId}/{document} {
  allow read, write: if request.auth != null && request.auth.uid == userId
}
```

For a collection where ownership is a field rather than a path segment, split the operations. This is
where R3 lives:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // substitute: <your_collection>, ownerId
    match /<your_collection>/{docId} {

      // read the existing document: check the stored owner
      allow get, list: if request.auth != null
                       && resource.data.ownerId == request.auth.uid;

      // create: the owner field in the INCOMING document must be the caller
      allow create: if request.auth != null
                    && request.resource.data.ownerId == request.auth.uid;

      // update: the caller must own the existing doc AND must not reassign it
      allow update: if request.auth != null
                    && resource.data.ownerId == request.auth.uid
                    && request.resource.data.ownerId == resource.data.ownerId;

      // delete: only the existing owner
      allow delete: if request.auth != null
                    && resource.data.ownerId == request.auth.uid;
    }
  }
}
```

The variable distinction, in Firebase's words: "The `resource` variable refers to the requested
document, and `resource.data` is a map of all of the fields and values stored in the document." For
updates, "the `request.resource` variable will contain the pending document state after the
operation."

So `resource.data` is what is already stored, and `request.resource.data` is what the caller is
sending. Which one you read decides whether the rule works.

### R7. Privileged fields

The generic "unchanged field" form Firebase documents:

```
allow update: if request.resource.data.population > 0
              && request.resource.data.name == resource.data.name;
```

Applied to a privilege column:

```
match /profiles/{userId} {
  allow update: if request.auth.uid == userId
                && request.resource.data.role == resource.data.role
                && request.resource.data.plan == resource.data.plan
                && request.resource.data.credits == resource.data.credits;
}
```

Without those three clauses, a user can write `{"role": "admin"}` straight into their own profile
document from the browser console. The UI never showed the field. That is not a control.

VERIFY: an `assertFails` test where a user updates their own doc with `role: 'admin'`, plus an
`assertSucceeds` test where the same user updates `displayName`.

### R8. Storage rules

A separate ruleset with a separate service name and a bucket-shaped match path.

```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {

    match /users/{userId}/{allPaths=**} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null
                   && request.auth.uid == userId
                   && request.resource.size < 5 * 1024 * 1024
                   && request.resource.contentType.matches('image/.*');
    }
  }
}
```

`request.resource.size` and `request.resource.contentType` are how F3 (upload type and size limits)
gets enforced on this stack. There is no multer, no busboy, no server middleware; the rules file is
the upload validator.

`contentType` is client-supplied metadata. It stops the accidental case, not a determined one. Pair it
with serving from a separate origin, and do not trust it as content sniffing.

### D9 and R10. Cloud Functions do their own checks

A callable function is a public HTTPS endpoint. It receives the caller's ID token but it does not
enforce anything.

```js
const { onCall, HttpsError } = require('firebase-functions/https')
const admin = require('firebase-admin')

exports.deleteOrder = onCall(async (request) => {
  const uid = request.auth?.uid
  if (!uid) throw new HttpsError('unauthenticated', 'sign in required')

  const orderId = request.data?.orderId
  if (typeof orderId !== 'string') throw new HttpsError('invalid-argument', 'orderId required')

  const ref = admin.firestore().doc(`orders/${orderId}`)
  const snap = await ref.get()
  if (!snap.exists) throw new HttpsError('not-found', 'no such order')
  if (snap.data().ownerId !== uid) throw new HttpsError('permission-denied', 'not yours')

  await ref.delete()
  return { ok: true }
})
```

Three things here that are the whole point:

- `request.auth?.uid` with an explicit `unauthenticated` throw. The token is verified by the platform;
  its presence is not.
- The ownership check is done by the function, because the Admin SDK bypasses rules entirely.
- `request.data` is caller-controlled and untyped. Validate it.

For an HTTP function (`onRequest`) there is no `request.auth` at all. You must verify the ID token
yourself with `admin.auth().verifyIdToken(...)` or the endpoint is public.

`firebase-functions/https` is the 2nd-gen path shown in the current docs. Older projects import from
`firebase-functions/v2/https`, and 1st-gen code looks like
`functions.https.onCall((data, context) => ...)` with `context.auth`. Read the installed version
before writing either shape.

### F2. App Check

App Check attests that a request comes from your real app on a real device, which is the closest thing
this stack has to bot protection on a public form.

```js
import { initializeApp } from 'firebase/app'
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check'

const app = initializeApp({
  // Your firebase configuration object
})

const appCheck = initializeAppCheck(app, {
  provider: new ReCaptchaV3Provider('your-site-key'),
  isTokenAutoRefreshEnabled: true
})
```

Firebase's own guidance is to use reCAPTCHA Enterprise for new integrations and to upgrade off v3
where possible. The Enterprise provider class name differs; verify it against
<https://firebase.google.com/docs/app-check/web/recaptcha-enterprise-provider> before applying rather
than guessing it.

Attestation providers by platform: Apple platforms use DeviceCheck, App Attest, or reCAPTCHA
Enterprise; Android uses Play Integrity or reCAPTCHA Enterprise; web uses reCAPTCHA Enterprise.
App Check covers Cloud Firestore, Realtime Database, Cloud Storage, callable Cloud Functions, and
others.

**App Check does not replace rules.** Firebase: "App Check guards access to your Google backend
resources and custom backends by requiring API calls to contain a valid App Check token." It proves
which app is calling, never which user may see which row. If a report presents App Check as a fix for
an R-group finding, that report is wrong.

Enabling it is a two-step deploy: ship the client code first, watch the metrics for unattested
traffic, and only then turn on enforcement in the console. Enforcing before the client has rolled out
locks your own users out.

### P8. Webhook signatures on an HTTP function

An `onRequest` function is a public URL. Anyone can POST to it. If it writes to Firestore with the
Admin SDK, which bypasses every rule, then the provider signature is the only thing standing between a
stranger and your billing state.

```js
const { onRequest } = require('firebase-functions/v2/https')
const crypto = require('node:crypto')

exports.stripeWebhook = onRequest((req, res) => {
  // req.rawBody is the unparsed Buffer. req.body has already been JSON-parsed
  // by the Functions runtime, so it can never match the signature.
  const expected = crypto
    .createHmac('sha256', process.env.WEBHOOK_SECRET)
    .update(req.rawBody)
    .digest('hex')

  if (!safeEqual(expected, req.get('x-signature') ?? '')) {
    return res.status(400).send('bad signature')
  }
  return res.status(200).send('ok')
})

function safeEqual(a, b) {
  // timingSafeEqual THROWS when the buffers differ in length, and the caller
  // controls the length. Hash both sides to a fixed 32 bytes first.
  const ha = crypto.createHash('sha256').update(a).digest()
  const hb = crypto.createHash('sha256').update(b).digest()
  return crypto.timingSafeEqual(ha, hb)
}
```

Two things carry the weight here.

**`req.rawBody`, not `req.body`.** The Functions runtime parses the body for you, and a re-serialized
object will not match the bytes the signature covers. This is the single most common reason a
correct-looking Stripe webhook fails in Cloud Functions. With the Stripe SDK, pass `req.rawBody` to
`stripe.webhooks.constructEvent(req.rawBody, sig, secret)` and let it verify; confirm the current
signature against <https://docs.stripe.com/webhooks> before applying.

**`crypto.timingSafeEqual`, never `===`.** A `===` on a signature leaks the answer through how long it
takes to fail. Use `safeEqual` for every attacker-supplied value compared against a secret: webhook
signatures, invitation codes, and any API key you check by value.

`req.rawBody` is not documented on the HTTP-events guide; it is the property the `firebase-functions`
typings add to the Express request and the one Stripe's own Firebase extension uses. See the sources
at the end of this file.

An `onCall` function has no `rawBody` and needs none, because the platform verifies the caller's ID
token. Its risk is D9, not P8.

### K1. The Admin SDK never reaches the client

```bash
rg -n "firebase-admin|serviceAccount|GOOGLE_APPLICATION_CREDENTIALS|private_key" \
  --glob '!node_modules' --glob '!*.lock'
```

Any `*.json` service account file in the repo is a K3 finding and a CRITICAL one; the key grants full
project access with every rule bypassed. It must be rotated, not just deleted. See
`secrets-runbook.md`.

The web `apiKey` in `firebaseConfig` is a different thing and is not a secret. Do not report it as
one. Do check that it has API restrictions applied in the Google Cloud console (K8), which is a
tier 3 recipe the user runs.

### V2. Query only the fields you need

Firestore returns whole documents. There is no column projection on a document read. So the fix is
schema shape, not query shape: keep private fields in a subcollection or a separate document that has
its own stricter rule.

```
match /profiles/{userId} {
  allow read: if request.auth != null;                      // public card

  match /private/{docId} {
    allow read: if request.auth.uid == userId;              // email, phone, stripe id
  }
}
```

If `stripe_customer_id` sits on the same document as `displayName` and the rule allows any signed-in
user to read the profile, every account on the internet has every user's Stripe id. That is a V2
finding with a schema fix, not a query fix.

---

## The traps specific to this stack

**Rules are the only server-side control on client SDK paths.** Repeat this to the user in plain
words. There is no middleware, no route handler, no `if (user.id !== row.owner)` between the browser
and the database. When a rule is wrong, nothing else catches it.

**`allow read, write: if true;` and the test-mode expiry.** Firebase creates databases in a test mode
whose generated ruleset opens everything and is written to stop working after about 30 days, which is
why so many projects ship one line of `if false` panic at the deadline instead of real rules. Grep for
both shapes:

```bash
rg -n 'if true|request\.time\s*<\s*timestamp\.date' firestore.rules storage.rules
```

I could not find the exact generated test-mode ruleset reproduced in Firebase's public docs, so treat
the precise text as unverified and match on the shape, not on a string. What is documented, verbatim
from Firebase, is that test mode "allows anyone to read and overwrite your data."

**`request.auth != null` reads as an auth check and is not an authorization check.** Firebase lists
`allow read, write: if request.auth.uid != null;` as an insecure rule in its own documentation. Anyone
can sign up. If the collection holds per-user data, this rule hands the whole collection to every
account.

**`request.resource.data.owner == request.auth.uid` on an update.** This is the mistake that looks
most correct. `request.resource.data` is the document the *caller sent*. The caller sets `owner` to
their own uid, the rule passes, and they have taken over someone else's document. On create, binding
`request.resource.data.owner == request.auth.uid` is right and necessary. On update and delete, you
must read `resource.data.owner`, the value already stored. Getting these two backwards is the single
highest-value thing to check in a Firebase audit.

**One broad `allow read, write` for everything.** The safe condition genuinely differs per operation:
create binds the incoming owner, update binds the stored owner and forbids reassignment, delete binds
the stored owner, list needs to be safe for a query that returns many documents. Rules do not narrow
a query for you; `list` either allows the whole query or denies it, so a rule written with a single
document in mind can expose a collection.

**Firestore rules and Storage rules are different files with different syntax.** `service
cloud.firestore` with `match /databases/{database}/documents` versus `service firebase.storage` with
`match /b/{bucket}/o`. Securing one and forgetting the other is common, because the console shows them
on separate screens and `firebase deploy` needs `--only firestore:rules,storage`. Check `firebase.json`
for whether a `storage.rules` file is even wired up.

**Untested rules.** A rules file that has never run in the emulator is a hypothesis. The language is
small but its evaluation order and its `get()`/`exists()` calls surprise people, and a syntactically
valid rule can deny everything or allow everything. Deploying untested rules is the failure that
follows test mode as the most common cause of Firebase incidents.

**The Admin SDK ignores rules completely.** Every Cloud Function, every server script, every
`firebase-admin` import operates as a superuser. Perfect rules plus one callable function with no
ownership check is an open database with extra steps.

**`req.body` in an HTTP function webhook.** The Functions runtime parses the body before your handler
sees it, so the signature check compares against bytes that no longer exist. It fails closed while you
are testing, which is why people reach for the fix that actually breaks it: skipping verification. Use
`req.rawBody`, and compare with `crypto.timingSafeEqual`, never `===`.

**Realtime Database is not Firestore.** If you find `database.rules.json`, the rules are JSON with
`.read` and `.write` expressions and a completely different evaluation model, including rule cascading
that Firestore does not have. Do not apply the Firestore rules in this file to it.

---

## Verified against

Checked 2026-09-06.

- <https://firebase.google.com/docs/rules/rules-language> `rules_version = '2'`, service and match block structure, allow operations
- <https://firebase.google.com/docs/rules/basics> locked-mode ruleset verbatim, content-owner pattern
- <https://firebase.google.com/docs/rules/insecure-rules> `if true` and `request.auth.uid != null` named as insecure, with exact snippets
- <https://firebase.google.com/docs/firestore/security/rules-conditions> `resource.data` vs `request.resource.data` definitions, unchanged-field example
- <https://firebase.google.com/docs/storage/security> `service firebase.storage`, `/b/{bucket}/o`, `request.resource.size`, `request.resource.contentType`
- <https://firebase.google.com/docs/rules/unit-tests> `@firebase/rules-unit-testing`, `initializeTestEnvironment`, `assertFails`, `assertSucceeds`, `withSecurityRulesDisabled`, `firebase emulators:exec`
- <https://firebase.google.com/docs/functions/callable> `firebase-functions/https`, `onCall`, `request.auth.uid`, `HttpsError`
- <https://firebase.google.com/docs/app-check> protected products, attestation providers, complementary to Authentication
- <https://firebase.google.com/docs/app-check/web/recaptcha-provider> `initializeAppCheck`, `ReCaptchaV3Provider`, `isTokenAutoRefreshEnabled`
- <https://firebase.google.com/docs/functions/http-events> `onRequest` from `firebase-functions/v2/https`, and that HTTP functions have no CORS configured by default
- <https://github.com/firebase/firebase-functions/pull/420/files> the PR that extends the Express request type with `rawBody`
- <https://github.com/invertase/stripe-firebase-extensions/blob/next/firestore-stripe-payments/functions/src/index.ts> Stripe's own Firebase extension verifying with `req.rawBody` and the `stripe-signature` header
- <https://nodejs.org/api/crypto.html> referenced for `crypto.timingSafeEqual` throwing on a length mismatch; confirm there before relying on the exact error
- <https://firebase.google.com/docs/firestore/quickstart> test mode described as allowing anyone to read and overwrite

Could not verify and must not be stated as fact:

- The exact generated test-mode ruleset, including the `request.time < timestamp.date(...)` expiry
  expression and its 30-day window. Firebase describes test mode but does not reproduce the ruleset on
  any page I could reach. Match on shape; do not quote a string you have not read in the repo.
- A CLI command that prints the currently deployed ruleset. Verify against
  <https://firebase.google.com/docs/reference/rules/rest> or read it in the console.
- The reCAPTCHA Enterprise provider class name for web App Check. Verify against
  <https://firebase.google.com/docs/app-check/web/recaptcha-enterprise-provider> before applying.
- Whether the installed `firebase-functions` major exposes `firebase-functions/https` or
  `firebase-functions/v2/https`. Read `package.json`.
