# Quickstart

A first run on a Next.js and Supabase booking app at `/Users/you/tidemark`. Tidemark is made up, so
the output below is an illustration. Yours prints your real paths. To try a real run first, use the
[vulnerable fixture](../examples/vulnerable-app/README.md) that ships in this repo.

Phases 0 to 4 read your code and write a report. Phase 5 is the only one that changes anything,
and it asks first, one finding at a time.

## 1. Install

The Vercel skills CLI, for all your projects. In a terminal it shows the agent menu:

```bash
npx skills add Aboudjem/secure-my-app -g
```

Only this project: drop `-g`. In a script, add `-a <agent>`.

Or as a Claude Code plugin, the same skill:

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install secure-my-app@10x
```

## 2. Run it

Say what you want in plain words. "Secure my app before I launch", "is this safe to launch", "am I
going to get hacked" and "did I leak a key" all reach the same skill.

The short triggers: `/secure-my-app:secure-my-app` in Claude Code, `$secure-my-app` in Codex CLI.

## 3. Answer three questions

It reads the shape of the app first: `package.json`, `next.config.*`, `supabase/`, `middleware.ts`,
`git remote -v`, and the *names* of your `.env*` files, not the values. Then three questions.

```text
1. Is this app live and reachable by strangers? If yes, what is the URL?
   > yes, https://tidemark-preview.vercel.app  (preview, same code as prod)
2. Is the repo public, or has it ever been public?
   > it was public for about two weeks in June
3. Does more than one customer or team share this database?
   > yes, teams share it
```

Question 1 is optional and it decides how strong the report is: without a URL most of ROOMS comes back
`UNPROVEN`, and ROOMS is where the expensive breaches are. Answer 2 means every secret that sat in the
repo those weeks is compromised. Answer 3 turns on the tenant checks.

## 4. It maps the surface, then runs 65 checks

Phase 1 writes `.secure-my-app/surface.json`: every route, every table with its row level security
state, every client-side database call, every webhook, every upload path. That file is why the second
run says "2 fixed, 0 regressed, 1 new" instead of starting over.

Phase 2 runs the controls in fixed order: KEYS, DOOR, ROOMS, PIPES, VAULT, FLOOR, SUPPLY. Nothing is a
finding yet. A candidate clears four rungs first: it exists at a `file:line`, somebody you can name can
reach it, nothing stops them through the real calling role, and it costs you something you can name.
Stop short of a rung and it is `UNPROVEN`, with the reason. Phase 3 asks again before touching the
network: about 30 requests at most, no `DELETE`, that host only.

## 5. Read the verdict

```text
VERDICT: DO NOT LAUNCH   coverage 53 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
findings: 2 critical  3 high  2 medium  0 low   scan: gitleaks yes, osv-scanner yes, semgrep no, trufflehog no
DO FIRST
1. R1  Switch on row level security for bookings, with an owner-only policy
2. K5  Rotate the Stripe secret key in the dashboard, then scrub it from history
3. R4  Add the ownership check to GET /api/bookings/[id]

CRITICAL  R1  Anyone can read every row of `bookings`
  where   supabase/migrations/0002_bookings.sql:11   no ENABLE ROW LEVEL SECURITY
  proof   [executed] curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: $ANON"
          -> 200, 1,204 rows, keys: id,user_id,email,phone,address,total_cents
  impact  Every customer's email, phone and home address, to anyone holding your
          publishable key, which is in your page source by design.

CRITICAL  K5  Live Stripe secret key in git history, not rotated  (.env.local:4, 8c31f0a)
HIGH      R4  /api/bookings/[id] returns any booking to any signed-in user
HIGH      R5  Team scoping reads workspace_id from the request body
HIGH      D9  The auth wrapper returns a session when getUser() throws

full report  /Users/you/tidemark/.secure-my-app/report.md
Stopping here. Say which findings to fix, or "fix the criticals".
```

The first line is the verdict, and the next lines are the three things to do first. You can stop
reading there and still act. The coverage sits on the verdict line because the label alone is
misleading: a thorough run and a run that could barely check anything reach the same label. The third
label is `NOTHING CONFIRMED HERE`, never "secure" and never "passed", and it would mean only that of
the 53 controls this run could check, nothing reached the top two bands, with 8 still unproven.

Then it stops. Open `.secure-my-app/report.md`, where every finding carries the same six fields plus a
status: what, where, proof, impact, fix, verify, status. Add `.secure-my-app/` to your `.gitignore`.

## 6. Fix one finding

Say `fix R1`. Nothing is written until you approve this specific fix.

```text
R1  Enable row level security on `bookings`, owner-only read

  confirm first: bookings.user_id IS the auth user id, not a profile id
  no permissive sibling policy here, so an OR cannot defeat this one
  checkpoint: git commit -m "checkpoint before secure-my-app R1"

  alter table public.bookings enable row level security;
  create policy "own bookings" on public.bookings
    for select to authenticated using ((select auth.uid()) = user_id);

  apply?  > yes

R1  after
  anon     curl the same endpoint                    -> []          PASS
  user A   GET /api/bookings/<A's id> as A           -> 200, 1 row  PASS
  user B   GET /api/bookings/<A's id> as B           -> empty       PASS
  build    npm run build                             -> ok

  STATUS  FIXED
```

The middle line is the one most tools skip. A fix is done only when the attacker's request is refused
AND a legitimate user's still succeeds; a patch that returns `403` to everybody closes the hole and
closes the product. User B read a real row owned by A, because an empty result against an empty table
is a test that could not fail. If either half comes back wrong, that fix is reverted from its
checkpoint, marked `FIX FAILED, NEEDS HUMAN`, and the run moves on. Fixes are never stacked.

## 7. The leaked key gets a runbook, not a diff

secure-my-app never rotates a credential. It has no access to your Stripe console, cannot confirm a new
key propagated, and a half-right rotation takes your app down mid-afternoon. K5 gets this:

```text
CREDENTIAL  Stripe secret key, .env.local:4, still in history at 8c31f0a
ROTATE AT   https://dashboard.stripe.com/apikeys  ->  Roll key
ORDER       create the new key, deploy it, THEN revoke the old one. Revoking
            first breaks checkout; deploying first costs no downtime
AFTER       confirm the old key returns 401          STATUS  HANDED OVER
```

**Rotate before you scrub history.** Purging the key from git without rotating gives you a repository
that looks clean and a key that still works in somebody else's collection. secure-my-app will not run
`git filter-repo`, `git rebase` or a force push on its own, not even inside a "fix everything" yes.

## 8. Run it again

A second run diffs against `surface.json`, so it reports `since last run: 2 fixed, 0 regressed, 0
new`. With both criticals closed the gate moves to `LAUNCH WITH KNOWN GAPS`.

## Next

- [Honest limits](limits.md), what a clean run does not prove. Read it before you tell anyone it passed
- [The control catalogue](controls.md), all 65 controls · [A report from a real run](../examples/sample-report.md)
- [FAQ](faq.md) · [Install in your editor](editors.md)
