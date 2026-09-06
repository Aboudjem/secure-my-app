# Quickstart

A first run, start to finish, on a real-shaped app. The project here is a Next.js and Supabase
booking app at `/Users/you/tidemark`, deployed to Vercel, three months old, mostly written by an
agent. `/Users/you/tidemark` stands in for your project; lockpatch prints your real paths.

Nothing below is fixed until you say so. Phases 0 through 4 read, run commands, and write a report.
Phase 5 is where anything changes, and it asks first, one finding at a time.

## 1. Install

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install lockpatch@10x
```

Any other agent, same skill directory:

```bash
npx skills add Aboudjem/lockpatch
```

## 2. Run it

Type `/lockpatch` in your project, or just say what you want.

```text
/lockpatch
```

"lockpatch this before I launch", "am I going to get hacked", "check my RLS" and "did I leak a key"
all reach the same skill.

## 3. It reads the app, then asks three questions

Phase 0 reads your manifests and the shape of the app: `package.json` and the lockfile,
`next.config.*`, `supabase/`, `middleware.ts`, `git remote -v`, and the *names* of your `.env*` files.
It does not read env values here, and it does not ask permission to read files.

```text
LOCKPATCH   scope

stack     Next.js 15.1 (app router) · Supabase (postgres 15) · Vercel
db        14 tables in public, 3 migrations, 2 with policies
auth      @supabase/ssr, cookie sessions, middleware.ts present
env       .env.local (7 names), .env.example (7 names)   values not read
routes    23 route handlers, 6 with a dynamic id segment
client    9 files calling supabase from a 'use client' tree
repo      github.com/you/tidemark
scanners  gitleaks yes, osv-scanner yes, semgrep no, trufflehog no

Three questions, because these three change what runs and nothing else does.

1. Is this app live and reachable by strangers right now? If yes, what is the URL?
   (Optional. It unlocks executed evidence, which is the difference between a good
   report and a weak one.)
2. Is the repo public, or has it ever been public?
3. Does more than one customer or team share this database?
```

Answer them plainly.

```text
1. yes, https://tidemark-preview.vercel.app  (preview, same code as prod)
2. it was public for about two weeks in June
3. yes, teams share it
```

That second answer matters more than it looks. A repository that was public for two weeks means
every secret that was in it during those two weeks is compromised, and the KEYS group runs
accordingly.

The third answer turns on the tenant isolation checks in ROOMS, which are otherwise `N/A`.

## 4. It maps the surface before judging anything

Phase 1 builds an inventory: every route and handler with its methods, every table with its row level
security state, every client-side database call, every env var referenced from client-reachable code,
every webhook receiver, every upload path, every model call. It writes
`/Users/you/tidemark/.lockpatch/surface.json`.

That file is why your second run can say "3 fixed, 1 regressed, 1 new" instead of starting over.

## 5. It runs the control checks

Group order is fixed: KEYS, DOOR, ROOMS, PIPES, VAULT, FLOOR, SUPPLY. You see progress, not a wall of
detail.

```text
KEYS    8 checked   1 fail  0 unproven  0 n/a
DOOR    9 checked   1 fail  2 unproven  0 n/a
ROOMS  10 checked   2 fail  1 unproven  0 n/a
PIPES  12 checked   1 fail  2 unproven  1 n/a
VAULT   8 checked   1 fail  1 unproven  0 n/a
FLOOR  10 checked   0 fail  2 unproven  3 n/a
SUPPLY  7 checked   1 fail  0 unproven  0 n/a
```

Nothing here is a finding yet. A candidate has to climb four rungs before it may appear as one: it
has to exist at a `file:line`, be reachable by somebody you can name, have nothing stopping it
through the actual calling role, and cost you something you can describe in your own vocabulary. A
candidate that stops short is `UNPROVEN`, and it says why.

## 6. Live probes, only with your yes

You gave a URL, so lockpatch asks once more before touching the network.

```text
Live probes against https://tidemark-preview.vercel.app
  about 24 requests, including redirects. No DELETE. No data-modifying request.
  Only this host. Proceed?
```

You said the production URL exists and a preview exists, so it uses the preview. It also does not
treat the HTTP method as a safety boundary: a `GET` in your codebase can delete a record or send an
email, so it judges each endpoint by what it does, and skips anything it cannot read.

## 7. The report, and then it stops

The gate line comes first, with its coverage on the same line, because the gate alone is misleading.

```text
LOCKPATCH   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
scan: gitleaks yes, osv yes, semgrep no, trufflehog no
findings: 2 critical  3 high  2 medium  0 low

CRITICAL  R1  Anyone can read every row of `bookings`
  where   supabase/migrations/0002_bookings.sql:11   no ENABLE ROW LEVEL SECURITY
  proof   [executed] curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: $ANON"
          -> 200, 1,204 rows, keys: id,user_id,email,phone,address,total_cents
  impact  Every customer's email, phone and home address, to anyone holding your
          publishable key, which is in your page source by design.

CRITICAL  K5  Live Stripe secret key in git history, not rotated
  where   .env.local:4, present at commit 8c31f0a (June 12, repo was public then)
  proof   [executed] gitleaks detect --redact
          -> stripe-access-token  sk_live_51Nq...  .env.local:4  8c31f0a
  impact  Charge cards, issue refunds, read your full customer list. The repo was
          public for two weeks with this key in it.

HIGH  R4  /api/bookings/[id] returns any booking to any signed-in user
HIGH  R5  Team scoping reads workspace_id from the request body
HIGH  D9  The auth wrapper returns a session when getUser() throws

full report  /Users/you/tidemark/.lockpatch/report.md
inventory    /Users/you/tidemark/.lockpatch/surface.json

Stopping here. Say which findings to fix, or "fix the criticals".
```

Then it stops. A report you did not ask to have acted on is a complete delivery, and starting to edit
auth code because editing seems helpful is how a launch night goes wrong.

Open `.lockpatch/report.md` and read it. Every finding is the same six fields plus a status, in the
same order, every time: what, where, proof, impact, fix, verify, status. The
[worked report](../examples/sample-report.md) shows the full shape.

Add `.lockpatch/` to your `.gitignore` unless you specifically want the report in version control.

## 8. Fix one finding, and prove it closed

```text
fix R1
```

Every fix is one loop, and the loop does not start until you approve this specific fix.

```text
R1  Enable row level security on `bookings`, owner-only read

  before I write this, two things to confirm:
    - bookings.user_id IS the auth user id (not a profile id)   confirm?
    - owner-only read is the intent, staff do not need a broad read   confirm?

  no permissive sibling policy exists on this table, so this one will not be
  defeated by an OR. checked with pg_policies.

  checkpoint  git commit -m "checkpoint before lockpatch R1"  (so git reset is the undo)

  alter table public.bookings enable row level security;
  create policy "own bookings" on public.bookings
    for select to authenticated using ((select auth.uid()) = user_id);

  the paired test, both halves:
    anon:    curl the same endpoint            -> []
    user A:  reads A's own booking             -> 200, one row
    user B:  reads A's booking                 -> empty, not an error
    state:   select relrowsecurity from pg_class
               where oid = 'public.bookings'::regclass  -> t

  apply?
```

You say yes. It applies, then re-runs both halves and reads the output.

```text
R1  after

  anon     curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: $ANON"   -> []          PASS
  user A   GET /api/bookings/<A's id> as A                                -> 200, 1 row  PASS
  user B   GET /api/bookings/<A's id> as B                                -> empty       PASS
  build    npm run build                                                  -> ok
  tests    npm test  22/22

  STATUS  FIXED
```

The middle line is the one most tools skip, and it is the reason this is a fix rather than a
regression. A patch that returns `403` to everyone closes the hole and closes the product. Note also
that user B's read used a real fixture row owned by A, because an empty result against an empty table
is a test that could not fail.

If any of those three had come back wrong, that one fix is reverted from the checkpoint, the finding
is marked `FIX FAILED, NEEDS HUMAN` with what was tried, and the run moves on. Fixes are never
stacked.

## 9. The leaked key is not a code fix

K5 does not get a diff. lockpatch never rotates a credential for you, because it does not have your
Stripe console, cannot confirm the new key propagated, and a half-right rotation takes your app down
in the middle of the day. It writes the runbook instead.

```text
CREDENTIAL   Stripe secret key
FOUND        .env.local:4, still present in history at 8c31f0a
OPENS        charge cards, refund, read the full customer list
ROTATE AT    https://dashboard.stripe.com/apikeys  ->  Roll key
ORDER        create the new key, deploy it, THEN revoke the old one
DOWNTIME     none if you deploy before revoking. Revoking first breaks checkout
AFTER        confirm the old key returns 401

STATUS  HANDED OVER
```

**Rotate before you scrub history.** Purging the key from git history without rotating gives you a
repository that looks clean and a key that still works in somebody else's collection. That order is
the single most common mistake in this whole genre, and lockpatch will not run `git filter-repo`,
`git rebase` or a force push on its own initiative, not even inside a "fix everything" yes.

## 10. Run it again

A second run diffs against `surface.json` rather than starting over.

```text
LOCKPATCH   gate: LAUNCH WITH KNOWN GAPS
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
since last run: 2 fixed, 0 regressed, 0 new

HIGH  R4  /api/bookings/[id] returns any booking to any signed-in user   OPEN
HIGH  R5  Team scoping reads workspace_id from the request body          OPEN
HIGH  D9  The auth wrapper returns a session when getUser() throws       OPEN
```

The gate moved from `DO NOT LAUNCH` to `LAUNCH WITH KNOWN GAPS` because the criticals are closed. It
did not move to `NOTHING CONFIRMED HERE`, and even that label would not mean the app is safe. It
would mean that in the 47 controls this run could check, nothing rose to the top two bands, with 8
still unproven.

## What to read next

- [Honest limits](limits.md), what a clean run does not prove. Read this one before you tell anyone
  the app passed
- [The control catalogue](controls.md), all 65 controls in seven groups
- [A worked report](../examples/sample-report.md), the full `.lockpatch/report.md` shape
- [FAQ](faq.md) · [Install in your editor](editors.md) · [The skill itself](../skills/lockpatch/SKILL.md)
