# Supabase and Next.js

The per-stack answer to the FIX column in `controls.md`. Control IDs are the anchors: `R1` here is
`R1` there.

Two moving targets in this stack, and both have bitten people in 2026. Supabase is mid-migration from
`anon` / `service_role` JWTs to `sb_publishable_` / `sb_secret_` keys, and Next.js 16 deprecated
`middleware.ts` and renamed it to `proxy.ts`. Read the fingerprint section and pin the versions before
you write a single line of fix.

---

## How to fingerprint this stack

| Marker | What it proves |
| --- | --- |
| `@supabase/supabase-js` in `package.json` | Supabase client |
| `@supabase/ssr` in `package.json` | Cookie-based Supabase auth on a server framework. `@supabase/auth-helpers-*` is the deprecated predecessor |
| `supabase/config.toml` | Supabase CLI project. `project_id` is in here |
| `supabase/migrations/*.sql` | Schema is version controlled. Grep these for `enable row level security` |
| `next.config.js` / `next.config.mjs` / `next.config.ts` | Next.js |
| `app/` with `layout.tsx` | App Router |
| `pages/` with `_app.tsx` | Pages Router |
| `middleware.ts` at repo root or in `src/` | Next.js 15 or earlier convention |
| `proxy.ts` at repo root or in `src/` | Next.js 16 or later. Same feature, renamed |
| `'use server'` at the top of a file | Server Actions. Every exported function is a public POST endpoint |
| `NEXT_PUBLIC_SUPABASE_URL` in `.env*` | Confirms the pair |

Pin the Next.js version before writing any fix that touches routing or auth:

```bash
node -p "require('./node_modules/next/package.json').version" 2>/dev/null \
  || rg -n '"next"' package.json
```

Anything below `14.2.25`, `15.2.3`, `13.5.9` or `12.3.5` is vulnerable to CVE-2025-29927. See the traps
section.

---

## The exact commands

### Reach the database

The connection string is in the Supabase dashboard under Project Settings, Database. Never paste it
into the report. Export it and refer to `$DB_URL`.

```bash
# every DETECT query in controls.md that needs $DB
psql "$DB_URL" -c "select relname from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity;"

psql "$DB_URL" -c "select tablename, policyname, cmd, qual, with_check, roles
  from pg_policies where schemaname = 'public' order by tablename;"

psql "$DB_URL" -c "select proname from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and p.prosecdef;"
```

If the project is local rather than hosted, `supabase start` prints a connection string for the local
stack and `supabase status` reprints it.

### Run Supabase's own linter

This is the single highest-signal free check in the stack. It runs 29 rules including
`0013_rls_disabled_in_public` and `0010_security_definer_view`.

```bash
supabase link --project-ref <your-project-ref>   # once
supabase db lint --linked --level warning --schema public
```

Flags, verbatim from the CLI reference: `--db-url <string>`, `--fail-on [none|warning|error]`,
`--level [warning|error]`, `--linked`, `--local`, `-s, --schema <strings>`. For CI, add
`--fail-on error`.

If you cannot link, `supabase db lint --db-url "$DB_URL" --level warning` takes the connection string
directly. No connection at all means every lint result is `UNPROVEN`, not `PASS`.

### Hit the REST endpoint the way an attacker does

PostgREST is exposed at `https://<project-ref>.supabase.co/rest/v1/`. The publishable key is public by
design, so this is not a privileged request. It is exactly the request any visitor's browser can make.

```bash
PROJECT_REF=<your-project-ref>
PUBKEY=<sb_publishable_... or the legacy anon JWT>

curl -s -o /dev/null -w '%{http_code}\n' \
  "https://$PROJECT_REF.supabase.co/rest/v1/<your_table>?select=*&limit=1" \
  -H "apikey: $PUBKEY" \
  -H "Authorization: Bearer $PUBKEY"
```

`200` with rows is the R1 or R2 finding. `200` with `[]` is the pass signal for an anonymous read.
Tag this `[executed]` only if you actually ran it against a host the user owns.

### Check the build output for a leaked key

```bash
next build
rg -n 'sb_secret_|service_role' .next/static .next/server/app 2>/dev/null
rg -no 'eyJ[A-Za-z0-9_-]{20,}' .next/static 2>/dev/null | head
```

Any hit in `.next/static` is browser-reachable. Decode the JWT payload and read the `role` claim
before calling it. `anon` is expected. `service_role` is `K1`, CRITICAL.

---

## Fixes by control ID

### K1. The secret key never reaches the browser

Two files, one rule. The secret key lives only in a module that a client component cannot import.

```ts
// lib/supabase/admin.ts
import 'server-only'
import { createClient } from '@supabase/supabase-js'

// SUPABASE_SECRET_KEY has NO NEXT_PUBLIC_ prefix, on purpose.
export const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!,
  { auth: { persistSession: false } }
)
```

`import 'server-only'` is the enforcement, not the comment. It makes the build fail if a
`'use client'` module imports this file. Add the package if it is missing:

```bash
npm i server-only
```

VERIFY: `next build` succeeds, and the `rg` over `.next/static` above returns nothing.

### K2. No secret behind a public prefix

`NEXT_PUBLIC_` is a build-time inline. The value ends up in the JavaScript bundle whatever you name
it. Rename the variable, do not try to hide it.

```diff
- NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY=sb_secret_...
+ SUPABASE_SECRET_KEY=sb_secret_...
```

Then rotate. Renaming an already-shipped variable does not un-ship it. See `secrets-runbook.md`.

### K6. The client key is the publishable key

```ts
// lib/supabase/client.ts
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  )
}
```

Supabase's own naming, quoted: publishable keys carry the `sb_publishable_` prefix and are
"Safe to expose online: web page, mobile or desktop app, GitHub actions, CLIs, source code." Secret
keys carry `sb_secret_` and "provide full access to your project's data, bypassing Row Level
Security."

### D1. The auth check is server-side

Supabase now documents `getClaims()` as the server-side identity check. It verifies the JWT signature,
locally against the cached JWKS when the project uses asymmetric signing keys, which is the default
for projects created after 1 May 2025.

```ts
// lib/supabase/server.ts
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()   // await required on Next.js 15+; synchronous on 14
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // called from a Server Component; the proxy/middleware refreshes the session instead
          }
        },
      },
    }
  )
}
```

Then gate the route:

```ts
// app/api/<your-route>/route.ts
import { createClient } from '@/lib/supabase/server'

export async function GET() {
  const supabase = await createClient()
  const { data, error } = await supabase.auth.getClaims()
  const userId = data?.claims?.sub
  if (error || !userId) return new Response(null, { status: 401 })

  // ... query scoped to userId
}
```

`getAll` / `setAll` is the current cookie interface. The older `get` / `set` / `remove` triple still
compiles on some versions but is not what the docs show; do not write new code with it.

Supabase's warning, verbatim: "Always use `supabase.auth.getClaims()` to protect pages and user data.
*Never* trust `supabase.auth.getSession()`" in server code. `getSession()` reads the cookie without
verifying it.

If the project predates asymmetric keys and still uses a shared HS256 secret, `getClaims()` falls back
to a network call, same as `getUser()`. Either is a valid server-side check. `getSession()` is not.

### R1. RLS on for every table holding user data

```sql
alter table public.<your_table> enable row level security;
```

Run this for every row the `pg_class` query returned. Enabling RLS with no policy denies everything to
`anon` and `authenticated`, which breaks the app. Ship R1 and R2 in the same migration.

### R2 and R3. Policies that actually restrict

Write one policy per command. A single `for all` policy is harder to reason about and is where the
write half gets forgotten.

```sql
-- substitute: public.<your_table>, <owner_column>
create policy "read own rows"
on public.<your_table> for select
to authenticated
using ( (select auth.uid()) = <owner_column> );

create policy "insert own rows"
on public.<your_table> for insert
to authenticated
with check ( (select auth.uid()) = <owner_column> );

create policy "update own rows"
on public.<your_table> for update
to authenticated
using ( (select auth.uid()) = <owner_column> )
with check ( (select auth.uid()) = <owner_column> );

create policy "delete own rows"
on public.<your_table> for delete
to authenticated
using ( (select auth.uid()) = <owner_column> );
```

Two details that are not cosmetic:

- `(select auth.uid())` rather than bare `auth.uid()`. Supabase's own wording: "Wrapping the function
  causes an `initPlan` to be run by the Postgres optimizer, which allows it to 'cache' the results
  per-statement, rather than calling the function on each row." On a large table the unwrapped form
  turns a policy into a per-row function call and the query stops using the index. This is a
  performance fix, not a security fix, but it is the form Supabase documents and the form
  `auth_rls_initplan` lints for.
- `to authenticated`. Supabase: "Always name the role a policy applies to, using the `to` clause" so
  the policy is not evaluated for anonymous requests at all.

Before writing any R3 finding, re-read the per-command table in `controls.md`. A null `with_check` on
an `UPDATE` policy is not a bug.

### R5. Multi-tenant scoping

The tenant comes from the database, never from the request body.

```sql
-- substitute: public.<your_table>, org_id, public.memberships
create policy "read rows in my orgs"
on public.<your_table> for select
to authenticated
using (
  org_id in (
    select m.org_id from public.memberships m
    where m.user_id = (select auth.uid())
  )
);
```

If `memberships` itself has RLS on, a policy on `memberships` that queries `memberships` recurses.
The documented way out is a `security definer` helper, and it is safe only because the helper's body
takes no caller-supplied argument and derives everything from `auth.uid()`:

```sql
create or replace function public.my_org_ids()
returns setof uuid
language sql
security definer
stable
set search_path = ''
as $$
  select m.org_id from public.memberships m
  where m.user_id = (select auth.uid());
$$;

revoke execute on function public.my_org_ids() from public;
grant execute on function public.my_org_ids() to authenticated;
```

`set search_path = ''` is not optional on a `security definer` function. Without it the function
resolves unqualified names against the caller's `search_path`, which the caller controls.

### R7. Privileged columns enforced by the database

A UI that hides the field is not a control. Stop the write in the policy.

```sql
-- substitute: public.profiles, is_admin, plan
create policy "update own profile, not privileges"
on public.profiles for update
to authenticated
using ( (select auth.uid()) = id )
with check (
  (select auth.uid()) = id
  and is_admin = (select p.is_admin from public.profiles p where p.id = profiles.id)
  and plan     = (select p.plan     from public.profiles p where p.id = profiles.id)
);
```

VERIFY: signed in as the row owner, `PATCH` with `{"is_admin": true}` is rejected, and a `PATCH`
changing only `full_name` still returns 200. Read the row back to confirm.

### R8. Storage

```sql
-- private bucket, each user confined to a folder named after their uid
create policy "upload to own folder"
on storage.objects for insert
to authenticated
with check (
  bucket_id = '<your_bucket_id>'
  and (storage.foldername(name))[1] = (select auth.jwt() ->> 'sub')
);

create policy "read own folder"
on storage.objects for select
to authenticated
using (
  bucket_id = '<your_bucket_id>'
  and (storage.foldername(name))[1] = (select auth.jwt() ->> 'sub')
);
```

DETECT which buckets are public:

```bash
psql "$DB_URL" -c "select id, name, public from storage.buckets;"
```

A `public = true` bucket serves every object to anyone who can guess the path. That is correct for a
logo and wrong for an invoice.

### R9. Views and functions that bypass RLS

Postgres creates a view as the creating role. On Supabase that is `postgres`, which has `BYPASSRLS`.
So a view over an RLS-protected table returns every row over the REST API even though your policies
are perfect. This is the trap that a table-by-table RLS audit cannot see.

```sql
alter view public.<your_view> set (security_invoker = on);
```

or at creation, which is what the splinter lint prints:

```sql
create view public.order_items
    with (security_invoker=on)
    as select
        id,
        ...
    from
        app.order_items;
```

`security_invoker` needs Postgres 15 or later. Every current Supabase project qualifies; check
`select version();` if the project is old.

VERIFY: `supabase db lint --linked` no longer reports `0010_security_definer_view`, and the anonymous
`curl` against `/rest/v1/<your_view>` returns `[]`.

### P2 and R6. Validate and allowlist at the boundary

A Server Action is a public POST endpoint. Its TypeScript signature is erased at runtime.

```ts
// app/actions/update-profile.ts
'use server'

import { z } from 'zod'
import { createClient } from '@/lib/supabase/server'

const UpdateProfile = z.object({
  full_name: z.string().min(1).max(120),
  website: z.string().url().optional(),
})
// role, is_admin, plan and credits are absent from this schema on purpose.

export async function updateProfile(formData: FormData) {
  const supabase = await createClient()
  const { data: claims } = await supabase.auth.getClaims()
  const userId = claims?.claims?.sub
  if (!userId) throw new Error('unauthorized')

  const parsed = UpdateProfile.safeParse(Object.fromEntries(formData))
  if (!parsed.success) return { errors: parsed.error.flatten().fieldErrors }

  const { error } = await supabase
    .from('profiles')
    .update(parsed.data)          // named fields only, never the raw body
    .eq('id', userId)             // ownership, not just RLS
  if (error) throw new Error('update failed')
}
```

`.update(parsed.data)` plus a schema that omits privileged fields is the R6 fix. `.eq('id', userId)`
is the R4 fix. Keep both even with RLS on; they are independent layers and the second one survives a
policy edit.

### V2. Return only the fields you need

```diff
- const { data } = await supabase.from('profiles').select('*')
+ const { data } = await supabase.from('profiles').select('id, full_name, avatar_url')
```

`select('*')` over a table that also holds `stripe_customer_id` or `phone` ships those to the browser
even when RLS correctly limits the rows.

### P9. Security headers

```js
// next.config.js
const securityHeaders = [
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
]

module.exports = {
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }]
  },
}
```

Do not add `preload` to the HSTS value on day one. See `wrong-advice.md`. Do not add
`X-XSS-Protection: 1; mode=block`; that header is deprecated and can introduce vulnerabilities.

For CSP, `frame-ancestors` supersedes `X-Frame-Options` in modern browsers. Next.js documents a
nonce-based CSP separately at `/docs/app/guides/content-security-policy`; a static CSP in
`next.config.js` will fight Next's inline scripts unless you go nonce-based, so treat CSP as its own
finding rather than bolting a broken one on.

### P8. Stripe webhooks

The raw body matters. A parsed JSON body cannot be verified.

```ts
// app/api/webhooks/stripe/route.ts
import Stripe from 'stripe'
import { headers } from 'next/headers'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: Request) {
  const body = await req.text()                       // raw bytes, not req.json()
  const sig = (await headers()).get('stripe-signature')
  if (!sig) return new Response('missing signature', { status: 400 })

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch {
    return new Response('invalid signature', { status: 400 })
  }

  // idempotency: store event.id and return 200 early if you have seen it
  return new Response(null, { status: 200 })
}
```

Never hand-roll the HMAC and never compare with `==`. `constructEvent` does a constant-time compare
and enforces the timestamp tolerance that stops replay.

---

## The traps specific to this stack

**The publishable key in your bundle is not the bug.** It is meant to be there. Supabase's protection
model is RLS, not key secrecy. If you write a finding that says "your Supabase key is exposed in page
source", you have written a false positive and burned the user's trust for every real finding in the
report. The finding is "table X is readable with the publishable key", and its proof is the `curl`
above returning rows.

**A `SECURITY DEFINER` view defeats correct RLS.** Every table has RLS on, every policy is right, and
a view over those tables returns the whole database over the REST API. Views default to the creator's
privileges, and on Supabase the creator is `postgres`, which bypasses RLS. Nothing in a per-table
audit finds this. `supabase db lint` does, as `0010_security_definer_view`. Run the linter.

**Both key naming schemes are live.** `sb_publishable_` / `sb_secret_` and the legacy `anon` /
`service_role` JWTs both work today. Grep for both. Never describe the `anon` key as "the insecure
one". Do note the one real upgrade in the new scheme: a secret key used from a browser returns HTTP
401, because Supabase matches on the `User-Agent` header. That is a guardrail, not a control. Supabase
says so itself: "The browser block returns HTTP 401 Unauthorized, but an attacker can still use the
key from other tools." A leaked `sb_secret_` key is still CRITICAL.

**Middleware is not an auth boundary, and CVE-2025-29927 is the proof.** Sending the internal
`x-middleware-subrequest` header made Next.js skip middleware entirely, bypassing any auth check that
lived only there. Patched in `12.3.5`, `13.5.9`, `14.2.25` and `15.2.3`. The upgrade is necessary and
not sufficient. The durable guidance is Next.js's own: proxy/middleware does optimistic redirects, and
the real check lives in the Data Access Layer, next to the query. Next.js states it directly for
Server Functions: "A matcher change or a refactor that moves a Server Function to a different route
can silently remove Proxy coverage. Always verify authentication and authorization inside each Server
Function rather than relying on Proxy alone."

**In Next.js 16 the file is `proxy.ts`, not `middleware.ts`.** The docs say: "the `middleware` file
convention is deprecated and has been renamed to `proxy`." The exported function is renamed too. The
codemod is `npx @next/codemod@canary middleware-to-proxy .`. If you are writing a fix for a Next.js 16
project and you create `middleware.ts`, it may not run at all. Check the installed version first.
Proxy also defaults to the Node.js runtime as of v16.0.0.

**Every `'use server'` export is a public HTTP POST endpoint.** Next.js: "The `\"use server\"`
annotation exposes an end point that makes all exported functions invokable by the client... As long
as a user gets the handle to the id of an action, it can invoke it with any arguments." Zod is not
authorization. A well-formed payload can still name a row the caller does not own. Every action needs
its own identity check and its own ownership filter, at the top, before anything else.

**Server Actions get CSRF protection; Route Handlers do not.** Next.js compares the `Origin` header to
`Host` (or `X-Forwarded-Host`) on Server Actions and rejects a mismatch, and actions are POST-only.
Do not bolt a CSRF token library onto Server Actions. Do check `route.ts` handlers yourself: "When
Custom Route Handlers (`route.tsx`) are used instead, extra auditing can be necessary since CSRF
protection has to be done manually there."

**`.bind()` arguments on a Server Action are not encrypted.** Closed-over variables in a Server Action
closure are encrypted with the action ID before being sent to the client. Arguments passed via
`.bind(null, x)` are not. Next.js says so in capitals: "These are NOT encrypted." Do not bind a
secret, an internal id you were relying on being opaque, or a price.

**A `createClient` that takes the secret key, in a file a client component can import.** This is K1
and it is the single most expensive mistake in this stack. The tell is a file under `lib/` or
`utils/` with no `import 'server-only'` at the top, exporting a client built from
`SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_SECRET_KEY`, imported by a component that also has
`'use client'` somewhere in its tree. Trace the import graph, do not trust the directory name.

**`getSession()` on the server reads an unverified cookie.** It is the right call when you need the
raw tokens. It is the wrong call for an authorization decision. `getClaims()` verifies the signature.

**Caching a personalised page.** `Cache-Control: public` on a route that renders per-user data lets
the CDN serve one user's page to the next visitor. When the Supabase proxy/middleware writes refreshed
auth cookies it also supplies cache headers that must be applied to the response; dropping them is how
sessions end up cached at the edge.

---

## Verified against

Checked 2026-09-06.

- <https://supabase.com/docs/guides/api/api-keys> key prefixes, browser 401 guardrail
- <https://supabase.com/docs/guides/database/postgres/row-level-security> policy SQL, `(select auth.uid())` initPlan wording, `to authenticated`
- <https://supabase.github.io/splinter/0010_security_definer_view/> `security_invoker=on` remediation SQL
- <https://supabase.com/docs/reference/cli/supabase-db-lint> flags and levels
- <https://supabase.com/docs/guides/auth/server-side/creating-a-client> `createBrowserClient` / `createServerClient`, `getAll`/`setAll`, `getClaims()` warning
- <https://supabase.com/docs/reference/javascript/auth-getclaims> JWKS verification
- <https://supabase.com/docs/guides/storage/security/access-control> `storage.foldername(name)` policy
- <https://nextjs.org/docs/app/api-reference/file-conventions/proxy> middleware to proxy rename, v16.0.0, codemod, Server Function warning
- <https://nextjs.org/docs/app/guides/authentication> DAL, `verifySession`, Server Action and Route Handler checks
- <https://nextjs.org/blog/security-nextjs-server-components-actions> `'use server'` endpoints, Origin vs Host CSRF, `.bind()` not encrypted, `server-only`
- <https://nextjs.org/docs/app/api-reference/config/next-config-js/headers> `async headers()` shape, header values
- <https://vercel.com/blog/postmortem-on-next-js-middleware-bypass> CVE-2025-29927 header name and patched versions
- <https://docs.stripe.com/webhooks> referenced for `constructEvent`; confirm the current SDK signature against it before applying

Not verified here: the exact `data.claims` field layout returned by `getClaims()` beyond `sub`. The
reference page does not enumerate it. If a fix needs a claim other than `sub`, print the object once
in a scratch route and read it, or check
<https://supabase.com/docs/reference/javascript/auth-getclaims> before applying.
