# FAQ

Find what a stranger can take from your app, then close it and prove it closed. One Agent Skill: it
reads your project, runs 65 named control checks, writes a report where every finding carries its
proof (a code line, and with a live URL the request and its output), and stops until you say what
to fix.

## Is it safe to run

Yes. Phases 0 to 4 only read your project: files, greps, and any scanners you already have. The only
thing it writes is the report under `.secure-my-app/`, and it sends no request of its own unless you
hand it a URL and say yes. Your code is never changed without a fix you approved.

## Will it break my app

Not on its own. It does not touch your code until you approve a specific fix, and each fix gets a
checkpoint commit first. If your legitimate request stops working, that fix is reverted and marked
`FIX FAILED, NEEDS HUMAN`.

## Does it send my code anywhere

It makes no network call of its own. The only requests it ever sends are the phase 3 probes, against
the one host you named after you said yes. Your agent still sends context to its own model provider,
as it does for every other task.

## Does it need an API key or an account

No key, no account, no server, no dependency. It is Markdown your agent reads.

## Can it fix things automatically

No, and there is no batch mode. It reports, then stops. Fixing is a separate phase, one finding at a
time, each with its own approval and its own re-proof.

## How is it different from `/security-review`

`/security-review` reads a diff and finds the flaw in the code that is there. secure-my-app reads the
whole app and finds the control nobody wrote at all: the missing policy on `profiles` is in no diff,
because its absence is the shape of what you shipped. Use one on a change, the other before a launch.

## What does it write to disk

Two files under `.secure-my-app/`: `report.md`, ordered by severity, and `surface.json`, the inventory
as data and the reason a second run says "3 fixed, 1 regressed, 1 new". Add it to your `.gitignore`.

## What will it do to my live site

About 30 requests at most, against the one host you named. No `DELETE`, no data-modifying request, no
load testing. Given a production URL and a preview, it uses the preview. A `GET` in your code can
delete a record, so it judges each endpoint by what it does and skips what it cannot read.

## Do I have to give it a URL

No, it runs either way. But without one most of ROOMS comes back `UNPROVEN`, and ROOMS is where the
expensive breaches are. The header then says `static only` so you know what you are holding.

## Will my secrets end up in the report

No. Everything is redacted to the provider prefix plus four characters, everywhere:
`sk_live_51H...  (.env.local:3, commit 4a91c2e)`. It reads env variable *names* freely, reads *values*
only when a control needs one, says so first, and never echoes them.

## What do the three gate labels mean

```
GATE: DO NOT LAUNCH            >= 1 CRITICAL
GATE: LAUNCH WITH KNOWN GAPS   0 CRITICAL, >= 1 HIGH
GATE: NOTHING CONFIRMED HERE   0 CRITICAL, 0 HIGH
```

The third is not "secure" and not "passed". It says only that nothing in this run reached the top two
bands. It is never printed without its coverage on the same line, because a thorough run and a run
that could barely check anything reach the same label:

```
VERDICT: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 15 n/a   [static only]
```

## What does UNPROVEN mean

The check could not be settled either way. It gets no severity and adds nothing to the gate. An empty
grep is not evidence that a control exists, so promoting it to `PASS` is how a report becomes fiction.
Each one records why, plus the command that would settle it.

## Why is there no score out of 100

"We went from 62 to 78" is not a security goal, any weighted sum is gameable by adding passing
controls, and a tool that cannot see your infrastructure cannot measure a percentage of anything.

## It found a leaked key. What now

Rotate first, scrub history second, and almost everyone does this backwards. A secret that was public
for five minutes is compromised forever, and forks, mirrors, CI caches and every local clone keep a
copy, so rewriting history without rotating leaves you a clean looking repo and a working key.

It will not rotate it for you and will not rewrite history, not even inside a "fix everything" yes. It
has no access to your provider console, so it writes the runbook and you run it. `git filter-repo`,
`git rebase` and force pushes are their own conversation with their own confirmation.

## What is the paired test

Every fix is proven twice, in opposite directions.

```
Before   attacker's request succeeds      legitimate user's request succeeds
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

The right column is what most tooling skips. A fix is done only when the attacker's request is refused
AND a legitimate user's still succeeds, because a `403` for everybody closes the hole and the product.

"Fails" means refused, specifically. A timeout, a 500, or an empty result from a fixture row that never
existed all look like failure and prove nothing. A row level security fix needs three reads against
real rows: anonymous gets nothing, user A gets A's row, user B gets nothing of A's.

Note that row level security switched on with no matching policy denies. The absence of a policy is
not evidence of exposure; the exposure is security switched off, or a policy that permits too much.

## Do I need gitleaks or semgrep installed

No. If they are there it uses them and names them in the header; if not it runs the grep fallbacks and
says so. A missing tool never turns a check into a `PASS`, and it never installs one.

## Does it work outside Claude Code

Yes. `npx skills add Aboudjem/secure-my-app -g` puts the same directory wherever your agent reads skills,
and it degrades honestly: no shell means those controls come back `UNPROVEN` with their commands
written out, no network means the header says `static only`. See [editors](editors.md).

## Can I run just one part

Yes. `--group keys` runs KEYS alone, the right call in a hurry, because it is the only group where the
damage may already be done. The rest are `door`, `rooms`, `pipes`, `vault`, `floor`, `supply`, and
`--report-only` never offers to fix.

## Can I use the output as a security assessment

No, and it refuses to be described as one. It is not a penetration test and not a compliance audit.
Hire a person when your app holds payments, health data or other people's credentials, when a customer
or a regulator is asking, or when you think a breach already happened.

## Is it deterministic

The rating is, the scan is not. The same classified finding always lands in the same severity cell, but
discovery is a judgement, so two runs against an unchanged app can differ. `surface.json` exists so the
second run is a diff rather than an assumption.

## What does it not check

Cloud IAM. Network boundaries and firewalls. DNS and subdomain takeover. Physical and device security.
Social engineering. Insider access. Anything behind a login it was not given, or inside a service whose
code you do not have. Race conditions. Crypto implementation. Every report reprints that list, and
[honest limits](limits.md) has the long version.

## More

- [Quickstart](quickstart.md) · [Install in your editor](editors.md) · [The control catalogue](controls.md)
- [Honest limits](limits.md) · [A worked report](../examples/sample-report.md) · [The skill itself](../skills/secure-my-app/SKILL.md)
