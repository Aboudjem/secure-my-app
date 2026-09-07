# Express and Postgres

The per-stack answer to the FIX column in `controls.md`. Control IDs are the anchors.

Express ships with almost nothing on. Every control in this file is something you add. That is the
opposite of Django or Rails, where the job is finding what somebody switched off, and it means an
Express app that has never been audited is usually missing whole groups rather than failing one check.

---

## How to fingerprint this stack

| Marker | What it proves |
| --- | --- |
| `express` in `package.json` dependencies | Express. Check the major: 4 and 5 differ on error handling and `req.query` |
| `app.use(` / `express.Router()` in source | Confirms it is used as the server, not a transitive dep |
| `fastify` instead | Different plugin names. Most of this file's reasoning still holds, the code does not |
| `pg` or `pg-pool` | node-postgres, raw SQL |
| `knex`, `drizzle-orm`, `prisma`, `typeorm`, `sequelize` | Query builder or ORM. Each has its own raw escape hatch to grep for |
| `helmet`, `cors`, `express-rate-limit`, `express-session` | Which controls someone already reached for |
| `csurf` in `package.json` | Deprecated. See P4 |
| `passport`, `jsonwebtoken`, `jose`, `bcrypt`, `argon2` | The auth path |
| `app.set('trust proxy', ...)` | Someone thought about proxies. Read the value |

```bash
npm ls express helmet cors express-rate-limit csurf csrf-csrf csrf-sync express-session pg 2>/dev/null
node -p "require('express/package.json').version"
```

---

## The exact commands

### Reach the database

```bash
# from the app's own env, without echoing it into the report
psql "$DATABASE_URL" -c "\dt"
psql "$DATABASE_URL" -c "select column_name, data_type from information_schema.columns
  where table_name = '<your_table>';"
psql "$DATABASE_URL" -c "select relname from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname='public' and c.relkind='r' and not c.relrowsecurity;"
```

Postgres RLS on a plain Express app is uncommon and usually N/A: the app connects as one privileged
role and does its own filtering in SQL. If that is the case, say so and put the weight on R4 and R5
instead of R1 and R2. Do not report every table as an R1 finding on an app that never intended to use
RLS.

### Enumerate the routes

```bash
rg -n "app\.(get|post|put|patch|delete|all)\(|router\.(get|post|put|patch|delete|all)\(" \
  --glob '!node_modules' -g '*.{js,ts,mjs}'
```

Feed that list into `surface.json`. Every dynamic segment (`/:id`) is an R4 candidate.

### Look at the live headers

```bash
curl -sI "$URL/" | tr 'A-Z' 'a-z' | rg \
  'content-security-policy|strict-transport-security|x-content-type-options|referrer-policy|x-frame-options|x-powered-by'
```

`x-powered-by: Express` present means `helmet()` is not on that route, since helmet removes it.

### Prove a rate limit exists

Only against a host the user owns, and only with an explicit yes.

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w '%{http_code} ' -X POST "$URL/api/login" \
    -H 'content-type: application/json' -d '{"email":"a@example.com","password":"x"}'
done; echo
```

A `429` before the twelfth is the pass signal for D6. Twelve `401`s is the finding.

---

## Fixes by control ID

### P9. Security headers

```js
const express = require('express')
const helmet = require('helmet')

const app = express()
app.use(helmet())
```

That one line sets 13 headers. Verbatim from helmet's docs, the defaults are:

| Header | Default value |
| --- | --- |
| `Content-Security-Policy` | `default-src 'self';base-uri 'self';font-src 'self' https: data:;form-action 'self';frame-ancestors 'self';img-src 'self' data:;object-src 'none';script-src 'self';script-src-attr 'none';style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |
| `Origin-Agent-Cluster` | `?1` |
| `Referrer-Policy` | `no-referrer` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Content-Type-Options` | `nosniff` |
| `X-DNS-Prefetch-Control` | `off` |
| `X-Download-Options` | `noopen` |
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Permitted-Cross-Domain-Policies` | `none` |
| `X-Powered-By` | removed |
| `X-XSS-Protection` | `0` |

**What helmet does NOT do, and people assume it does:**

- No CORS. `helmet()` and `cors()` are different packages solving different problems. See P5.
- No rate limiting. See D6 and F1.
- No CSRF protection. See P4.
- No `Cross-Origin-Embedder-Policy`. Helmet's docs: "This header is not set by default." It breaks
  most third-party embeds, which is why.
- No `Permissions-Policy`. Not in the default set. Add it yourself if you want it.
- No body size limit and no request timeout. See F10 and the slow-loris note below.
- No HSTS `preload`. Correct. Do not add it on day one, see `wrong-advice.md`.
- `X-XSS-Protection: 0` is deliberate and correct. If you find `1; mode=block` set by hand anywhere,
  that is a finding to remove, not to keep.

The default CSP contains `'unsafe-inline'` on `style-src`. That is a real weakening, and it is a
separate lower-severity finding, not a reason to call P9 a fail.

### P5. CORS as an allowlist

```js
const cors = require('cors')

const allowlist = ['https://app.example.com', 'https://www.example.com']

app.use(cors({
  origin(origin, cb) {
    // no Origin header: same-origin, curl, or a server-to-server call
    if (!origin) return cb(null, true)
    return allowlist.includes(origin) ? cb(null, true) : cb(new Error('origin not allowed'))
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
}))
```

`cors()` with no options sends `Access-Control-Allow-Origin: *`. With `credentials: true` a wildcard
is rejected by browsers anyway, so the dangerous shape is `origin: true`, which reflects whatever
`Origin` the caller sent and therefore allows everyone with credentials. Grep for `origin: true` and
`origin: '*'`.

### P4. CSRF on cookie-authenticated writes

**`csurf` is dead. Do not use it, this used to be the recommendation.** `expressjs/csurf` is archived
and unmaintained and carries its own deprecation notice. If it is in `package.json`, removing it is
part of the fix.

Two maintained replacements. Pick by whether you have a server-side session.

**With sessions, use `csrf-sync` (synchroniser token):**

```js
const { csrfSync } = require('csrf-sync')

const {
  invalidCsrfTokenError,
  generateToken,
  getTokenFromRequest,
  getTokenFromState,
  storeTokenInState,
  revokeToken,
  csrfSynchronisedProtection,
} = csrfSync()

app.use(session(/* your existing session config */))
app.use(csrfSynchronisedProtection)

app.get('/csrf-token', (req, res) => res.json({ token: generateToken(req) }))
```

**Stateless, use `csrf-csrf` (double submit cookie), v4:**

```js
const { doubleCsrf } = require('csrf-csrf')

const {
  doubleCsrfProtection,
  generateCsrfToken,
  validateRequest,
  invalidCsrfTokenError,
} = doubleCsrf({
  getSecret: () => process.env.CSRF_SECRET,          // required
  getSessionIdentifier: (req) => req.session.id,     // required in v4
})

app.use(doubleCsrfProtection)
app.get('/csrf-token', (req, res) => res.json({ token: generateCsrfToken(req, res) }))
```

Defaults you should know rather than override blindly: `cookieName` is
`"__Host-psifi.x-csrf-token"`, and the `__Host-` prefix requires `secure: true` and HTTPS, so it will
not work over plain HTTP in local dev. `getCsrfTokenFromRequest` defaults to
`(req) => req.headers["x-csrf-token"]`, so your client must send that header.
`ignoredMethods` defaults to `["GET", "HEAD", "OPTIONS"]`.

The v3 names were `generateToken` and `getTokenFromRequest`. In v4 they are `generateCsrfToken` and
`getCsrfTokenFromRequest`, and `getSessionIdentifier` became required. Check the installed major
before writing either name.

If the API is authenticated only by an `Authorization: Bearer` header and never by a cookie, CSRF is
`N/A`. Say so; do not add a token flow that nothing needs.

### D6 and F1. Rate limiting

```js
const rateLimit = require('express-rate-limit')

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 10,                    // v7 renamed `max` to `limit`; `max` still works
  standardHeaders: 'draft-7',
  legacyHeaders: false,
  // store: new RedisStore({ ... })   // see the trap below
})

app.use('/api/login', authLimiter)
app.use('/api/password-reset', authLimiter)
app.use('/api/signup', authLimiter)
```

Create the limiter once, at startup. `ERR_ERL_CREATED_IN_REQUEST_HANDLER` fires when a limiter is
constructed inside a handler, which silently gives every request its own fresh counter.

Do not reuse one `store` instance across two limiters; that is `ERR_ERL_STORE_REUSE`. Give each its
own store or its own `prefix`.

### D6 prerequisite. `trust proxy`

If the app runs behind a load balancer, a CDN, nginx, Fly, Render, Heroku or Vercel, `req.ip` is the
proxy's address until you set this. Every IP-keyed rate limit then counts the whole internet as one
client and either blocks everyone or nobody.

```js
// number of proxies between the client and this process
app.set('trust proxy', 1)
```

Express's own table of accepted values: a boolean, an IP address or subnet or array of them (with the
preconfigured names `loopback`, `linklocal`, `uniquelocal`), a number of hops, or a function. The
default is `false`, meaning "the app is understood as directly facing the client and the client's IP
address is derived from `req.socket.remoteAddress`".

Getting it wrong in either direction is a finding, and express-rate-limit will tell you which:

| Symptom | Error code | Meaning |
| --- | --- | --- |
| `trust proxy` is `true` | `ERR_ERL_PERMISSIVE_TRUST_PROXY` | "This error is logged when the `trust proxy` setting is set to `true`." Any caller can prepend a fake `X-Forwarded-For` and get a fresh bucket per request |
| `X-Forwarded-For` present, `trust proxy` is `false` | `ERR_ERL_UNEXPECTED_X_FORWARDED_FOR` | Every request keys on the proxy's IP. One shared bucket for all users |
| `req.ip` undefined | `ERR_ERL_UNDEFINED_IP_ADDRESS` | Supply a custom `keyGenerator` |
| custom `keyGenerator` uses a bare IPv6 address | `ERR_ERL_KEY_GEN_IPV6` | An IPv6 client rotates addresses within its own /64 and walks straight past the limit. Wrap with the `ipKeyGenerator` helper |

`app.set('trust proxy', true)` is the single most common broken rate limit in this stack. Use the hop
count, or the proxy's subnet, never `true`.

### P1. Parameterized queries

node-postgres, the correct form:

```js
const text = 'INSERT INTO users(name, email) VALUES($1, $2) RETURNING *'
const values = ['brianc', 'brian@example.com']
const res = await client.query(text, values)
```

The wrong forms to grep for. All three are injectable:

```js
client.query(`SELECT * FROM users WHERE email = '${req.body.email}'`)   // template literal
client.query("SELECT * FROM users WHERE id = " + req.params.id)          // concatenation
knex.raw(`select * from orders where id = ${req.params.id}`)             // raw with interpolation
```

```bash
rg -n 'query\(\s*`[^`]*\$\{' --glob '!node_modules'
rg -n '\.raw\(\s*`[^`]*\$\{|sql\.raw|knex\.raw|\$queryRawUnsafe|\$executeRawUnsafe' --glob '!node_modules'
```

Prisma's `$queryRaw` with a tagged template is parameterized. `$queryRawUnsafe` is not, and the name is
the only warning you get.

Placeholders bind values, not identifiers. A table or column name cannot be a `$1`. If user input
chooses a column, the fix is an allowlist, not a placeholder.

### P2 and R6. Validate and allowlist the body

```js
const { z } = require('zod')

const UpdateProfile = z.object({
  fullName: z.string().min(1).max(120),
  website: z.string().url().optional(),
})
// role, isAdmin, plan, credits, balance are absent on purpose.

app.patch('/api/profile', requireAuth, async (req, res) => {
  const parsed = UpdateProfile.safeParse(req.body)
  if (!parsed.success) return res.status(400).json({ errors: parsed.error.flatten().fieldErrors })

  const { fullName, website } = parsed.data
  await pool.query(
    'update profiles set full_name = $1, website = $2 where id = $3',
    [fullName, website ?? null, req.user.id]
  )
  res.json({ ok: true })
})
```

The R6 finding is any of these:

```bash
rg -n '\.\.\.\s*req\.body|update\(\s*req\.body|insert\(\s*req\.body|Object\.assign\([^,]+,\s*req\.body' \
  --glob '!node_modules'
```

Also cap the body size, which Express does not do by default in a useful way:

```js
app.use(express.json({ limit: '100kb' }))
app.use(express.urlencoded({ extended: true, limit: '100kb' }))
```

### R4. Ownership on every by-id route

The filter goes in the `WHERE`, not in an `if` after the fetch.

```js
// finding: id alone
const { rows } = await pool.query('select * from orders where id = $1', [req.params.id])

// fix: id AND the session subject
const { rows } = await pool.query(
  'select id, total, status, created_at from orders where id = $1 and user_id = $2',
  [req.params.id, req.user.id]
)
if (rows.length === 0) return res.status(404).end()
```

Return `404` rather than `403` on a row the caller does not own, so the response does not confirm the
id exists.

VERIFY, both directions: signed in as A, `GET /api/orders/<B's id>` returns 404, and
`GET /api/orders/<A's id>` still returns 200.

### R5. Tenant from the session

```js
// finding
const orgId = req.body.orgId || req.query.orgId || req.headers['x-org-id']

// fix
const orgId = req.user.orgId          // set by requireAuth from the verified session
```

If the user can belong to several orgs, take the requested org from the request, then check
membership in the database and reject on miss. Never take it and use it.

### D1 and D9. One auth middleware, failing closed

```js
async function requireAuth(req, res, next) {
  try {
    const token = req.cookies?.session
    if (!token) return res.status(401).end()
    const payload = jwt.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] })
    req.user = { id: payload.sub, orgId: payload.org }
    return next()
  } catch {
    return res.status(401).end()      // never next(), never a default user
  }
}
```

The fail-open shapes to grep for:

```bash
rg -n -A6 'catch\s*\(' --glob '!node_modules' | rg -n 'next\(\)|return true|isAuth\s*=\s*true'
```

A `catch` that calls `next()` turns an expired-token error, a database blip, or a typo in an env var
into a logged-in session. This is the class behind the best-known AI-app breach. Check it even when
the code looks fine.

### D2. Session cookie flags

```js
res.cookie('session', token, {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax',        // 'strict' if no cross-site login redirect flow
  path: '/',
  maxAge: 1000 * 60 * 60 * 24 * 7,
})
```

With `express-session`:

```js
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, secure: true, sameSite: 'lax', maxAge: 86400000 },
}))
```

`secure: true` needs `app.set('trust proxy', 1)` behind a TLS-terminating proxy, or the cookie is
never set. That is the same setting as the rate-limit fix, and it is one more reason to get it right.

### D3. Password hashing

```js
const argon2 = require('argon2')

const hash = await argon2.hash(password, {
  type: argon2.argon2id,
  memoryCost: 19456,   // 19 MiB, the OWASP minimum
  timeCost: 2,
  parallelism: 1,
})
const ok = await argon2.verify(hash, password)
```

bcrypt with a work factor of at least 10 is acceptable legacy, not the recommendation. If you keep
bcrypt, know that it silently truncates input at 72 bytes.

Never `crypto.createHash('sha256')` on a password. Grep:

```bash
rg -n -i "createHash\(\s*['\"](md5|sha1|sha256)" --glob '!node_modules'
```

### D4. JWT verification

```js
// finding: decode is not verify. It parses an unsigned token and returns its claims.
const payload = jwt.decode(token)

// fix: verify with a pinned algorithm list
const payload = jwt.verify(token, secret, { algorithms: ['HS256'] })
```

Omitting `algorithms` is what makes `alg: none` and RS256-to-HS256 confusion possible. With an RS
keypair, pin `['RS256']` and pass the public key; never let the library pick.

### P6. SSRF

```js
const dns = require('node:dns/promises')
const net = require('node:net')

async function assertPublicUrl(raw) {
  const u = new URL(raw)
  if (u.protocol !== 'https:' && u.protocol !== 'http:') throw new Error('scheme')
  const { address } = await dns.lookup(u.hostname)
  if (isPrivate(address)) throw new Error('private address')
  return u
}

function isPrivate(ip) {
  if (net.isIPv4(ip)) {
    const [a, b] = ip.split('.').map(Number)
    return a === 10 || a === 127 || a === 0 || a === 169 && b === 254
      || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168)
  }
  return ip === '::1' || ip.startsWith('fc') || ip.startsWith('fd') || ip.startsWith('fe80')
}
```

Check after DNS resolution, not on the string, and set `redirect: 'manual'` on the fetch so a
`302` to `169.254.169.254` cannot walk around the check. This is a mitigation, not a guarantee: DNS
rebinding still exists. An allowlist of hostnames beats a denylist of addresses whenever the feature
allows one.

### P8. Webhook signatures, and constant-time comparison

Two things break a correct-looking webhook check, and the first one is the most common reason a
Stripe integration silently accepts forged events.

**The raw body must survive.** `express.json()` parses and discards the exact bytes the signature was
computed over, so by the time your handler runs the payload no longer matches. Mount the raw parser
on the webhook path only, before the global JSON parser.

```js
import express from "express";
import crypto from "node:crypto";

const app = express();

// The webhook route gets raw bytes. Mount it BEFORE app.use(express.json()).
app.post("/api/webhooks/stripe",
  express.raw({ type: "application/json" }),
  (req, res) => {
    // req.body is a Buffer here, not an object
    const sig = req.get("stripe-signature");
    // With the SDK, hand it the Buffer and let it verify:
    //   stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET)
    // Confirm the current signature against https://docs.stripe.com/webhooks before applying.
  });

app.use(express.json()); // everything else
```

**The comparison must be constant time.** `===` on a signature leaks the answer through how long it
takes to fail. `crypto.timingSafeEqual` is the answer, with one gotcha: **it throws when the two
buffers differ in length**, which an attacker controls. Hash both sides to a fixed length first, so
the lengths always match and the throw becomes impossible.

```js
function safeEqual(a, b) {
  const ha = crypto.createHash("sha256").update(a).digest();
  const hb = crypto.createHash("sha256").update(b).digest();
  return crypto.timingSafeEqual(ha, hb); // both are always 32 bytes
}

// Verifying your own HMAC webhook (a provider with no SDK):
const expected = crypto
  .createHmac("sha256", process.env.WEBHOOK_SECRET)
  .update(req.body) // the raw Buffer
  .digest("hex");

if (!safeEqual(expected, req.get("x-signature") ?? "")) {
  return res.status(400).send("bad signature");
}
```

Never write `if (expected === received)`. Use `safeEqual` for **every** attacker-supplied value you
compare against a secret: webhook signatures, password reset tokens, email verification tokens, API
keys, and session identifiers you look up by value.

VERIFY: an unsigned POST to the webhook route returns 400, and a correctly signed one still returns
200. Both halves, per the paired test.

### P7. Open redirect

```js
const next = req.query.next ?? '/'
const dest = new URL(next, `https://${req.headers.host}`)
if (dest.origin !== `https://${req.headers.host}`) return res.redirect('/')
res.redirect(dest.pathname + dest.search)
```

`next.startsWith('/')` is not enough on its own: `//evil.example` starts with `/` and is a
protocol-relative absolute URL.

### V3. Errors that do not leak

Express 4 and 5 both need an explicit error handler with four arguments, registered last.

```js
app.use((err, req, res, _next) => {
  req.log?.error({ err }, 'unhandled')          // full detail to the log
  res.status(err.status || 500).json({ error: 'Internal Server Error' })   // nothing to the client
})
```

Never `res.json(err)` and never `res.send(err.stack)`.

### F10. Bounded pagination

```js
const limit = Math.min(Number(req.query.limit) || 50, 100)
const offset = Math.max(Number(req.query.offset) || 0, 0)
await pool.query('select ... limit $1 offset $2', [limit, offset])
```

An unclamped `limit` is a free full-table export over your own API.

---

## The traps specific to this stack

**`app.use(helmet())` is read as "headers done".** It is 13 headers and no CORS, no CSRF, no rate
limit, no `Permissions-Policy`, no `Cross-Origin-Embedder-Policy`, no body limit. Say which of those
the app still lacks rather than marking P9 green and moving on.

**Recommending `csurf`.** It is archived. Any advice, any generated code, any blog post from before
2023 that reaches for it is wrong now. The maintained options are `csrf-csrf` and `csrf-sync`, and
which one you pick depends on whether the app has sessions.

**`express-rate-limit` with the default MemoryStore behind more than one instance.** The counter lives
in the process. Two instances behind a load balancer double the effective limit; ten instances
multiply it by ten; an autoscaler makes it unknowable. The docs also note that "all rate limits in the
default MemoryStore are reset when the node.js process is restarted", so a deploy clears every
counter. A limiter that looks configured and does not limit is worse than none, because it stops
anyone looking again. If the app runs more than one process, the fix is a shared store
(`rate-limit-redis` or equivalent) and the finding stands until it has one.

**`app.set('trust proxy', true)`.** It reads as the confident choice and it is the insecure one. With
`true`, Express takes the left-most `X-Forwarded-For` entry, and that entry is whatever the client
typed. Every request can carry a new fake IP and every IP-keyed limit becomes decorative.
express-rate-limit logs `ERR_ERL_PERMISSIVE_TRUST_PROXY` for exactly this. Use the hop count.

**Not setting `trust proxy` at all when there is a proxy.** The mirror-image failure. `req.ip` is the
load balancer for every request, so all users share one rate-limit bucket, `secure` cookies are never
set, and your access logs are useless. `ERR_ERL_UNEXPECTED_X_FORWARDED_FOR`.

**Template literals in `client.query`.** They look identical to the parameterized form at a glance,
because both use backticks in a lot of codebases. The difference is `${}` inside the SQL string.
node-postgres's own docs put it plainly: string concatenation "can (and often does) lead to sql
injection vulnerabilities". Grep for `${` between backticks inside a `query(` call, not for the word
`query`.

**Order of middleware.** A route registered before `app.use(requireAuth)` is not protected by it.
Express runs middleware in registration order, so a route file imported above the auth line is open.
Read the order, not just the presence.

**Slow-loris and unbounded bodies.** Node's HTTP server has generous defaults. `express.json({ limit })`
caps the body; `server.headersTimeout` and `server.requestTimeout` cap the connection. Neither helmet
nor express-rate-limit does this for you.

**One `pg` role for everything.** Most Express apps connect as a single superuser-ish role, which is
why Postgres RLS is usually N/A here. That is a design choice, not a bug, but it means R1 and R2
provide zero defence in depth and every ownership check is application code that a single missing
`and user_id = $2` defeats. Weight R4, R5 and R6 accordingly.

---

## Verified against

Checked 2026-09-06.

- <https://helmet.js.org/> the 13 default headers and their exact values, the default CSP string, Cross-Origin-Embedder-Policy not set by default
- <https://github.com/helmetjs/helmet> the exported middleware names
- <https://github.com/expressjs/csurf> archived and deprecated
- <https://github.com/Psifi-Solutions/csrf-csrf> `doubleCsrf` factory, returned member names, required `getSecret` and `getSessionIdentifier`, default `cookieName` and `getCsrfTokenFromRequest`, v4
- <https://github.com/Psifi-Solutions/csrf-sync> `csrfSync` factory and returned member names
- <https://express-rate-limit.mintlify.app/reference/configuration> `limit` renamed from `max` in v7, MemoryStore reset on restart, option names
- <https://github.com/express-rate-limit/express-rate-limit> the `ERR_ERL_*` codes and their exact descriptions
- <https://expressjs.com/en/guide/behind-proxies.html> `trust proxy` values and the `false` default
- <https://node-postgres.com/features/queries> `$1` placeholders, values array, the injection warning, named prepared statements
- <https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html> referenced for the Argon2id parameters; confirm the current minimums there before applying

Not verified here: the current major version numbers of `helmet`, `csrf-sync` and `express-rate-limit`
(their docs pages do not state one). Read the installed version from `package.json` before writing a
fix that depends on a renamed option, and check `csrf-csrf`'s `UPGRADING.md` if the installed major is
below 4.
