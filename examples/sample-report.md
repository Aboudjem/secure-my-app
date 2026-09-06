# lockpatch report

An illustrative `.lockpatch/report.md` in the shape lockpatch produces. The app is fictional:
**Tidemark**, a Next.js 15 and Supabase booking app, three months old, mostly agent-written, with a
preview deployment on Vercel and one shared database across customer teams. Every value below is
invented. The structure, the field order, the redaction convention and the honesty rules are real.

---

```
LOCKPATCH   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
scan: gitleaks yes, osv-scanner yes, semgrep no, trufflehog no
findings: 2 critical  1 high  1 medium  0 low        run 2026-09-06T14:22Z
```

**Read the gate line as one sentence.** `DO NOT LAUNCH` means at least one CRITICAL is open. The
coverage half says what this run could and could not settle: 8 controls came back `UNPROVEN` and are
listed in the appendix, and 4 were `N/A` because the surface does not exist in this app. `semgrep`
and `trufflehog` were not installed, so the code-pattern and key-liveness checks ran in degraded
mode, and the affected controls say so in their own PROOF lines.

Findings are ordered by severity, then by reachability, then by group. Within a band, the smallest
fix comes first.

---

## CRITICAL  R1  Anyone can read every row of `bookings`

```
WHAT     Row level security is switched off on public.bookings, so the publishable
         key reads the whole table with no session.
WHERE    supabase/migrations/0002_bookings.sql:11
PROOF    [static]   supabase/migrations/0002_bookings.sql:11
                    create table public.bookings (...);
                    -- no `alter table ... enable row level security` in any migration

         [executed] psql "$DB" -c "select relrowsecurity from pg_class
                      where oid = 'public.bookings'::regclass"
                    -> f

         [executed] curl -s "$URL/rest/v1/bookings?select=*&limit=3" \
                      -H "apikey: sb_publishable_7f2a..."
                    -> 200, 1204 rows
                    keys: id, user_id, email, phone, address_line1, postcode,
                          total_cents, stripe_payment_intent
                    role tested: anon (no Authorization header sent)

IMPACT   Every customer's email address, phone number and home address, plus what
         they paid, to anyone at all. The publishable key is in your page source by
         design, so "anyone" means anyone who opens devtools on tidemark.app.
FIX      -- confirm two things before running this:
         --   1. bookings.user_id IS the auth user id, not a profile id
         --   2. owner-only read is the intent; staff have their own service path
         -- pg_policies shows no existing policy on this table, so nothing
         -- permissive will OR with the one below and defeat it.

         alter table public.bookings enable row level security;

         create policy "own bookings" on public.bookings
           for select to authenticated
           using ((select auth.uid()) = user_id);

VERIFY   anon:    curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: $ANON"
                  must return []
         user A:  GET /api/bookings/<A's booking id> as A   -> 200, one row
         user B:  GET /api/bookings/<A's booking id> as B   -> empty, not an error
         state:   select relrowsecurity from pg_class
                    where oid = 'public.bookings'::regclass  -> t

         All three, with a real fixture row owned by A. An empty result against an
         empty table is a test that could not fail.
STATUS   FIXED
```

**After, as run:**

```
anon     curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: sb_publishable_7f2a..."
         -> 200, []                                                          PASS
user A   GET /api/bookings/b_39fd21 as user A (fixture row, owner)
         -> 200, {"id":"b_39fd21", ...}                                      PASS
user B   GET /api/bookings/b_39fd21 as user B (different team)
         -> 200, []   (empty, not 500, record confirmed present)             PASS
state    select relrowsecurity from pg_class where oid='public.bookings'::regclass
         -> t                                                                PASS
build    npm run build     -> compiled successfully
tests    npm test          -> 22 passed, 0 failed
```

Applied after a checkpoint commit at `4b8e1c0`. Both halves of the paired test were re-run and read,
not inferred from the diff.

---

## CRITICAL  K5  Live Stripe secret key in git history, never rotated

```
WHAT     A Stripe secret key was committed to a repository that was public for two
         weeks, and it has not been rotated since.
WHERE    .env.local:4, present in history at commit 8c31f0a (2026-06-12)
PROOF    [executed] gitleaks detect --redact
                    -> stripe-access-token
                       secret:   sk_live_51Nq...
                       file:     .env.local
                       line:     4
                       commit:   8c31f0a
                       author:   (redacted)
                       date:     2026-06-12

         [executed] git log --oneline 8c31f0a -1
                    -> 8c31f0a  wire up checkout

         [static]   user confirmed in phase 0: the repository was public from
                    2026-06-08 to 2026-06-23

         liveness NOT confirmed here. trufflehog is not installed, so nothing in
         this run asked Stripe whether the key still works. Treated as live,
         which is the only safe default for a key that sat in a public repo.

IMPACT   Charge cards, issue refunds, and read your entire customer list, from
         anywhere, by anyone who cloned or scraped the repository during those two
         weeks. Bots scrape new public commits within seconds.
FIX      Not a code change. lockpatch does not rotate credentials: it does not have
         your Stripe console, cannot confirm the new key propagated, and a
         half-completed rotation takes checkout down mid-day.

         CREDENTIAL   Stripe secret key
         FOUND        .env.local:4, still present in history at 8c31f0a
         OPENS        charge cards, refund, read the full customer list
         ROTATE AT    https://dashboard.stripe.com/apikeys  ->  Roll key
         ORDER        create the new key, deploy it, THEN revoke the old one
         DOWNTIME     none in that order. Revoking first breaks checkout
         AFTER        confirm the old key returns 401

         Rotate before you scrub history. Removing the key from git history without
         rotating gives you a repository that looks clean and a key that still
         works in somebody else's collection. Forks, mirrors, CI caches and every
         local clone keep their own copy, and you cannot reach those.

         History rewriting is a separate conversation with its own explicit yes,
         and every collaborator has to delete their clone and clone again.
VERIFY   The old key returns 401 from Stripe.
         gitleaks detect --redact  finds nothing at the new value.
         .env is gitignored: git check-ignore .env  exits 0
STATUS   HANDED OVER
```

---

## HIGH  R4  Any signed-in user can read any booking by id

```
WHAT     GET /api/bookings/[id] looks the row up by id alone, with no check that the
         row belongs to the caller.
WHERE    app/api/bookings/[id]/route.ts:14
PROOF    [static]   app/api/bookings/[id]/route.ts:11-18
                    const { data } = await supabase
                      .from("bookings")
                      .select("*")
                      .eq("id", params.id)     <- no .eq("user_id", user.id)
                      .single();

         [executed] as user B, against a fixture booking owned by user A:
                    curl -s "$URL/api/bookings/b_39fd21" \
                      -H "Cookie: sb-access-token=eyJhbGciOi..."
                    -> 200
                       {"id":"b_39fd21","email":"a-user@example.com",
                        "phone":"+44...","total_cents":18400}
                    role tested: authenticated, user B, team_2

IMPACT   Any account, including one somebody creates for free in ten seconds, reads
         any other customer's booking: their email, phone, address and what they
         paid. Booking ids are sequential-looking, so enumeration is trivial.
FIX      // app/api/bookings/[id]/route.ts
         const { data: { user } } = await supabase.auth.getUser();
         if (!user) return NextResponse.json({}, { status: 401 });

         const { data } = await supabase
           .from("bookings")
           .select("id, starts_at, total_cents, status")
           .eq("id", params.id)
           .eq("user_id", user.id)        // the ownership check
           .maybeSingle();

         if (!data) return NextResponse.json({}, { status: 404 });

         The narrowed select is deliberate: this route was returning the whole row,
         which is a separate V2 problem. 404 rather than 403 avoids confirming that
         somebody else's booking id exists.
VERIFY   attacker:    GET /api/bookings/b_39fd21 as user B  -> 404
         legitimate:  GET /api/bookings/b_39fd21 as user A  -> 200, one row
         and the row is still present in the table throughout, so the 404 is a
         refusal rather than a missing record.

         Repeat for all 6 dynamic id routes in surface.json. The two-account test
         belongs in your own test suite so it keeps running after lockpatch is gone.
STATUS   OPEN
```

---

## MEDIUM  V3  Stack traces reach the browser on 500

```
WHAT     Unhandled errors are serialised into the response body, including file
         paths and the failing SQL.
WHERE    app/api/_lib/handler.ts:32
PROOF    [static]   app/api/_lib/handler.ts:30-34
                    } catch (err) {
                      return NextResponse.json({ error: String(err),
                                                 stack: err.stack }, {status:500});
                    }

         [executed] curl -s "$URL/api/bookings/not-a-uuid"
                    -> 500
                       {"error":"invalid input syntax for type uuid: \"not-a-uuid\"",
                        "stack":"at Object.query (/var/task/node_modules/pg/lib/
                         client.js:526:...)  at bookingsHandler (/var/task/.next/
                         server/app/api/bookings/[id]/route.js:88:...)"}

IMPACT   Structure, not data. An attacker learns your database engine, your
         directory layout, your dependency versions and your column types, which is
         what they use to aim the next attempt. No customer record is exposed by
         this finding on its own.
FIX      } catch (err) {
           logger.error({ err, route: "bookings/[id]" });   // server side only
           return NextResponse.json({ error: "Internal error" }, { status: 500 });
         }

         Keep the detail, move it to your log. The failure here is the response
         body, not the logging.
VERIFY   curl -s "$URL/api/bookings/not-a-uuid"
           -> 500, body is exactly {"error":"Internal error"}
           no file path, no SQL fragment, no dependency name in the body
         and the same request still appears in your server logs with the detail.
STATUS   DECLINED
```

You declined this one for now, on the grounds that the preview deployment is the only place it
reproduces and production already runs with `NEXT_PUBLIC_DEBUG` off. That is your call to make. The
finding stays open in `surface.json` and will appear again on the next run rather than being
forgotten.

---

## Unproven

Eight checks could not be settled in this run, in either direction. None of them has a severity, none
of them counts toward the gate, and none of them is a pass. Each carries the reason and the command
that would settle it.

| ID | Control | Why it could not be settled | Run this to settle it |
| --- | --- | --- | --- |
| D3 | Password hashing | Auth is delegated to Supabase, and the `users` table is in the `auth` schema, which this connection cannot read | `psql "$DB" -c "select encrypted_password from auth.users limit 1"` as the postgres role, and confirm a `$2a$` prefix |
| D6 | Login rate limiting | A rate-limit probe needs 12 rapid POSTs to your login route. That is a separate yes and you did not give one | With your permission and against the preview host: 12 POSTs to `/auth/v1/token`, expect a 429 before the twelfth |
| D8 | MFA cannot be skipped | No MFA enrolment path exists in the code, but the Supabase project may have MFA enabled at the dashboard, which this run cannot see | Check Authentication > MFA in the Supabase dashboard, then confirm a half-authenticated session is refused by a protected route |
| P1 | Query parameterisation | `semgrep` is not installed, and the grep fallback found 3 template literals inside SQL strings that could not be traced to request data by reading alone | `semgrep --config p/owasp-top-ten` , or trace `lib/reports.ts:44,71,96` by hand |
| P9 | Security headers | Vercel's edge added `x-frame-options` on the preview host but the production host was not probed, and platform middleware differs between them | `curl -sI https://tidemark.app` and read the same five headers |
| V1 | Column encryption | Cannot tell whether `payment_method_last4` is a Stripe token or a stored value from the schema alone | `psql "$DB" -c "select payment_method_last4 from bookings limit 1"` and look at the shape |
| F6 | Prompt injection boundary | The support-assistant route calls a model with ticket text, but the tool list is built at runtime from a config this run could not resolve | Read `lib/assistant/tools.ts` with the runtime config present, then send a canary injection string through a ticket |
| S1 | Dependency advisories | `osv-scanner` ran with `--offline`. Its advisory data was last downloaded 2026-08-11, which is 26 days before this run | `osv-scanner --lockfile=package-lock.json` online, and re-read the result |

Four controls came back `N/A` because the surface does not exist in this app: **F3** no file upload,
**F5** no coupon or multi-step order state, **P11** no GraphQL endpoint, **V7** no deletion request
path.

---

## Not checked, and why

None of the following is inside what lockpatch can see. This list is printed on every run, including
runs with no findings at all, because a clean report that omits it invites exactly the wrong
conclusion.

- **Cloud IAM**, role trust policies, and anything in your Vercel or Supabase console
- **Network boundaries**, security groups, firewalls, and private networking
- **DNS and your registrar**, including subdomain takeover on anything pointing at a service you no
  longer own
- **Physical and device security**, your laptops, and your browser extensions
- **Social engineering** and support-desk takeover, which is how a lot of real breaches start
- **Insider access**, and everyone who legitimately holds admin today
- **Anything behind a login you did not give this run**, which here means the whole authenticated
  admin area at `/admin`
- **Anything inside Stripe, Resend, or Sentry**, whose code this run cannot read
- **Race conditions and timing attacks**, which need a running system under load
- **Cryptographic implementation review**
- **Whether your team can actually respond** when something happens

---

## What this report is not

It is not a penetration test. This run read code and made 24 benign HTTP requests against one host
you named and confirmed you own. It did not chain exploits, pivot, or test infrastructure.

It is not a compliance audit. SOC 2, PCI DSS and GDPR are programmes with auditors and human sign
off. Nobody signs this.

It is not a statement that closing these four findings makes Tidemark secure. It means you closed
what this run found, in the 47 controls it could check, with 8 still unproven. The next gap is the
one nobody wrote a check for yet.

Given that this app takes card payments and holds customer addresses, get a real assessment before
you scale it.

---

```
next run: lockpatch diffs against .lockpatch/surface.json and reports
          "n fixed, n regressed, n new" rather than starting over.
```
