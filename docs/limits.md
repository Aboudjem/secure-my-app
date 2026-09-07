# Honest limits

**A clean secure-my-app run is not evidence that your app is secure.** It is evidence that in the part
of your app this run could actually check, nothing rose to CRITICAL or HIGH. Those are different
claims, and the distance between them is where people get hurt.

Below is what it does not do, cannot see, or cannot promise. Every report reprints a short version.

## The gate is not a verdict

```
GATE: DO NOT LAUNCH            >= 1 CRITICAL
GATE: LAUNCH WITH KNOWN GAPS   0 CRITICAL, >= 1 HIGH
GATE: NOTHING CONFIRMED HERE   0 CRITICAL, 0 HIGH
```

The third label is deliberately awkward. Not "secure", not "passed", not "clean", not "no exposure
found". It says only that nothing in this run reached the top two bands, and medium, low and unproven
results are routinely listed underneath it. The phrase is never abbreviated anywhere.

None of the three is permission to launch. That decision belongs to whoever knows what the app holds.

## The gate never ships without its coverage

A run that checked everything and a run that could barely check anything reach the same label. So the
counts are printed on the same line, always:

```
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

Read it as one sentence. Nine unproven means nine controls this run could not settle either way. Six
`n/a` means six controls whose surface does not exist in your app, which is a real result.

## Evidence has tiers, and the weak ones close nothing

| Tier | Tag | What it means | Can it support a PASS |
| --- | --- | --- | --- |
| 1 | `static` | Read in the repo: a file, a line, a config value, a migration | Sometimes, for config that is itself the control |
| 2 | `executed` | A command was run here and this is its real output | Yes |
| 3 | `recipe` | A command written out for you to run. Nobody ran it | Never |

A run that came back all tier 1 and tier 3 says so in its first line, because that is a much weaker
document than one carrying executed evidence.

## What "no finding" actually means

It looks for missing controls it knows how to look for. There are 65, listed openly in
[the catalogue](controls.md) so you can see the edges of the map. It does not find:

- the control nobody has thought of yet
- a flaw in what your business rules are supposed to mean, as opposed to whether they are enforced
- a bug in a dependency that has no advisory
- a chain of three harmless behaviours that together give somebody your database
- anything an attacker would find by being creative for a week

An absent finding is the absence of a match against a finite list. It is not the absence of a
vulnerability.

## Unproven is a real outcome, and it is not a pass

"I grepped for a session check and found nothing" is not proof that no session check exists. Promoting
that to `PASS` is how a report becomes fiction, so it is written down as `UNPROVEN` with the exact
reason and the exact command that would settle it.

An honest run therefore produces a list of things it could not answer. That list is the point. A tool
that never says "I do not know" is guessing somewhere and not telling you.

## Static evidence is much weaker than executed evidence

Without a URL and without a database connection, most of ROOMS cannot be settled at all, and ROOMS is
where the expensive breaches live. A migration tells you row level security was switched on in that
file. It does not tell you what the table looks like in production today, what ran after it, or whether
a permissive policy added from a dashboard sits beside your careful one and defeats it.

## It sees the repository, not the system

- cloud IAM roles, trust policies, and anything in a provider console
- network boundaries, security groups, firewalls, VPN and bastion configuration
- DNS, registrar access, and subdomain takeover
- physical and device security, your team's laptops and browser extensions
- social engineering and support desk takeover
- insider access, and anybody who legitimately has admin today
- anything behind a login you did not give it
- anything inside a service your app calls but whose code you do not have
- race conditions and timing attacks, which need a running system under load
- cryptographic implementation review
- whether your organisation can actually respond when something happens

## It is not a penetration test, and not a compliance audit

Say that out loud to anybody who asks for the result. It reads code and makes at most about 30 benign
requests against one host you named. It does not chain exploits, pivot, or test infrastructure. A
penetration test is a person, with time, permission, and a report somebody signs. Nobody signs this one.

SOC 2, HIPAA, PCI DSS, ISO 27001 and GDPR are programmes with auditors and human sign off. Mapping a
control to a framework is fair to ask for; calling an app "compliant" because a tool ran is not.

## It never rotates a credential, and never rewrites history

It finds leaked keys and writes the rotation runbook. You run it. It has no access to your provider
console, cannot confirm a new key propagated, and a rotation that goes half right takes your app down.

**Rotate first, scrub history second**, and almost everyone gets this backwards. A secret that was
public for five minutes is compromised forever. Purging it from git history without rotating produces a
repository that looks clean and a key that still works in somebody else's collection, which is the
worst outcome because it feels like a fix.

`git filter-repo`, `git filter-branch`, `git rebase` and force pushes are never run on its own
initiative and never inside a "fix everything" approval. A rewrite changes every commit hash, breaks
open pull requests, and makes every collaborator delete their clone. Forks and mirrors keep a copy.

## A fix is only as good as its second proof

```
Before   attacker's request succeeds      legitimate user's request succeeds
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

The second column is the one other tools skip, and it is why a patch that returns `403` to everybody
counts as a failure here. If the legitimate twin cannot be expressed, the fix is handed to you rather
than applied. "Fails" means refused, specifically: a timeout, a 500, or an empty result because the
fixture row never existed all look like failure and prove nothing.

## The rating is deterministic, the scan is not

Severity is a lookup on two enum values, so the same classified finding always produces the same
severity and the same findings always produce the same gate. But choosing those values is a judgement
and so is discovery, and a model can notice a route on one run and miss it on the next.
`.secure-my-app/surface.json` exists so a second run can be diffed rather than assumed to match.

## Scanners are optional, and their absence is never a pass

If `gitleaks`, `trufflehog`, `semgrep` or `osv-scanner` are installed it uses them, never installs one
silently, and never lets a missing tool turn a check into a `PASS`. Two honesty traps live here. A grep
over git history that walked 500 revisions covered 500 revisions, not all of them, so the report prints
the number. And `osv-scanner --offline` is only as current as its last download, so the advisory date
is printed or the claim is not made.

## Fixing everything it finds does not mean you are done

It means you closed what it found. That is worth doing and it is not the same as being finished. The
next control gap is the one nobody wrote a check for yet.

## When to get a real assessment instead

Hire a person when your app holds payments, health records, or credentials for other people's systems;
when a customer or a regulator is asking; or when you think a breach has already happened. That last
one is a human page. secure-my-app is not incident response and will say so rather than trying.

## Related

- [The control catalogue](controls.md), all 65 controls and what each one is for
- [FAQ](faq.md) · [Quickstart](quickstart.md) · [The skill](../skills/secure-my-app/SKILL.md)
