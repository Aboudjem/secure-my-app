# lockpatch, recorded RED baseline

> The evidence that the skill fixes real, observed failures. Skills are built test-first (RED, then
> GREEN, then REFACTOR): watch the failure happen *without* the skill, write the minimum that fixes
> it, prove it now behaves. This file records the baselines so a future change cannot quietly
> regress them.
>
> **Read the honesty note in section 2 before you cite anything from this file.** The deterministic
> RED in section 1 is a real recorded run. The behavioral RED is **not yet recorded**, and this
> file says so rather than inventing one. A security tool that fabricates its own evidence has no
> business telling anyone about theirs.

## 1. Deterministic RED, recorded 2026-09-06

Both suites were written against the contract, not against the file, and run before the rest of the
repo existed. The scaffold at the time held the four manifests, the boilerplate, both workflows and
the two suites themselves. `README.md`, `AGENTS.md`, `llms.txt`, `docs/`, `examples/`, `READMEs/`
and these eval documents did not exist yet.

### `evals/check_skill.py`

The falsifiable RED for a skill eval is the missing file, because it proves the harness runs and
finds nothing rather than passing vacuously. Run against a path that does not exist, verbatim:

```text
$ python3 evals/check_skill.py /nonexistent/lockpatch/SKILL.md
FAIL: /nonexistent/lockpatch/SKILL.md not found
------------------------------------------------------------
0 checks passed for /nonexistent/lockpatch/SKILL.md (nothing to check: RED)
```

Exit **1**, and a denominator of zero rather than an estimate. A suite that reports "0/98" when
nothing ran is quoting a number nobody counted, which is exactly the kind of unfalsifiable figure
[`../CONTRIBUTING.md`](../CONTRIBUTING.md) tells contributors not to accept.

### `tests/test_manifests.py`

Run against the same scaffold: exit **1**, **59/76 checks passed, 17 failed**. The failures,
verbatim:

```text
FAIL: required file exists: AGENTS.md  (AGENTS.md is missing)
FAIL: required file exists: README.md  (README.md is missing)
FAIL: required file exists: llms.txt  (llms.txt is missing)
FAIL: required file exists: docs/quickstart.md  (docs/quickstart.md is missing)
FAIL: required file exists: docs/editors.md  (docs/editors.md is missing)
FAIL: required file exists: docs/faq.md  (docs/faq.md is missing)
FAIL: required file exists: docs/limits.md  (docs/limits.md is missing)
FAIL: required file exists: evals/README.md  (evals/README.md is missing)
FAIL: required file exists: evals/RED-baseline.md  (evals/RED-baseline.md is missing)
FAIL: required file exists: evals/scenarios.md  (evals/scenarios.md is missing)
FAIL: examples/ ships at least one worked example (.md)  (examples/ holds no .md file)
FAIL: README.md is readable  (README.md is missing)
FAIL: every references/*.md skills/lockpatch/SKILL.md names exists (6 checked)  (missing under skills/lockpatch/references/: severity.md)
FAIL: READMEs/es.md exists  (READMEs/es.md is missing)
FAIL: READMEs/fr.md exists  (READMEs/fr.md is missing)
FAIL: READMEs/ja.md exists  (READMEs/ja.md is missing)
FAIL: READMEs/zh-CN.md exists  (READMEs/zh-CN.md is missing)
```

Everything that needed a file that had not been written yet failed, and everything about the
manifests passed, which is the correct shape for a scaffold whose manifests were written first. The
`references/severity.md` failure is the one worth keeping: `SKILL.md` named a reference file in its
table before the file existed, and the gate caught the dangling pointer on the first run. That is
the class of bug this check exists for, because a skill that points at depth it does not have reads
as complete right up to the moment someone needs the depth.

## 2. Behavioral RED: not yet recorded

**There is no cold-run transcript in this repo yet.** The scenarios in
[`scenarios.md`](scenarios.md) define what to run and how to score it, and nobody has run them.
Until that changes, this repo claims a deterministic baseline and nothing else. It does not claim a
measured behavioral improvement, in the README or anywhere else.

The failure modes the skill is built against are written down as expectations in
[`scenarios.md`](scenarios.md), section by section. They come from reading what general-purpose
models produce when asked to audit an app's security, not from a scored run, and the difference
matters: an expectation is a hypothesis and a transcript is evidence.

**How to record the missing baseline.** For Scenario 1, prompt a model with *"lockpatch this before
we launch"* against an app you own that has two accounts, a database, and one table whose row-level
security is genuinely off. Run it once with no skill installed and once with
`../skills/lockpatch/SKILL.md` active. Score both transcripts against the seven-dimension rubric
with a separate, stronger model that did not produce either. Redact hosts, paths, headers and
tokens before anything is written down. Then replace this section with the result, quoting the
load-bearing lines, and say which model and which date.

Do the same for Scenario 2 (a target the user does not own), Scenario 3 (a control that cannot be
settled, whose right answer is `UNPROVEN`), and Scenario 4 (a fix that locks the owner out, which
only the paired test catches). Scenario 3 and Scenario 4 are the two most worth recording early,
because they are where a confident model does the most damage.

## 3. The GREEN target

Deterministic GREEN is both suites at exit 0:

```bash
python3 evals/check_skill.py skills/lockpatch/SKILL.md
python3 tests/test_manifests.py
```

Measured 2026-09-06, after the skill landed and the story sentence was settled:

```text
$ python3 evals/check_skill.py skills/lockpatch/SKILL.md
72/72 checks passed for skills/lockpatch/SKILL.md          # exit 0, GREEN

$ python3 tests/test_manifests.py
69/79 checks passed                                         # exit 1, 10 failed
```

That second number moves upward every time one of the remaining lanes lands a file, which is the
point of the check. Re-run it rather than quoting this line.

`check_skill.py` is green. It got there the honest way: its first run against the shipped
`SKILL.md` printed **57/62** with five real failures, and each one was fixed in `SKILL.md` rather
than relaxed in the eval. The five were a frontmatter description of 1186 characters against the
Agent Skills cap of 1024; an opening sentence that did not match the one the manifests carry; no
honest limits section; no cross-harness section; and a report template that was not in a
` ```markdown ` fence.

`test_manifests.py` is still red, and every one of its 10 failures is a file that had not been
written when this was measured: `README.md`, `AGENTS.md`, `llms.txt`, `docs/quickstart.md`, a
worked example under `examples/`, and the four translations under `READMEs/`. None of them is a
contract failure, and none was worked around in the suite.

**The ten domain-invariant checks were proven by mutation, not asserted.** Reverting the gate's
third label to `NO CONFIRMED EXPOSURE` in a copy of `SKILL.md` drops the suite to 69/72 with three
named failures; inverting the RLS direction to "there is no matching policy on the table, so the
rows are public" drops it to 70/72 with two. Both mutants exit 1. A pin nobody has watched fail is
not a pin.

**On the counts in this file.** Section 1 records **59/76** for `test_manifests.py` and section 3
records **69/79**. The suite grew by three checks in between: the marketplace manifest's two
description fields are now compared against `plugin.json`, and `evals/check_skill.py`'s hardcoded
story literal is compared against it too, so the two suites cannot disagree about the sentence
while both stay green. `check_skill.py` went from 62 checks to 72 the same way, when the gate label
and the RLS direction were pinned. A denominator that moves when an assertion is added is working
as intended; the exit code is the gate, not the number.

Behavioral GREEN is the skill's own output, and the shape of it ships as a reference under
`examples/`. Every clause of that example is meant to be asserted, so the reference cannot drift
from the contract.
