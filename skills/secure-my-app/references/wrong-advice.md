# Security advice that used to be right

Load this before writing any fix. Every entry here is something a model is likely to write from
memory because it was correct for years, and is now wrong, deprecated, or harmful.

**Subtraction is part of the job.** If you find one of these already in the codebase, that is a
finding in its own right, usually LOW or MEDIUM, and the fix is removal rather than addition. No
other security checklist does this, and it is the fastest way to earn a user's trust: it proves you
read their code rather than pasting a template.

## Headers

| Do not write | Why | Write instead |
| --- | --- | --- |
| `X-XSS-Protection: 1; mode=block` | The auditor is gone from every current browser, and the filter it enabled introduced its own vulnerabilities. Setting it does nothing at best | Omit it. If a scanner demands the header, `X-XSS-Protection: 0` is the defensible value. Real protection is CSP plus escaping |
| `X-Frame-Options: ALLOW-FROM <uri>` | Never widely supported and dropped | `Content-Security-Policy: frame-ancestors <origin>`. Keep `X-Frame-Options: DENY` alongside it only for very old clients |
| `Feature-Policy` | Renamed | `Permissions-Policy` |
| `Expect-CT` | Obsolete, certificate transparency is enforced by default now | Omit it |
| `Public-Key-Pins` (HPKP) | Removed from browsers. It bricked sites that got it wrong | Never. There is no replacement and none is needed |
| `Strict-Transport-Security` with `preload` on day one | Preload is very hard to reverse and applies to every subdomain, including internal ones that may not have certificates | Ship HSTS with a long max-age first. Confirm every subdomain serves HTTPS. Submit to the preload list months later, deliberately |
| A CSP built entirely from `unsafe-inline` | It permits exactly what CSP exists to stop | Nonces or hashes. A CSP with `unsafe-inline` on `script-src` is a finding, not a pass |

## Passwords and tokens

| Do not write | Why | Write instead |
| --- | --- | --- |
| `SHA-256`, `SHA-1`, or `MD5` for a password, salted or not | Fast digests. A GPU tries billions per second. Salting changes nothing about speed | Argon2id, or bcrypt where Argon2 is unavailable. Check OWASP's current parameter guidance rather than quoting numbers from memory, they move |
| `bcrypt` at the library default cost | Defaults were set years ago and hardware has moved | Raise the cost factor deliberately, and re-check it against current guidance |
| Rolling your own token comparison with `==` | Timing leak | The platform's constant-time compare. In Node, `crypto.timingSafeEqual`. In Python, `hmac.compare_digest` |
| `Math.random()` or `random.random()` for a token, id, or reset code | Not cryptographically random. Predictable | `crypto.randomUUID()`, `crypto.randomBytes`, `secrets.token_urlsafe` |
| `jwt.decode()` as an authorization check | Decode does not verify. It reads a signature it never checks | `jwt.verify()` with an explicit algorithm list |
| `jwt.verify(token, secret)` with no `algorithms` option | Opens algorithm confusion. An attacker signs with `alg: none`, or signs HS256 using your published RS256 public key as the HMAC secret | Pass the algorithm list explicitly, always |

## Node and Express

| Do not write | Why | Write instead |
| --- | --- | --- |
| `csurf` | Deprecated and unmaintained for years | A maintained alternative such as the double-submit or synchroniser-token packages that replaced it, or `SameSite` plus an origin check where that genuinely covers the app's shape. Verify the package is still maintained before you name it |
| `express-rate-limit` with its default in-memory store, in production | The counter lives in one process. Two instances double the allowance, autoscaling removes the limit entirely, and a restart resets it | A shared store (Redis or equivalent). If none exists, say the limiter is per-instance in the report rather than calling the control passed |
| A rate limiter behind a proxy with no `trust proxy` | Every request looks like it came from the proxy, so either everyone shares one bucket or the limiter keys on a header an attacker sets | Configure `trust proxy` to the actual hop count. Getting this wrong in the other direction lets an attacker spoof `X-Forwarded-For` and evade the limit entirely |
| `helmet()` and calling headers done | Helmet does not set a Content-Security-Policy you can rely on for a real app, and does not force HTTPS | Add CSP deliberately, and check the live response with curl rather than trusting the middleware list |
| `cors()` with no options | That is `Access-Control-Allow-Origin: *` | An explicit origin allowlist. Never a wildcard together with credentials, which browsers reject anyway |
| String-interpolating SQL because "the input is a number" | It is a string until something proves otherwise, and the proof usually is not there | Placeholders, every time |

## Supabase and Postgres

| Do not write | Why | Write instead |
| --- | --- | --- |
| "Your anon key is exposed, that is the vulnerability" | The publishable key is meant to be public. It is in the page source by design | The finding is the missing RLS policy, not the key. Report R1 and R2. Reserve the key finding for the service key, K1 |
| `using (true)` on a table with user data | RLS enabled with a permissive policy is RLS disabled with extra steps, and it reads as secure in a dashboard | A predicate on the current user or the tenant column |
| Flagging an `UPDATE` policy for a null `with_check` | Postgres applies the `USING` expression to the new row when `WITH CHECK` is omitted. This is correct code | See the per-command table in `controls.md`. Only `INSERT` genuinely needs its own `with_check` |
| `auth.uid()` bare inside a policy on a large table | It can be re-evaluated per row, which turns a policy into a performance problem and gets policies disabled | Wrap it as `(select auth.uid())` so the planner treats it as a constant. Verify against current Supabase guidance before presenting it as required |
| Assuming correct RLS means the data is safe | A `SECURITY DEFINER` view or function runs as its owner and can hand out every row regardless of policy | Check R9. This is the trap that survives an otherwise perfect RLS audit |

## Next.js

| Do not write | Why | Write instead |
| --- | --- | --- |
| Authorization in middleware as the only gate | Middleware is a routing concern, and a header-based bypass of Next.js middleware was published as CVE-2025-29927. Verify the current framework guidance rather than repeating either the old or the new folklore | Check the session in the handler, the server action, or the data layer, as close to the data as you can get. Middleware is defence in depth, never the boundary |
| Treating a server action as private because it is not a route | Server actions compile to callable HTTP endpoints. Anyone can call one | Check authentication and authorization inside every server action that touches data |
| `NEXT_PUBLIC_` for anything you would not print on a billboard | The prefix inlines the value into the client bundle at build time. That is its entire purpose | Server-only env vars have no prefix. If a secret ever carried the prefix, it is in a shipped bundle and must be rotated |

## Git and secrets

| Do not write | Why | Write instead |
| --- | --- | --- |
| `git filter-branch` | Deprecated, slow, and its own documentation recommends against it | `git filter-repo` |
| Scrub history, then rotate | Backwards. The scrub feels like the fix and is not | Rotate first. See `secrets-runbook.md` |
| "Make the repo private and you are fine" | Every existing clone and fork keeps its copy | Rotate |
| Committing `.env.example` with real values in it | It happens constantly, and it looks intentional so nobody checks | Key names, empty values |

## Dependencies

| Do not write | Why | Write instead |
| --- | --- | --- |
| `npm audit fix --force` as a fix | It takes major version bumps and breaks builds. It is not a security decision, it is a version decision | Read the advisory, check whether the vulnerable path is reachable, upgrade deliberately |
| Treating every advisory as a finding | Most reported advisories are in dev dependencies or in code paths the app never calls. Reporting all of them buries the one that matters | Check reachability first. Downgrade the unreachable ones, and say why |
| A clean offline scan as proof | Offline advisory data is only as current as its last download | Print the data's date next to the result, or do not make the claim |

## How to report one of these when you find it

Same six fields as any finding. The difference is the FIX column says remove:

```
LOW  W1  Obsolete header set: X-XSS-Protection
  where   next.config.js:22
  proof   [static] headers: [{ key: 'X-XSS-Protection', value: '1; mode=block' }]
  impact  None directly. It is dead configuration that reads as protection,
          which is worse than nothing because it stops the next person looking.
  fix     Remove the header. Add a real Content-Security-Policy instead.
  verify  curl -sI $URL | rg -i 'x-xss-protection'  returns nothing
```
