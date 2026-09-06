# lockpatch evals

Two layers, both built test-first (RED, then GREEN, then REFACTOR). The recorded baselines live in
[`RED-baseline.md`](RED-baseline.md).

The reason this repo carries an eval suite at all: lockpatch produces claims about somebody's
security, and people act on those claims. A skill that drifts into advice-shaped output, or that
promotes a guess to a CRITICAL, fails silently. There is no crash and no red test in the user's
project. CI is the only place that failure can be caught.

## 1. Deterministic, runs in CI

### `check_skill.py`: the design lock as assertions on `SKILL.md`

Encodes the house contract and the lockpatch design lock as pass/fail checks on
`../skills/lockpatch/SKILL.md`. It is the regression guard: if a future edit drops the WHEN-only
description, the story sentence, a required section, the section order, or a reference file it
points at, CI goes red.

```bash
python3 evals/check_skill.py skills/lockpatch/SKILL.md
```

What it asserts:

- **Frontmatter**: `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$`, is at most 64 characters, and equals
  the parent directory. `description` is present, at most 1024 characters (the Agent Skills spec
  cap) and at least 400 (the house floor). `metadata.version` is present and **quoted**, and there
  is no bare top-level `version:`. `license` is MIT and `argument-hint` is declared.
- **The description contract**: it carries the story sentence verbatim, names the trigger word,
  says that every finding carries a proof, says that a fix waits for approval, and is WHEN-only. A
  numbered procedure in the description becomes a shortcut models follow instead of reading the
  body, so `\b[1-9]\.\s` fails the check.
- **Structure**: the H1 is the bare slug; a section exists for each house function (the overview,
  the invocation, when to use and when not, the procedure, the hard rules, the output artifact, the
  depth pointer, the failure modes) and they appear in that order; honest limits and cross-harness
  are present; the body is under 600 lines; `/lockpatch`, `$ARGUMENTS` and the `.lockpatch/` output
  directory are all documented; and the report template sits in one fenced ` ```markdown ` block.
- **Style**: no emoji in any heading, and no em dash anywhere in the file. Arrows, the middle dot
  and the maths operators the house uses on purpose are left alone.
- **References**: every `references/*.md` path the body mentions exists on disk. A skill that
  points at depth it does not have reads as complete until someone needs the depth.
- **Domain invariants**: two claims that read as fine and are wrong are pinned rather than
  trusted to review, both caught by an adversarial review on 2026-09-06. The gate's third label is
  `NOTHING CONFIRMED HERE`, the retired `NO CONFIRMED EXPOSURE` appears nowhere in the skill or its
  references, and a worked example prints the label with its coverage counts on the same line.
  Row-level security switched ON with no matching policy **denies**, and the inverted claim (a
  table with no policy is therefore readable) appears nowhere. The inverted-claim regex ships with
  two self-tests proving it fires on the wrong sentence and stays quiet on the correct one, because
  a gate nobody has watched fail is not a gate.
- **Control sections give orders, not advice**: `you should`, `you may want to`, `it is
  recommended` and their neighbours are banned inside the procedure, the hard rules and the common
  mistakes. A hedge in a control section is what a model reads as permission to skip the step. A
  line that quotes the banned wording **in order to ban it** is a specimen and is exempt, and the
  number of specimens is pinned in `EXPECTED_SPECIMENS`, so the hatch cannot be widened silently.

A section may carry its own domain name as long as the function is there: `## The run` counts as the
procedure, `## The output` as the artifact, `## What this refuses to do` as the hard rules. The
contract is the function and the order, not a fixed vocabulary.

**The RED.** This suite was written and run before `skills/lockpatch/SKILL.md` existed. The
recorded run and its verbatim output are in [`RED-baseline.md`](RED-baseline.md).

Two RED targets you can reproduce right now:

```bash
# (i) the missing-file RED, the original baseline's shape
python3 evals/check_skill.py /nonexistent/lockpatch/SKILL.md   # exit 1, 0 checks ran

# (ii) a real sibling skill of the wrong shape
git clone https://github.com/Aboudjem/loopify /tmp/loopify
python3 evals/check_skill.py /tmp/loopify/skills/loopify/SKILL.md   # exit 1
```

(ii) is the useful one. loopify is a well-formed, shipping Agent Skill built by the same author to
the same standards, so the checks it fails are precisely the lockpatch-specific contract: the story
sentence, the proof-and-approval clauses, the section functions, the `.lockpatch/` output directory.
It passes the generic ones (spec-clean frontmatter, a documented `$ARGUMENTS`, a body under the line
cap). Record the figure you measure along with the loopify version you cloned; a number without a
version pinned to it is not reproducible.

### `test_manifests.py`: the release gate

```bash
python3 tests/test_manifests.py
```

Manifest validity across all four manifests, one version everywhere it is declared (the four
manifests, the latest `CHANGELOG.md` entry, and `SKILL.md`'s `metadata.version`), the required-file
list, the `SKILL.md` frontmatter contract, every relative link and every asset the README points at,
every `references/*.md` the skill names, the four translations with their may-lag marker, and a
secrets scan across every tracked file.

Its RED, recorded the same day against the scaffold: **59/76 checks passed, 17 failed**, quoted in
full in [`RED-baseline.md`](RED-baseline.md).

## 2. Behavioral: `scenarios.md` (judged transcripts)

Four scenarios: the core case, one that must be **refused** (a target the user does not own), one
whose right answer is **UNPROVEN** rather than a finding, and one where the **fix itself** is the
danger and only the paired test catches it. Each has a RED expectation and a GREEN rubric of seven
dimensions, all checkable from a transcript.

**Be honest about what exists here.** There is **no recorded behavioral run yet**. The scenarios
define what to run and how to score it; nobody has run them. Until that changes this repo claims a
deterministic baseline and nothing more, and neither the README nor anything else may claim a
measured behavioral improvement. [`RED-baseline.md`](RED-baseline.md) section 2 says how to record
the missing baseline, and which two scenarios are worth recording first.

To run one yourself: prompt a model twice, once with no skill and once with
`skills/lockpatch/SKILL.md` active, against an app you own with a real login and more than one user
account, then score each transcript against the rubric. Never let the model that produced the
transcript score it. Redact hosts, paths, headers and tokens before any transcript is written down.
