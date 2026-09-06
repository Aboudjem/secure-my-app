# FAQ

## What is lockpatch, in one sentence

Find what a stranger can take from your app. Then close it and prove it closed.

It is a Claude Code skill, and an Agent Skill for every other agent that reads them. It reads your
project, runs 65 named control checks, writes a report where every finding carries the command that
demonstrates it, and then stops until you say what to fix.

## How is this different from `/security-review`

Claude Code ships `/security-review`, and it is good at what it does: it reads a diff and finds the
flaw in the code that is there. A missing bounds check, a string concatenated into a query, a
comparison that is not constant time.

lockpatch is looking for something else. It reads the whole app and finds the control that was never
written at all. Nobody forgot to write the row level security policy on `profiles` in a diff you can
review, because the absence of that policy is not in any diff. It is the shape of the thing you
shipped.

Use `/security-review` on the change you just made. Use lockpatch before you launch, and again after
the app has grown past its first few tables. They are complements, and the SKILL.md says so in the
same words.

## Does it write to my code

Not until you say so. Phases 0 through 4 are read only: it reads files, runs greps, and with your
explicit yes and a URL you confirmed you own, makes a bounded number of benign HTTP requests. Then it
writes the report and stops.

Phase 5 is fixing, and it happens one finding at a time. Each fix is proposed with its diff, approved
by you for that fix specifically, applied after a checkpoint commit, and then re-proved in both
directions before it is marked closed. There is no batch mode where you approve everything at once.

## What does it actually write to disk

Two files, both under `.lockpatch/` in your project:

- `.lockpatch/report.md`, the full report ordered by severity
- `.lockpatch/surface.json`, the inventory and the findings as data

`surface.json` is why a second run can tell you "3 fixed, 1 regressed, 1 new" instead of handing you
a fresh wall of text. Add `.lockpatch/` to your `.gitignore` unless you want the report in version
control, which is a reasonable thing to want and an unreasonable thing to do by accident.

## Why is there no score out of 100

Three reasons, and lockpatch will give you all three if you ask it directly.

A number invites "we went from 62 to 78", which is not a security goal. "Can a stranger read my users
table" is. Any weighted sum is gameable by adding passing controls, which is the exact failure it is
supposed to prevent. And a tool that cannot see your infrastructure, your IAM, or your business logic
has no basis for claiming it measured a percentage of anything.

What ships instead is a count and a three-state gate, computed by rule, always printed with its
coverage.

## What do the three gate labels mean

```
GATE: DO NOT LAUNCH            >= 1 CRITICAL
GATE: LAUNCH WITH KNOWN GAPS   0 CRITICAL, >= 1 HIGH
GATE: NOTHING CONFIRMED HERE   0 CRITICAL, 0 HIGH
```

The third one is the important one. It is not "secure" and not "passed". It says that in what this
run could check, nothing rose to CRITICAL or HIGH. MEDIUM and LOW findings are usually listed
underneath it, and so are the unproven checks. Reading it as "my app is safe" is a misreading, which
is why the phrase never gets abbreviated.

## Why is the coverage printed on the same line as the gate

Because the gate alone is the most misleading line the tool can produce. A thoroughly checked app and
a run that could barely check anything reach the same label. So:

```
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

Nine unproven means nine controls this run could not settle either way. Six `n/a` means six controls
whose surface does not exist here, which is a real result rather than a skipped one.

## What does UNPROVEN mean, and why not just guess

`UNPROVEN` means the check could not be settled in this run, in either direction. It gets no severity,
it sits in its own appendix, and it contributes nothing to the gate.

It exists because the alternative is worse. An empty grep is not evidence that a control exists, it is
evidence that the grep did not find one. Promoting that to `PASS` is how a security report turns into
fiction. So lockpatch writes down the exact reason it could not decide, plus the exact command a human
can run to decide it.

A confident wrong finding is the worst thing this skill can produce. It sends somebody to "fix" a
working login at midnight before a launch.

## Do I have to give it a URL

No, and it will run either way. But it is the single biggest difference between a strong report and a
weak one.

Some things only a real request can settle: whether your security headers survive your platform's own
middleware, whether the publishable key really reads that table, whether `/api/orders/1042` returns
somebody else's order. Without a URL, most of the ROOMS group comes back `UNPROVEN`, and ROOMS is
where the expensive breaches are. The report header says `static only` so you know what you are
holding.

## What will it do to my live site

At most about 30 requests including redirects and retries, against the one host you named, after you
confirmed you own it. No `DELETE`. No data-modifying request. No load testing. No brute force beyond
the handful of requests a rate-limit check needs, and that one only with a separate yes.

If you tell it the URL is production and a preview URL exists, it uses the preview.

It also does not treat the HTTP method as a safety boundary, because nothing forces an application to
honour the method's meaning. A `GET` can delete a record, start a job, send an email, or cost you
money. lockpatch judges a request by what that endpoint does in your codebase. If it cannot tell what
an endpoint does, it does not send the request and marks the check `UNPROVEN`.

## Will it leak my secrets into the report

No secret value is ever written into a report, a log, a commit message, or a chat line. Everything is
redacted to the provider prefix plus four characters:

```
found: sk_live_51H...   (Stripe secret key, .env.local:3, commit 4a91c2e)
```

Where a match has to be confirmed, it compares hashes or prefixes. A findings file that quotes secrets
is a second, better organised copy of the leak, and those end up in shared folders.

It reads env variable *names* freely. It reads env *values* only when a control genuinely needs one,
says so before doing it, and never echoes them.

## It found a leaked key. What is the order

Rotate first. Scrub history second. Almost everyone does this backwards.

A secret that was public for five minutes is compromised forever. Bots scrape new commits within
seconds, GitHub keeps unreferenced objects reachable by SHA, and forks, mirrors, CI caches and
everybody's local clone keep their own copies. Rewriting history removes the secret from your branch
and from nowhere else. Doing it without rotating gives you a clean looking repository and a key that
still works.

The full order is in `references/secrets-runbook.md`: find, assess, rotate, replace, scrub, tell
everyone to re-clone, then prevent.

## Will it rotate the key for me

No, and it will not offer to. It does not have your provider console, it cannot confirm the new
credential propagated, and a rotation that goes half right takes your app down. It writes the runbook
with the dashboard URL, the create-then-revoke order, the expected downtime, and how to confirm the
old key now returns 401. You run it.

## Will it rewrite my git history

Never on its own initiative, and never inside a "fix everything" yes. `git filter-repo`,
`git filter-branch`, `git rebase` and force pushes are their own conversation with their own explicit
confirmation, and it comes with the warning that every collaborator has to delete their clone and
clone again.

## What is the paired test

Every fix is proven twice, in opposite directions.

```
Before   attacker's request succeeds      legitimate user's request succeeds
Fix      the control is added
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

The right hand column is the one most security tooling skips. A patch that returns `403` to everybody
closes the hole and closes the product. If lockpatch cannot express the legitimate twin for a
control, it says so and hands the fix to you rather than applying it.

"Fails" means refused, specifically. A timeout, a 500, a gateway error, or an empty result because the
fixture row never existed all look like failure and prove nothing.

## A fix broke my app. What happens

Step 3 of the fix protocol is a checkpoint commit, so `git reset` is the undo. If the attacker's
request still succeeds, if your legitimate request now fails, if the build broke, or if the result is
simply unclear, that one fix is reverted, the finding is marked `FIX FAILED, NEEDS HUMAN` with what
was tried, and the run moves to the next finding.

Fixes are never stacked. A broken fix left in place makes the next fix's verification meaningless.

## Why does it check three things for a row level security fix

Because two of the three are the ones people skip. Any ROOMS verification needs all three:

| As | Reading | Must be |
| --- | --- | --- |
| anonymous | any row | empty |
| user A | A's own row | the row |
| user B | A's row | empty |

Anonymous denial says nothing about what another signed-in user can reach, and the owner still
working is what proves you did not just break the product. All three need real fixture rows, because
an empty result against an empty table is a test that could not fail.

## Is it deterministic

The rating is. The scan is not.

Given a finding already classified on the two axes, the severity is always the same cell, and the
same set of classified findings always produces the same gate. There is no model judgement between
the inputs and the answer.

Choosing those two values is a judgement, and discovery is a judgement, so two runs against an
unchanged app can find different things. `surface.json` exists precisely so a second run can be
diffed against the first rather than assumed to match it.

## Do I need to install any scanners

No. lockpatch has no dependencies. If `gitleaks`, `trufflehog`, `semgrep` or `osv-scanner` happen to
be installed already, it uses them and says so in the report header. If they are not, it runs the
grep fallbacks, says which mode it used, and never lets a missing tool turn a check into a `PASS`.

It will tell you which tool would add what, so you can decide. It will not install one silently.

## Does it work outside Claude Code

Yes. It is one Markdown skill directory, so `npx skills add Aboudjem/lockpatch` puts it in whatever
your agent reads. What changes between harnesses is the tooling underneath, and lockpatch degrades
honestly rather than silently.

An agent with no shell cannot run the DETECT commands, so those controls come back `UNPROVEN` with
the command written out for you. An agent with no network cannot run the live phase, so the report
says `static only` in its header. Both are still useful runs. Neither is allowed to report a `PASS` it
did not earn. See [docs/editors.md](editors.md).

## Can I run just one part of it

Yes. `--group keys` runs the KEYS group alone, which is the right choice if you are in a hurry,
because it is the only group where the damage may already be done and the clock is running. The other
group names are `door`, `rooms`, `pipes`, `vault`, `floor` and `supply`.

`--report-only` never offers to fix, which is what you want in CI or on somebody else's repository.

## Can I use the output as a security assessment

No. lockpatch is not a penetration test and not a compliance audit, and it will refuse to be described
as either. It reads code and makes a bounded number of benign requests. Nobody signs it.

Get a real assessment when your app holds payments, health data, or credentials for other people's
systems, when a customer or a regulator is asking, or when a breach has already happened. That last
one is a human page, not a skill.

## What does it not check

Cloud IAM. Network boundaries and firewalls. DNS and subdomain takeover. Physical and device security.
Social engineering. Insider access. Anything behind a login it was not given. Anything inside a
service your app calls but whose code you do not have. Race conditions and timing attacks. Crypto
implementation review. Whether your team can actually respond when something happens.

Every report reprints that list under "not checked, and why". [Honest limits](limits.md) has the long
version.

## More

- [Quickstart](quickstart.md) · [Install in your editor](editors.md) · [The control catalogue](controls.md)
- [Honest limits](limits.md) · [A worked report](../examples/sample-report.md) · [The skill itself](../skills/lockpatch/SKILL.md)
