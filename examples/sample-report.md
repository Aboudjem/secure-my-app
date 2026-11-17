```
VERDICT: DO NOT LAUNCH   coverage 21 checked / 2 unproven / 42 n/a   [static + live: 127.0.0.1:4310]
findings: 3 critical  2 high  6 medium  0 low   scan: gitleaks yes, semgrep installed but not run, osv-scanner no, trufflehog no
DO FIRST
1. K3  Replace the session secret committed in server.js with a new one read from the environment
2. D3  Replace SHA-256 password hashing with a real password hash, then reset every password
3. R10 Put a sign-in check and an admin role check on GET /admin/export
```

> **A real run, not an illustration.** secure-my-app 0.3.0 wrote this report on 2026-11-17, against
> the fixture in [`examples/vulnerable-app/`](vulnerable-app/README.md), which has holes on purpose.
> Agent: Claude Code 2.1.326, headless. Command: `/secure-my-app --report-only --live http://127.0.0.1:4310`.
> The text below is the file the run wrote to `.secure-my-app/report.md`, unedited. The only
> addition is this note. [`sample-surface.json`](sample-surface.json) is the inventory from the same run.
> [`tests/test_fixture.py`](../tests/test_fixture.py) replays the requests behind the findings.
> Your run can differ: the rating is deterministic, the scan is not.

# secure-my-app report: paperboat

Run date 2026-11-17. Mode `--report-only --live http://127.0.0.1:4310`. Nothing in the app was changed.

**What this is.** A read of one 116-line server plus 27 requests to the local host you named. It is
not a penetration test and not a compliance audit. "Not checked, and why" at the end lists what it
could not see.

**How to read the ratings.** The fixture binds to `127.0.0.1`, so today only this machine can reach
it. You answered that it is live, so "PUBLIC" below means "needs no account", which is what a
stranger would have if this were deployed as written. The rating is deterministic, the scan is not.

**Evidence tags.** `[static]` read in the repo. `[executed]` a command run in this session, with its
real output. `[recipe]` a command not run, written out for you.

**Scanner notes.**

- gitleaks ran over the tree and the one commit and reported no leaks. It missed the session secret,
  which a plain grep found. A clean gitleaks run here is not a pass.
- semgrep is installed but was not run: its standard rulesets are fetched from a remote registry.
  The grep patterns from the control catalogue were used instead, which is the weaker mode.
- osv-scanner is absent and not needed: the app has no dependencies.

**Live probe budget.** 27 requests, all to `127.0.0.1:4310`. Sign-ins used only the two README
accounts. The one `PATCH` sent an empty body `{}`, which `Object.assign` turns into no change. No
request changed any data.

---

## CRITICAL K3 (+K4, K5) The key that signs every session is written in the public repo

WHAT The HMAC secret for the `session` cookie is a string literal in `server.js`, so anyone who reads the repo can mint a valid session for any user without a password.

WHERE server.js:10 (the literal), server.js:26-30 (signing), server.js:37-40 (verification)

PROOF

```
[static]   server.js:10   const SESSION_SECRET = "pape...";        (value redacted)
[executed] git grep -c 'SESSION_SECRET = "' fe13fab -- server.js
           -> fe13fab...:server.js:1          (in history, K4)
[executed] sign in as alice over HTTP, then build the same cookie locally from the
           repo secret and the payload {"sub":"u_1"}, and compare the two strings
           -> cookie forged from repo secret == cookie the live server issued: true
[static]   server.js:39-40  the server trusts `sub` and loads that user. Changing
           "u_1" to "u_3" in the payload gives the admin account's session.
```

The comparison proves the running server uses the committed secret, so it is live and unrotated
(K5). No session was forged for an account outside the two you authorised; the last step is read
from the code, not run.

IMPACT Every account, including `root@paperboat.test`, with no password. From there: every invoice, each customer's name, billing email, total and IBAN last four. Lines 15-17 also carry all three account passwords as literals, admin included.

SEVERITY CRITICAL by override: a live, unrotated credential in a public repo. Reach is "anyone who ever cloned it", which the matrix does not model.

FIX

```js
// server.js:10
const SESSION_SECRET = process.env.SESSION_SECRET;
if (!SESSION_SECRET || SESSION_SECRET.length < 32) {
  throw new Error(
    "SESSION_SECRET must be set to at least 32 random characters",
  );
}
```

```bash
# generate the new value; keep it out of the repo
node -e 'console.log(require("node:crypto").randomBytes(32).toString("base64url"))'
```

Order matters. Rotate first: deploy with the new value, which also ends every existing session.
Rewriting git history is optional, comes after, and is a separate conversation; every clone already
has the old value. Move the seeded passwords at lines 15-17 out of source and change the admin one.

VERIFY

```
attacker:  rebuild the cookie from the OLD secret, GET /api/invoices   -> 401 "sign in first"
legit:     sign in as alice, GET /api/invoices                        -> 200, invoice 1041
tree:      grep -n 'SESSION_SECRET = "' server.js                     -> no output
```

STATUS OPEN

---

## CRITICAL D3 Passwords are stored as unsalted SHA-256, and the hashes are public

WHAT Passwords are hashed with one round of SHA-256 and no salt, and the full hash list is served to anyone by `/admin/export`.

WHERE server.js:12 (the hash), server.js:15-17 (stored), server.js:72 (login compare)

PROOF

```
[static]   server.js:12   const sha256 = (s) => crypto.createHash("sha256").update(s).digest("hex");
[executed] curl -s http://127.0.0.1:4310/admin/export        (no cookie)
           -> 200, users[] carry password_hash, 64 hex characters each (f83e...)
[executed] compare alice's exported hash with sha256("<her README password>") locally
           -> alice hash == sha256(README password), no salt: true
```

IMPACT The password of every user, admin included. Unsalted SHA-256 is tried at billions of guesses per second on one GPU, so the export is close to a plaintext password list. That lets a stranger sign in as anyone and try the same passwords on other sites.

SEVERITY PUBLIC x ALL_DATA = CRITICAL. Reasoning: the hashes are reachable with no account today (R10), and they give more than R10 alone, namely working logins and reusable passwords. Once R10 is closed this drops to ADMIN_ONLY x ALL_DATA = MEDIUM, but hashes already served must be treated as cracked.

FIX

```js
// zero-dependency option: scrypt from node:crypto, random salt per user
const hashPassword = (pw) => {
  const salt = crypto.randomBytes(16);
  const key = crypto.scryptSync(String(pw), salt, 32, {
    N: 2 ** 17,
    r: 8,
    p: 1,
    maxmem: 256 * 1024 * 1024,
  });
  return `scrypt$${salt.toString("base64url")}$${key.toString("base64url")}`;
};
const checkPassword = (pw, stored) => {
  const [scheme, salt, key] = String(stored).split("$");
  if (scheme !== "scrypt" || !salt || !key) return false;
  const want = Buffer.from(key, "base64url");
  const got = crypto.scryptSync(
    String(pw),
    Buffer.from(salt, "base64url"),
    want.length,
    { N: 2 ** 17, r: 8, p: 1, maxmem: 256 * 1024 * 1024 },
  );
  return crypto.timingSafeEqual(got, want);
};
// server.js:72
const user = users.find((u) => u.email === email);
if (!user || !checkPassword(password, user.password_hash))
  return send(res, 401, { error: "wrong email or password" });
```

Argon2id through the `argon2` package is the first choice if you accept a dependency. Check the
scrypt or Argon2 parameters against OWASP's current password storage guidance before shipping; they
move. Then force a password reset for all three accounts.

VERIFY

```
store:     the stored value for alice starts with "scrypt$" (or "$argon2id$"), and two users
           with the same password have different stored values
attacker:  POST /login with alice's email and a wrong password   -> 401
legit:     POST /login with alice's email and her password       -> 200 and a session cookie
```

STATUS OPEN

---

## CRITICAL R10 (+D1) Anyone can download every user and every invoice from /admin/export

WHAT `GET /admin/export` returns the whole user list and the whole invoice list with no sign-in and no role check.

WHERE server.js:101-103

PROOF

```
[static]   server.js:101-103   no sessionUser() call, no role test, returns { users, invoices }
[executed] curl -s -o export.json -w '[%{http_code}] %{size_download} bytes' http://127.0.0.1:4310/admin/export
           -> [200] 960 bytes
           top keys: users, invoices     users: 3   invoices: 3
           user keys:    id,email,team,role,password_hash
           invoice keys: id,owner,team,customer,customer_email,total_cents,iban_last4
[executed] for contrast, the other data routes without a cookie:
           GET /api/invoices -> 401     GET /api/invoices/1042 -> 401
```

IMPACT Both teams' complete data in one request, to a visitor with no account: every user's email, team, role and password hash, and every invoice's customer, billing email, total and IBAN last four.

SEVERITY PUBLIC x ALL_DATA = CRITICAL.

FIX

```js
// server.js:101
if (req.method === "GET" && path === "/admin/export") {
  const user = sessionUser(req);
  if (!user) return send(res, 401, { error: "sign in first" });
  if (user.role !== "admin") return send(res, 403, { error: "admins only" });
  return send(res, 200, {
    users: users.map(({ id, email, team, role }) => ({
      id,
      email,
      team,
      role,
    })),
    invoices,
  });
}
```

**Close R6 in the same change.** Today any member can set their own `role` to `admin` through
`PATCH /api/me`, so a role check alone is a gate with a self-service key. The field list above also
closes V2.

VERIFY

```
anonymous:  curl -s -w '[%{http_code}]' $URL/admin/export                  -> 401
member:     same request with alice's cookie                               -> 403
admin:      same request with the admin's cookie                           -> 200, users and invoices
            and no user object has a password_hash key
```

STATUS OPEN

---

## HIGH R4 Any signed-in user can read any invoice by changing the number in the URL

WHAT `GET /api/invoices/:id` looks the invoice up by id alone and never compares its owner or team with the caller.

WHERE server.js:83-92 (the lookup is line 89)

PROOF

```
[static]   server.js:89   const invoice = invoices.find((i) => i.id === id);
[executed] alice (team_1) reads her own invoice:
           GET /api/invoices/1041 -> 200 {"id":1041,"owner":"u_1","team":"team_1","customer":"Harbor Bakery",...}
[executed] alice (team_1) reads bob's invoice:
           GET /api/invoices/1042 -> 200 {"id":1042,"owner":"u_2","team":"team_2","customer":"Northside Dental",
             "customer_email":"billing@northside-dental.test","total_cents":92000,"iban_last4":"0038"}
[executed] bob (team_2) reads alice's invoice:
           GET /api/invoices/1041 -> 200 {"id":1041,"owner":"u_1","team":"team_1",...}
[executed] the list route scopes correctly: alice GET /api/invoices -> 200, invoice 1041 only
```

IMPACT One team's customers, billing contacts, amounts and IBAN digits, readable by the other team. Ids are consecutive (1041, 1042, 1043), so counting upward walks the whole table.

SEVERITY ANY_USER x OTHER_USERS = HIGH.

FIX

```js
// server.js:89
const invoice = invoices.find((i) => i.id === id && i.owner === user.id);
if (!invoice) return send(res, 404, { error: "no such invoice" });
```

If teammates are meant to see each other's invoices, use `i.team === user.team` instead. That is a
product decision; the code today gives no hint which was intended. Return 404 rather than 403 so
the response does not confirm the id exists.

VERIFY

```
alice:  GET /api/invoices/1042 (bob's)   -> 404 "no such invoice"
alice:  GET /api/invoices/1041 (hers)    -> 200, the invoice
bob:    GET /api/invoices/1041 (alice's) -> 404
bob:    GET /api/invoices/1042 (his)     -> 200, the invoice
```

STATUS OPEN

---

## HIGH R6 (+R5) A user can overwrite any field of their own account, including role and team

WHAT `PATCH /api/me` copies the whole request body onto the stored user record with no field list.

WHERE server.js:94-99 (the copy is line 97)

PROOF

```
[static]   server.js:97   Object.assign(user, await readJson(req));
           Every key in the body lands on the record: role, team, id, email, password_hash.
[executed] alice sends PATCH /api/me with body {}  -> 200 {"id":"u_1","email":"alice@paperboat.test","team":"team_1","role":"member"}
           The route is live and accepts alice's session. An empty body was used so nothing changed.
[recipe]   not run, because it changes data:
           curl -s -X PATCH $URL/api/me -H 'content-type: application/json' -H "Cookie: $ALICE" -d '{"role":"admin"}'
           expected today: 200 with "role":"admin"
```

This finding rests on static evidence. The write itself was not sent, because this run does not
modify data. Line 97 leaves no branch that could refuse a field.

IMPACT A member makes themselves `admin` or moves themselves to the other team (R5: the tenant comes from the request body). No route reads `role` today, so the admin flag buys nothing yet, but it defeats the R10 fix the moment that lands. Overwriting `id` with another user's id makes that user's session resolve to the wrong record, which locks accounts out.

SEVERITY ANY_USER x SELF_ESCALATION = HIGH.

FIX

```js
// server.js:97
const body = await readJson(req);
if (body === null || typeof body !== "object" || Array.isArray(body))
  return send(res, 400, { error: "bad body" });
if (typeof body.email === "string" && /^[^@\s]+@[^@\s]+$/.test(body.email))
  user.email = body.email;
// id, team, role and password_hash are never taken from the body
```

Decide which fields a user may edit. The app shows only `email` as a plausible one.

VERIFY

```
attacker:  PATCH /api/me {"role":"admin","team":"team_2"}  -> the response still shows role member, team team_1
           then read it back: GET /admin/export as admin shows alice unchanged
legit:     PATCH /api/me {"email":"alice2@paperboat.test"} -> 200 with the new email
```

STATUS OPEN

---

## MEDIUM D2 The session cookie has no HttpOnly, Secure or SameSite attribute

WHAT The login response sets `session=...; Path=/` and nothing else.

WHERE server.js:74

PROOF

```
[executed] curl -s -i -X POST $URL/login -H 'content-type: application/json' -d '{"email":"alice@...","password":"..."}'
           -> set-cookie: session=eyJzdW...REDACTED; Path=/
```

IMPACT The cookie is readable by any script on the origin, is sent over plain HTTP, and has no cross-site rule of its own. No path to steal it was demonstrated here: the app serves no HTML, so there is no script injection point.

SEVERITY PUBLIC x INFO = MEDIUM, following the catalogue's own treatment of a missing browser hardening attribute. It is a missing layer, not a demonstrated theft.

FIX

```js
// server.js:74   (add Secure once the app is served over HTTPS; it will not be set over http)
{ "set-cookie": `session=${sign({ sub: user.id })}; Path=/; HttpOnly; SameSite=Lax; Secure; Max-Age=28800` }
```

VERIFY

```
curl -s -i -X POST $URL/login ... | grep -i '^set-cookie'   -> shows HttpOnly, SameSite=Lax and Secure
legit: sign in from the real client, then GET /api/invoices -> 200
```

STATUS OPEN

---

## MEDIUM D6 Login accepts unlimited password guesses

WHAT Nothing limits attempts on `POST /login`, per address or per account.

WHERE server.js:70-75

PROOF

```
[static]   no limiter, counter or lockout anywhere in server.js
[executed] 12 POSTs to /login with wrong passwords, alternating alice's email and an unknown one
           -> 12 x 401, none 429, each under 1 ms
```

IMPACT A stranger can guess passwords for a known email as fast as the server answers. No account was taken this way in this run; the proof is that nothing slows the attempt.

SEVERITY PUBLIC x INFO = MEDIUM. Reasoning: what is proven is the missing throttle, not a takeover.

FIX

```js
// in-process counter, fine for one instance. With more than one instance use a shared store.
const attempts = new Map(); // key -> { n, resetAt }
function tooMany(key, max = 10, windowMs = 15 * 60 * 1000) {
  const now = Date.now();
  const a = attempts.get(key);
  if (!a || a.resetAt < now) {
    attempts.set(key, { n: 1, resetAt: now + windowMs });
    return false;
  }
  return ++a.n > max;
}
// in POST /login, before the lookup
if (
  tooMany(`ip:${req.socket.remoteAddress}`) ||
  tooMany(`email:${String(email).toLowerCase()}`)
) {
  return send(
    res,
    429,
    { error: "too many attempts, try later" },
    { "retry-after": "900" },
  );
}
```

Behind a proxy `req.socket.remoteAddress` is the proxy. Take the client address from the proxy's
header only when you know the hop count.

VERIFY

```
attacker:  12 rapid wrong-password POSTs  -> a 429 before the twelfth
legit:     one correct sign-in from a different address and account -> 200
```

STATUS OPEN

---

## MEDIUM V3 (+P2) A malformed request returns the stack trace and server file paths

WHAT The catch-all error handler sends `err.stack` to the client, and a body that is not valid JSON is enough to trigger it without signing in.

WHERE server.js:108-112 (handler), server.js:54 (unvalidated parse), server.js:88 (a second throw, signed-in only)

PROOF

```
[executed] curl -s -w ' [%{http_code}]' -X POST $URL/login -H 'content-type: application/json' -d '{'
           -> {"error":"SyntaxError: Expected property name or '}' in JSON at position 1 ...",
               "stack":"SyntaxError: ...\n    at JSON.parse (<anonymous>)\n    at IncomingMessage.<anonymous>
               (<absolute path on this machine>/paperboat/server.js:54:28)\n    at IncomingMessage.emit (node:events:519:28)..."} [500]
```

The absolute path is cut here on purpose; the real response contained the full directory, including
the local account name.

IMPACT Directory layout, the operating system account name, file and line numbers, and Node internals, to anyone. No user data.

SEVERITY PUBLIC x INFO = MEDIUM.

FIX

```js
// server.js:108
const server = http.createServer((req, res) => {
  route(req, res).catch((err) => {
    if (err instanceof SyntaxError || err instanceof TypeError)
      return send(res, 400, { error: "bad request" });
    console.error(err); // detail stays in the server log
    send(res, 500, { error: "internal error" });
  });
});
```

Better still, validate each body where it is read and return 400 there, so a client mistake is
never an exception.

VERIFY

```
attacker:  the same curl -> 400 {"error":"bad request"}, no "stack" key, no file path
legit:     POST /login with valid JSON and the right password -> 200
```

STATUS OPEN

---

## MEDIUM V5 No security event is recorded anywhere

WHAT Failed sign-ins, refused requests and the full data export leave no trace.

WHERE server.js:73, 79, 86, 96, 102 (every refusal and the export return without logging)

PROOF

```
[executed] grep -n 'console\.' server.js   -> 115: the startup line only
[static]   the 12 failed sign-ins and the export download in this run passed through code paths with no log call
```

The server's own output stream was not visible to this run, so the claim rests on the code.

IMPACT If someone downloads `/admin/export` or guesses passwords, you cannot find out that it happened, when, or from where.

SEVERITY PUBLIC x INFO = MEDIUM. It hands an attacker nothing directly; it removes your ability to notice.

FIX

```js
const audit = (event, req, extra = {}) =>
  console.log(
    JSON.stringify({
      t: new Date().toISOString(),
      event,
      ip: req.socket.remoteAddress,
      path: req.url,
      ...extra,
    }),
  );
// call it on: failed login (with the email, never the password), every 401 and 403, and every admin export
```

VERIFY

```
one failed sign-in -> one line in the server log with event "login_failed" and no password in it
```

STATUS OPEN

---

## MEDIUM D5 Sessions never expire and cannot be ended

WHAT The signed cookie holds only the user id. There is no expiry, no sign-out route and no server-side session record.

WHERE server.js:74 (payload `{ sub }`), server.js:32-41 (no time check)

PROOF

```
[executed] decode the payload of the cookie the server issued to alice -> {"sub":"u_1"}
[static]   sessionUser() checks the signature and nothing else; grep for expiry, max-age, logout, revoke -> no hits
```

IMPACT A cookie copied once works until the signing secret changes. A user cannot sign out, and changing a password leaves old cookies valid.

SEVERITY ADMIN_ONLY x OTHER_USERS = MEDIUM. Reasoning: the attacker must first hold someone's cookie, which is privilege they would have to steal.

FIX

```js
// issue:   sign({ sub: user.id, exp: Date.now() + 8 * 60 * 60 * 1000 })
// verify, in sessionUser() after the signature check:
const { sub, exp } = JSON.parse(
  Buffer.from(body, "base64url").toString("utf8"),
);
if (typeof exp !== "number" || exp < Date.now()) return null;
```

For real revocation keep a server-side session id that can be deleted, and add a sign-out route.
While there, compare the signature with `crypto.timingSafeEqual` instead of `!==` (line 38).

VERIFY

```
attacker:  a cookie whose exp is in the past, correctly signed -> 401
legit:     a fresh sign-in cookie -> 200 on GET /api/invoices
```

STATUS OPEN

---

## MEDIUM V2 The export sends password hashes that no caller needs

WHAT `/admin/export` returns whole user records, `password_hash` included.

WHERE server.js:102

PROOF

```
[executed] GET /admin/export -> user keys: id,email,team,role,password_hash
```

IMPACT Even after the route is admin-only, every export file and every admin browser holds the full hash list.

SEVERITY ADMIN_ONLY x ALL_DATA = MEDIUM. The public reach of this same response is counted once, under R10.

FIX The field list in the R10 fix: `users.map(({ id, email, team, role }) => ({ id, email, team, role }))`.

VERIFY

```
admin: GET /admin/export -> 200, and no user object has a password_hash key
```

STATUS OPEN

---

# UNPROVEN appendix

These carry no severity and do not move the verdict.

**P4 CSRF protection on cookie-authenticated writes.**
The control is absent in code: no token, no `Origin` check, no `SameSite` on the cookie.
`[executed]` a `PATCH /api/me` carrying `Origin: https://evil.example` and alice's cookie returned 200. But a browser attack was not shown to work. The only cookie-authenticated write is a `PATCH`,
which browsers preflight, and `[executed]` the preflight (`OPTIONS /api/me` with a foreign origin)
returned 404 with no `Access-Control-Allow-Origin`, so a browser would stop there. Protection today
is an accident of the method. It ends the day someone adds a `POST` write route or CORS headers.
To settle it: open a page on another origin in a browser where alice is signed in and run
`fetch("http://127.0.0.1:4310/api/me", {method:"PATCH", credentials:"include", body:"{}"})`.
A network error means blocked; a 200 means it is a finding.

**P10 HTTPS forced and HSTS set.**
The only host given is plain `http://127.0.0.1:4310` and the code has no TLS, no redirect and no
HSTS header. On loopback there is no wire to listen on, and this run cannot see whether a TLS proxy
would sit in front of a real deployment. To settle it on a deployed host:
`curl -sI http://<host>/` must redirect to https, and `curl -sI https://<host>/` must show
`strict-transport-security`.

---

# Coverage

65 controls: 21 checked (5 pass, 16 fail), 2 unproven, 42 n/a.

| Group  | Pass   | Fail           | Unproven | N/A                         |
| ------ | ------ | -------------- | -------- | --------------------------- |
| KEYS   |        | K3 K4 K5       |          | K1 K2 K6 K7 K8              |
| DOOR   | D9     | D1 D2 D3 D5 D6 |          | D4 D7 D8                    |
| ROOMS  |        | R4 R5 R6 R10   |          | R1 R2 R3 R7 R8 R9           |
| PIPES  | P5 P13 | P2             | P4 P10   | P1 P3 P6 P7 P8 P9 P11 P12   |
| VAULT  | V4     | V2 V3 V5       |          | V1 V6 V7 V8                 |
| FLOOR  | F9     |                |          | F1 F2 F3 F4 F5 F6 F7 F8 F10 |
| SUPPLY |        |                |          | S1 S2 S3 S4 S5 S6 S7        |

**What passed, and on what evidence.**

- D9 auth fails closed. `[executed]` a garbage cookie returned 401; `[static]` every exception path ends in a 500, never a 200 with data.
- P5 CORS. `[executed]` a request with `Origin: https://evil.example` got no `Access-Control-Allow-Origin` back; `[static]` no CORS header is set anywhere.
- P13 no unsafe deserialization. `[static]` the cookie is decoded with `JSON.parse`, and only after its signature is checked (lines 37-39).
- V4 no secrets in logs. `[executed]` the only `console` call is the startup line.
- F9 login does not reveal which emails exist. `[executed]` a known and an unknown email got the same 401 body. Timing was not measured. There is no signup or reset route to compare.

**Why the N/A are N/A.**

- No database, so no RLS, policies, storage buckets, views or SQL: R1 R2 R3 R7 R8 R9 P1 V1 V7.
- No browser bundle, client env prefix, client key or third-party key: K1 K2 K6 K8 V8. No config or secrets file: K7 (the literal in `server.js` is K3).
- No JWT library, reset or magic link, or MFA: D4 D7 D8.
- No HTML is served, so no rendering sink and no page to frame: P3 P9. `[executed]` the response headers are `content-type`, `Date`, `Connection`, `Keep-Alive` only.
- No outbound fetch, redirect, webhook, GraphQL or file read: P6 P7 P8 P11 P12.
- No static files or public directory: V6 (the export endpoint is R10).
- No paid call, public form, upload, checkout, status field, model call or paginated list: F1 through F8, F10.
- No dependencies, lockfile, CI or preview environment: S1 through S7. `[static]` `package.json` has no dependencies and `server.js` requires only `node:http` and `node:crypto`.

---

# Not checked, and why

- **The two data-changing requests.** The `role` write in R6 was not sent. It is proven from the code and written out as a recipe.
- **The admin account.** No sign-in or forged session was made for `root@paperboat.test`. You authorised the two README accounts only.
- **Request size and slow requests.** `readJson` (lines 48-59) has no body cap and the server sets no timeouts. Proving it means sending load, which this skill does not do.
- **Timing.** The signature compare on line 38 uses `!==`. Timing attacks need a running system and many requests.
- **The Node runtime itself.** Its version and patch level were not checked.
- **Everything outside the repository.** Cloud IAM, network rules and firewalls, DNS and registrar access, subdomain takeover, device and physical security, social engineering, insider access, anything behind a login not given, any service the app would call, race conditions, cryptographic implementation review, and whether anyone would respond to an incident.

A report with fewer findings than this one would still not mean the app is safe. It would mean
nothing rose to critical or high in what this run could check.
