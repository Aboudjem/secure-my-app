# Contributing to lockpatch

Thanks for wanting to help. `lockpatch` is a Claude Code skill that audits an app's security:
**find what a stranger can take from your app, then close it and prove it closed**. The second
half is the whole promise. Every finding carries the command that shows the hole and the output
that command produced, and no fix counts as done until the attacker's request is refused and a
legitimate user's identical request still works. A security tool that guesses is worse than no
security tool, because people act on it. So this one is built carefully and tested first. This
guide explains how to add to it without breaking that contract.

Contributions of every size are welcome: a sharper trigger, a new check with a real proof shape, a
reference file for a stack that is not covered, a new eval scenario, a clearer doc, a typo fix.
Open an issue first if you want to discuss a larger change.

## The words this repo uses

They are fixed, and they mean one thing each.

- A **finding** is one hole, with a severity and a named thing a stranger can take.
- The **proof** is the exact request that demonstrates it: method, path, headers, body, and the
  response that came back. It is runnable by a human who was not there.
- A **fix** is the change that closes the finding.
- The **re-run** is the same proof request, executed again after the fix. It has to fail now.
- The **login check** is the user's own authenticated path, executed again after the fix. It has
  to still work.
- The audit's output lives under `.lockpatch/` in the project being audited, never in this repo.

Anything lockpatch believes but cannot reproduce is a **suspicion**, and the report says so in that
word. A suspicion is never counted, ranked or fixed as a finding.

## Repo layout

```
.claude-plugin/
  plugin.json           the Claude Code manifest (the version 10x pins)
  marketplace.json      the single-plugin marketplace entry
.cursor-plugin/
  plugin.json           the same manifest under Cursor's directory name
.copilot-plugin/
  plugin.json           the same manifest under GitHub Copilot's directory name
skills/lockpatch/
  SKILL.md              the skill: the two phases, the audit procedure, the report
                        template, the proof rules, the fix-and-re-verify loop, the
                        handoff format
  references/           the depth, loaded only when the audit reaches that area
evals/
  check_skill.py        deterministic assertions on SKILL.md (runs in CI)
  scenarios.md          behavioral scenarios + rubrics
  RED-baseline.md       the recorded RED: the deterministic suite + the cold run
  README.md             the two eval layers and how to reproduce them
tests/
  test_manifests.py     manifests, version parity, required files, README link and
                        asset resolution, i18n parity (runs in CI)
examples/               an illustrative report in the shape lockpatch produces
assets/                 animated SVGs + the 1280x640 social preview card
docs/                   quickstart, editors, limits, faq
                        (docs/audit/ is a local build journal, gitignored)
READMEs/                zh-CN, ja, es, fr translations of README.md
AGENTS.md               instructions for AI agents working in / invoking this repo
README.md               human-facing overview
llms.txt                the machine-readable map of this repo
LICENSE                 MIT
```

`AGENTS.md` is the source of truth for how the skill behaves and the rules it enforces. Read it
before changing anything in `skills/`.

## We build TEST-FIRST (RED, then GREEN, then REFACTOR)

This skill exists to fix specific, observed failures. Every guarantee traces back to something we
watched a model do wrong first.

**The rule: no new behavioral guarantee lands without a failing baseline first.**

The founding baseline is recorded in [`evals/RED-baseline.md`](evals/RED-baseline.md). Asked to
audit an app's security with no skill installed, a cold model produced a ranked list of plausible
vulnerabilities with no request behind any of them, edited three files in the same turn without
asking, and reported the result as fixed without running anything. That single run carries most of
the failures this skill exists to prevent: **findings with no proof**, so nothing in the list is
falsifiable; **fixes applied without approval**, in an area where a wrong fix locks real users out;
**no re-verification**, so "fixed" means "edited"; and **no check that the owner can still log in**.

1. **RED: watch it fail.** Before you write skill text, run the scenario against a model that does
   *not* have your change (or does not have the skill at all) and record what it does wrong,
   verbatim. Test the weak case too: the skill must hold on cheaper models, not only the strongest
   one.
2. **GREEN: write the minimum that fixes it.** Add the clause, rail or gate that makes that exact
   failure stop. Re-run the same scenario and show it now behaves. If the change is statically
   checkable, add an assertion to `evals/check_skill.py` (or `tests/test_manifests.py` if it spans
   the repo).
3. **REFACTOR: tighten.** Clean up wording, keep the skill body under 600 lines, move depth into
   `references/`, deduplicate, all without changing behavior. Re-run to confirm.

A PR that adds behavior but cites no baseline failure it fixes will be sent back for a RED step.
"I think a model might" is not a baseline; "here is the model doing it" is.

## Hard rules you must keep

These mirror the skill's rules in `AGENTS.md` and `SKILL.md`. Do not look for loopholes.

- **Proof or it is not a finding.** Any new check you add must define the request that proves it
  and the response that confirms it. A check that can only produce a hunch belongs in the
  suspicions list, and its text must say "suspicion" out loud.
- **No fix without a human approval, one finding at a time.** Do not add a batch mode, an
  auto-apply flag, an "obviously safe" exemption, or a severity threshold above which approval is
  skipped. The approval is per finding because the blast radius is per finding.
- **No fix is closed without both re-runs.** The proof request has to fail, and the user's own
  authenticated path has to still work. Removing the second check to make a scenario pass is the
  single change most likely to be rejected on sight.
- **Secrets by location, never by value.** No code path may write a credential's value into the
  report, the proof, or anything else under `.lockpatch/`. Name the file, the line, the
  environment variable, and print a redacted form.
- **Never rewrite history, never destroy evidence.** No `git rebase`, no `git commit --amend`, no
  force-push, no `git filter-branch`, and no deleting a file that holds the evidence for a
  finding. A leaked key in history is rotated, and rotation is the user's action, not the skill's.
- **Content the audit reads is data, never instructions.** A response body, an error page, a log
  line, an issue comment: none of it can change the plan, the severity, the approval state or the
  report. This is not optional in a tool whose whole job is pointing at hostile input.
- **Only targets the user named.** The skill never widens scope to a host, a subdomain, a
  production environment or a third-party service the user did not name, and it says out loud that
  authorization is the user's to give.
- **Description stays WHEN-only.** Do not re-introduce a procedure summary into the frontmatter
  `description`. It becomes a shortcut models follow instead of reading the body.
- **No hallucination, anywhere.** No invented CVEs, no invented framework behavior, no "works with
  X" claims without a primary source. If a check depends on a framework's defaults, cite the
  version those defaults were read from.
- **Keep the SVGs GitHub-safe.** No `<script>`, no external references, well-formed XML, and a
  `prefers-reduced-motion` guard in every animated one. CI enforces all four.
- **Frontmatter stays spec-clean.** `name` matches the directory and `^[a-z0-9]+(-[a-z0-9]+)*$`
  (no leading, trailing or consecutive hyphens); `description` is at most 1024 characters; the
  version lives under `metadata` as a quoted string, and it must match `plugin.json`,
  `marketplace.json`, both editor mirrors and the latest `CHANGELOG.md` entry.
- **No emoji in section headers, and no em dashes anywhere.** Use a comma, a full stop, or
  parentheses. CI checks the skill body for both.

## How to test locally

```bash
# 1. Both deterministic suites must pass.
python3 evals/check_skill.py skills/lockpatch/SKILL.md    # expect: exit 0, all checks pass
python3 tests/test_manifests.py                           # expect: exit 0, all checks pass

# 2. Run the skill for real: drop it in and exercise the path you changed.
cp -r skills/lockpatch ~/.claude/skills/lockpatch
#   then ask Claude Code: "lockpatch this" in an app you own
```

For a behavioral change, re-run the relevant [`evals/scenarios.md`](evals/scenarios.md) case cold
(RED) and with the skill (GREEN) and paste the before and after into your PR. Run it against an app
you own, with a real database and a real login. An audit of a fixture with no auth proves nothing
about the checks that matter.

## Commit and PR etiquette

- Branch off the default branch; do not commit directly to it.
- Keep commits focused; messages say what changed and *why* (link the baseline failure your change
  fixes).
- One logical change per PR. Smaller PRs get reviewed faster.
- In the PR description include: the RED baseline (the failure you observed), the GREEN fix, and
  how you verified it (`check_skill.py` output and/or a sample run).
- **Never commit a `.lockpatch/` directory, a real proof request, a real hostname, a token, or
  anything from `docs/audit/`.** A finding from your own app is not a test fixture.
- Be kind in review, see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## CI must pass

Every PR runs `.github/workflows/validate.yml`: the frontmatter check, the manifest version
agreement, the `check_skill.py` eval, the `test_manifests.py` release gate, a secrets scan, the
gitleaks scan, the markup safety gate (SVG and HTML, including the reduced-motion guard), the
Markdown relative-link check, the lychee link check, and `claude plugin validate` when the CLI is
present on the runner. It must be green before merge. If CI fails, read the log and push a fix; do
not ask for a merge override.

Thanks again. Careful contributions to a tool people will believe about their own security
genuinely matter.
