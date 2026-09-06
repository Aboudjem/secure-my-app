# Honest limits

This page exists because lockpatch is a security tool, and the worst thing a security tool can do is
leave you feeling safer than you are. Everything below is a thing lockpatch does not do, cannot see,
or cannot promise. None of it is hidden in a footnote inside the product: the report carries a short
version of this list every time it runs.

If you read only one line: **a clean lockpatch run is not evidence that your app is secure.** It is
evidence that in the part of your app this run could actually check, nothing rose to CRITICAL or
HIGH. Those are different claims, and the distance between them is where people get hurt.

## The gate is not a verdict

lockpatch ends on one of exactly three gate lines.

```
GATE: DO NOT LAUNCH            >= 1 CRITICAL
GATE: LAUNCH WITH KNOWN GAPS   0 CRITICAL, >= 1 HIGH
GATE: NOTHING CONFIRMED HERE   0 CRITICAL, 0 HIGH
```

The third label is deliberately awkward. It is not "secure", not "passed", not "clean", not even "no
exposure found". It says what happened and nothing more: nothing in this run rose to the top two
bands. MEDIUM and LOW findings are routinely listed underneath it. Unproven checks are routinely
listed underneath it. A user who reads that line as "my app is safe" has been misled by it, which is
why the phrase is never abbreviated, not in the report and not in conversation.

None of the three labels is permission to launch. They summarise what was found. The release
decision belongs to the person who knows what the app is for and what it holds.

## The gate never ships without its coverage

A run that checked everything and a run that could barely check anything can reach the same label.
That is the single most dangerous property of any pass or fail summary, so the coverage counts are
printed on the same line, always:

```
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

Read it as one sentence. Nine unproven checks means nine controls this run could not settle in either
direction. Six `n/a` means six controls whose surface does not exist in your app, which is a real
result and not a skipped one. `static only` means no live request was ever made, which makes the
whole document weaker than one carrying executed evidence.

## Evidence has tiers, and the weak ones cannot close anything

| Tier | Tag | What it means | Can it support a PASS |
| --- | --- | --- | --- |
| 1 | `static` | Read in the repo. A file, a line, a config value, a migration | Sometimes, for config that is itself the control |
| 2 | `executed` | A command was run here and this is its real output | Yes |
| 3 | `recipe` | A command written out for you to run. Nobody ran it | Never |

A tier 3 recipe cannot support a `PASS` and cannot close a finding. If a whole run comes back tier 1
and tier 3, the report says so in its first line, because that report is a much weaker document than
one with tier 2 evidence and you are entitled to know which one you are holding.

## What "no finding" actually means

lockpatch looks for missing controls it knows how to look for. There are 65 of them, and they are
listed openly in [the control catalogue](controls.md) so you can see the edges of the map.

It does not find:

- the control nobody has thought of yet
- a flaw in the logic of what your business rules are supposed to mean, as opposed to whether they are
  enforced at all
- a bug in a dependency that has no advisory
- a chain of three individually harmless behaviours that together give somebody your database
- anything an attacker would find by being creative for a week

An absent finding is the absence of a match against a finite list. It is not the absence of a
vulnerability.

## Unproven is a real outcome, and it is not a pass

Every control check ends in `PASS`, `FAIL`, `UNPROVEN`, or `N/A`. The third one exists because the
alternative is worse.

"I grepped for a session check and found nothing" is not proof that no session check exists. It is
proof that the grep did not find one, which is evidence of absence at the weakest possible strength.
Promoting that to `PASS` is how a security report becomes fiction. lockpatch writes it down as
`UNPROVEN`, records the exact reason it could not decide, and writes out the exact command a human can
run to decide it.

This means an honest run can produce a list of things it could not answer. That list is the point. A
tool that never says "I do not know" is a tool that is guessing somewhere and not telling you.

## Static evidence is much weaker than executed evidence

Without a URL and without a database connection, most of the ROOMS group cannot be settled at all,
and ROOMS is where the expensive breaches live. Reading a migration tells you whether row level
security was switched on in that file. It does not tell you what the table looks like in production
today, what other migrations ran after it, what the effective role of your connection is, or whether
a permissive policy added from a dashboard is sitting beside your careful one and defeating it.

Give lockpatch a URL and it gets stronger. Give it nothing and roughly half of what matters comes
back `UNPROVEN`, honestly labelled.

## It sees the repository, not the system

Everything in this list is outside what lockpatch can reach, and every report reprints it:

- cloud IAM roles, trust policies, and anything in a provider console
- network boundaries, security groups, firewalls, VPN and bastion configuration
- DNS, registrar access, and subdomain takeover
- physical and device security, your team's laptops, your team's browser extensions
- social engineering and support desk takeover
- insider access, and anybody who legitimately has admin today
- anything behind a login you did not give it
- anything inside a service your app calls but whose code you do not have
- race conditions and timing attacks, which need a running system under load
- cryptographic implementation review
- whether your organisation can actually respond when something happens

## It is not a penetration test

Say this out loud to anybody who asks for the result. lockpatch reads code and makes a bounded number
of benign requests, capped at roughly 30 including redirects and retries, against one host you named
and confirmed you own. It does not chain exploits. It does not pivot. It does not test
infrastructure. It does not attempt to gain persistence. It does not test anything it was not pointed
at.

A penetration test is a person, with time, permission, and a report somebody signs. Nobody signs this
one.

## It is not a compliance audit

SOC 2, HIPAA, PCI DSS, ISO 27001 and GDPR are programmes with auditors, evidence periods, scoping
documents and human sign off. Mapping a control to a framework is a reasonable thing to ask for.
Saying an app "is compliant" because a tool ran is not, and lockpatch will not write that sentence.

## It never rotates a credential for you

lockpatch finds leaked keys and writes the rotation runbook. You run it. This is not caution for its
own sake: it does not have your provider console, cannot confirm the new key propagated, and a
rotation that goes half right takes your app down in the middle of the day.

The order matters more than the tooling, and almost everyone gets it backwards. **Rotate first, scrub
history second.** A secret that was public for five minutes is compromised forever. Purging it from
git history without rotating produces a repository that looks clean and a key that still works in
somebody else's collection, which is the worst of both outcomes because it feels like a fix.

## It never rewrites git history on its own initiative

`git filter-repo`, `git filter-branch`, `git rebase` and force pushes are never run by lockpatch, and
they are never included in a "fix everything" approval. A history rewrite changes every commit hash,
breaks open pull requests, and requires every collaborator to delete their clone and clone again.
That is a conversation with its own explicit yes, not a step inside an audit.

Forks and mirrors keep their copy either way. You cannot reach those.

## A fix is only as good as its second proof

Every fix is proven twice, in opposite directions:

```
Before   attacker's request succeeds      legitimate user's request succeeds
Fix      the control is added
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

The second column is the one other tools skip, and it is why a patch that returns `403` to everybody
counts as a failure here rather than a success. If lockpatch cannot express the legitimate twin for a
control, it says so and hands the fix to you rather than applying it. That is a complete outcome, not
a shortfall.

"Fails" also means refused, specifically. A timeout, a 500, a gateway error, or an empty result
because the fixture row never existed all look like failure and prove nothing. The after state has to
be the authorization refusal you expect, from the application, with the record present.

## The rating is deterministic, the scan is not

Severity is a lookup on two enum values, so the same classified finding always produces the same
severity and the same set of findings always produces the same gate. There is no model judgement
between the inputs and the answer.

Choosing those two values is a judgement, and discovery is a judgement. A model can notice a route on
one run and miss it on the next. So two runs of lockpatch against the same unchanged app can find
different things, and the honest sentence is: the rating is deterministic, the scan is not.
`.lockpatch/surface.json` exists so a second run can be diffed against the first rather than assumed
to match it.

## Scanners are optional, and their absence is never a pass

If `gitleaks`, `trufflehog`, `semgrep` or `osv-scanner` are already installed, lockpatch uses them.
It never installs one silently, and it never lets a missing tool turn a check into a `PASS`. The
degraded grep fallbacks are weaker than the tools, so the report says which mode each group ran in.

Two specific honesty traps live here. A grep over git history that walked 500 revisions covered 500
revisions, not all of them, and the report says the number. And `osv-scanner --offline` is only as
current as its last download, so the advisory data's date is printed next to the result or the claim
is not made.

## Fixing everything it finds does not mean you are done

It means you closed what it found. That is genuinely worth doing and it is not the same as being
finished. The next control gap is the one nobody wrote a check for yet.

## When to get a real assessment instead

Stop reading tool output and hire a person when your app holds payments, health records, or
credentials for other people's systems; when you are being asked for a security assessment by a
customer or a regulator; or when you think a breach has already happened. That last one is a human
page, not a skill. lockpatch is not incident response and will say so rather than trying.

## Related

- [The control catalogue](controls.md), all 65 controls and what each one is for
- [FAQ](faq.md), including why there is no score out of 100
- [Quickstart](quickstart.md), a first run end to end
- [The skill itself](../skills/lockpatch/SKILL.md), where all of this is enforced
