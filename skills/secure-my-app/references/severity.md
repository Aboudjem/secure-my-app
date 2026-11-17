# Severity, and the gate

Load this when assigning severity, or when the user challenges a rating.

## Two axes, no adjectives

Severity is a lookup. You are not judging how bad something feels, you are reading two enum values
out of `surface.json` and finding the cell.

**Be honest about where the judgement lives.** Choosing the two values is a judgement, and you should
write the reasoning for each into the finding. The step from those two values to a severity is not a
judgement, it is this table. When someone asks whether the rating is objective, that is the
distinction to give them: the inputs are argued, the arithmetic is fixed.

**Axis 1. Who can do it.** The weakest actor who can reach it.

| Value | Means |
| --- | --- |
| `PUBLIC` | No account. A stranger with a URL |
| `ANY_USER` | Any account, including one they just created for free |
| `SAME_TENANT` | Someone already inside the victim's organisation |
| `ADMIN_ONLY` | Requires privilege the attacker would have to steal first |

**Axis 2. What they get.** The most valuable thing reachable through it.

| Value | Means |
| --- | --- |
| `ALL_DATA` | Every row, or every user. The table, not a record |
| `OTHER_USERS` | A specific victim's data, account, or money |
| `SELF_ESCALATION` | Privilege, credit, or money for themselves only |
| `INFO` | Structure, versions, existence. No data |

## The matrix

| | ALL_DATA | OTHER_USERS | SELF_ESCALATION | INFO |
| --- | --- | --- | --- | --- |
| **PUBLIC** | CRITICAL | CRITICAL | HIGH | MEDIUM |
| **ANY_USER** | CRITICAL | HIGH | HIGH | LOW |
| **SAME_TENANT** | HIGH | HIGH | MEDIUM | LOW |
| **ADMIN_ONLY** | MEDIUM | MEDIUM | LOW | LOW |

**In one sentence: CRITICAL means a stranger, or anybody who can sign up, can read or write data that
is not theirs, today, with a request you have written out.**

## Two overrides

1. **A live, unrotated credential is always CRITICAL**, whatever the matrix says. Its reachability is
   "anyone who has ever cloned this repository", which the matrix cannot express. A rotated key found
   in history is LOW, and the finding becomes hygiene.
2. **Anything below rung 4 gets no severity.** It is `UNPROVEN`, it sits in its own appendix, and it
   contributes nothing to the gate. Do not assign a provisional severity to an unproven finding; a
   provisional CRITICAL is read as a CRITICAL.

## Worked examples

| Finding | Who | What | Severity |
| --- | --- | --- | --- |
| No RLS on `profiles`, publishable key reads it | `PUBLIC` | `ALL_DATA` | CRITICAL |
| `/api/orders/:id` has no ownership check | `ANY_USER` | `OTHER_USERS` | HIGH |
| Live Stripe secret key in git history, not rotated | override | override | CRITICAL |
| Same key, confirmed rotated last month | `PUBLIC` | `INFO` | LOW |
| Profile update accepts `role` from the body | `ANY_USER` | `SELF_ESCALATION` | HIGH |
| A teammate can read another team member's draft | `SAME_TENANT` | `OTHER_USERS` | HIGH |
| Stack trace on a 500 shows file paths | `PUBLIC` | `INFO` | MEDIUM |
| `X-Frame-Options` missing on a page with no authenticated action | `PUBLIC` | `INFO` | MEDIUM |
| Admin route lets an admin delete audit logs | `ADMIN_ONLY` | `SELF_ESCALATION` | LOW |
| Dev dependency advisory, not reachable at runtime | not reachable | `INFO` | LOW |

When two readings are defensible, take the **higher-severity one and write the reasoning into the
finding**. An over-rated finding costs the user ten minutes of reading. An under-rated one costs them
the breach.

## When the matrix cannot express the finding

Four axes are two axes short of a real severity model, on purpose, because a model nobody reads rates
nothing. But some findings genuinely do not fit, and forcing them into a cell understates them:

- **Code execution on your server.** Not "data", it is the machine.
- **Destruction.** An attacker who can delete rather than read. The matrix only measures reading and
  writing what is not yours.
- **Availability.** Taking the app down is not in any of the four `what they get` values.
- **Money moving.** Fraud that costs real money is worse than `SELF_ESCALATION` suggests.
- **Downstream compromise.** A key to somebody else's system, where the blast radius is not yours.

For these, **rate CRITICAL, and write one line saying the matrix does not cover this class and why.**
Do not silently squeeze it into `SELF_ESCALATION`. Do not invent new enum values either; the point of
a small table is that it stays readable. The exception carries its own explanation.

If you find yourself taking this exit more than once or twice in a run, the finding is probably an
architectural problem rather than a control gap. Say that instead of filing five findings.

## The gate

There is no 0 to 100 score. Three reasons, and say them if asked:

1. A number invites "we went from 62 to 78", which is not a security goal. "Can a stranger read my
   users table" is.
2. Any weighted sum is gameable by adding passing controls, which is the exact failure mode a score
   is supposed to prevent.
3. A tool that cannot see infrastructure, IAM, or business logic has no basis for claiming it
   measured a percentage of anything.

What ships instead is a count and a gate, computed by rule:

```
GATE: DO NOT LAUNCH            >= 1 CRITICAL
GATE: LAUNCH WITH KNOWN GAPS   0 CRITICAL, >= 1 HIGH
GATE: NOTHING CONFIRMED HERE   0 CRITICAL, 0 HIGH
```

**Never print the gate without its coverage.** The gate on its own is the most misleading line this
skill can produce, because a run that checked everything and a run that could barely check anything
reach the same label:

```
VERDICT: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 15 n/a   [static only, no live probes]
```

Three rules on that line:

1. `unproven` and `n/a` are always shown, never rolled into the checked count.
2. The evidence mode is always shown. `static only` is a much weaker document than `static + live`.
3. MEDIUM and LOW findings still get listed under `NOTHING CONFIRMED HERE`. The label describes the
   two top bands, not the report.

**The third label must not be softened to "secure", "passed", or "no exposure".** Nothing confirmed
here is the strongest honest claim available to a tool that read some code and made thirty requests.
"Secure" tells a user to stop looking, and that is a harm this skill can cause. Say the full phrase in
conversation too, not an abbreviation of it.

None of the three labels is permission to launch. They summarise what was found, and the release
decision belongs to the human who knows what the app is for.

The gate is ungameable in the useful direction: adding files can only add findings. The only way to
move it is to remove a confirmed exposure, or to check less, which the coverage half exposes.

## What "deterministic" means here, exactly

Be precise, because this is the claim most likely to be overstated.

**Deterministic:** the arithmetic. Given a finding already classified as `PUBLIC` and `ALL_DATA`, the
severity is always CRITICAL. Given the same set of classified findings, the gate is always the same.
There is no model judgement between the inputs and the answer.

**Not deterministic:** two things, and both matter. Discovery, because a model may notice a route on
one run and miss it on another. And classification, because deciding that a finding is `PUBLIC`
rather than `ANY_USER` is an argument, which is why every finding carries its reasoning.

So: **the rating is deterministic, the scan is not.** If a user asks "will I get the same result
tomorrow", that sentence is the honest answer, plus the fact that `surface.json` exists precisely so
a second run can be diffed against the first rather than assumed to match it.

## Reporting order

Severity first, then reachability, then group order (KEYS, DOOR, ROOMS, PIPES, VAULT, FLOOR, SUPPLY).
Within a severity band, put the one with the smallest fix first. People fix in the order they read,
and an early win keeps them reading.
