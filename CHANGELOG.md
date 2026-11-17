# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2026-11-17

A shorter first screen, an install line for each agent, and new images. No change to what the skill does.

### Changed

- **README first screen.** One line, one sentence, three points with their proof (fixes proven
  closed, proof for each hole, no surprise changes), the agents it works with, the command, the real
  sample, then what it is, when to use it and what you get. The limit stays on the first screen.
- **Pick your agent.** The Install section opens with a badge for Claude Code, Codex, Cursor, Gemini
  CLI, GitHub Copilot and OpenCode. Each links to one command that installs for all your projects
  (`-g`). Each command was run into an empty home folder on 2026-11-17.
- **Install paths.** `docs/editors.md` now gives `~/.agents/skills/` as the global path for Cursor,
  Codex, GitHub Copilot, Gemini CLI and OpenCode, where skills 1.9.0 puts the files.
- **Images.** New hero (dark and light) and social preview: the headline, the three points, the
  command, and alice's request to bob's invoice, `200` before the fix and `404` after it.
- **Listing description.** Shorter and plainer. The skill's own description is unchanged.
- **Translations.** The four translations carry the same changes.

## [0.3.1] - 2026-11-17

A clearer first screen and truer wording. No change to what the skill does.

### Changed

- **README first screen.** One install command, the line to type, then the real VERDICT block and
  the alice and bob finding. A `Why use it` block follows, each point with its proof. The limit
  sits next to the promise: without a live URL most access checks come back `UNPROVEN`.
- **True wording about proof.** A `PROOF` can be a code line, not always a command. The README,
  `llms.txt`, `AGENTS.md` and the FAQ now say so.
- **Listing description.** The manifests now say what a run gives you: 65 checks, a proof per hole,
  and a fix that counts only when its `VERIFY` command shows the change. The skill's own
  description is unchanged.
- **Translations.** The four translated READMEs are full translations of the new English README.
  A new test checks that their code blocks and heading levels match the English one.
- **Social preview.** Rebuilt with the new headline and the real run's numbers.

## [0.3.0] - 2026-11-17

The report now opens with its verdict and the three things to do first. The README shows a report
from a real run, and one command runs every test.

### Changed

- **Verdict first.** Line 1 of every report is `VERDICT: <gate label>` with the coverage counts on
  the same line. Line 2 holds the counts. Then `DO FIRST`: at most three numbered actions, each a
  control id and a plain action. The list is never padded. Gate labels, gate rule, control ids,
  severities and the proof-first ladder are unchanged.
- **Coverage adds up.** Every coverage example now sums to the 65 controls (`15 n/a`, was `6`).
- **Stable finding keys.** `surface.json` keys a finding by control id plus its `WHERE`, so a
  second run matches it when a line number moves.
- **README.** The invocation (`/secure-my-app`) is in the first screen. New sections: Proof, FAQ,
  Limits, and a works-with table of the agents tested on 2026-11-17. Star badge removed.
- **No email in the manifests.** The author is a name and a URL.

### Added

- `examples/vulnerable-app/`, a one-file API with holes on purpose, to try the skill safely.
- `examples/sample-report.md` and `sample-surface.json`, written by a real run on that fixture
  (Claude Code 2.1.326). The old Tidemark report is kept as `examples/illustration-supabase.md`
  and says it is invented.
- `make test`, the one test command: the skill eval, the manifest and README contract tests, and
  `tests/test_fixture.py`, which starts the fixture and replays each hole the sample report names.
- `.claude-plugin/icon.png`, `.github/social-preview.png`, `CODEOWNERS`, Dependabot for actions.

### CI

- CI runs `make test` on every push and pull request.
- `npx skills@1.9.0 add . --list` must find the skill.
- `claude plugin validate . --strict` runs on a pinned Claude Code, unconditionally.
- Every action is pinned to a commit sha.

## [0.2.0] - 2026-09-07

Renamed from `lockpatch` to `secure-my-app`, and the docs cut down to something you can read in a
minute. No behaviour changed: the same 65 controls, the same ladder, the same paired test.

### Changed

- **Renamed.** `lockpatch` said nothing to someone who had not already been told what it was.
  `secure-my-app` says it. The GitHub repo moved to `Aboudjem/secure-my-app`; the old URL
  redirects. The command is now `/secure-my-app`, the install is
  `claude plugin install secure-my-app@10x`, and the state directory the skill writes is
  `.secure-my-app/`.
- **The README is 99 lines, down from 239.** Three bullets tell you what it does, one sample
  report shows you what you get, one table lists the seven groups. Everything longer moved into
  `docs/`. The four translations track it at the same length.
- **The docs got shorter without losing anything load-bearing.** `faq.md` 264 to 157,
  `quickstart.md` 189 to 145, `limits.md` 212 to 154, `editors.md` 95 to 83. All 65 controls
  stayed in `controls.md`.
- **New artwork.** The social card now shows both halves of the paired test in one picture: the
  attacker's request going 200 to 403, and a real user's request staying 200 throughout. That is
  the whole product in one image, which the old ladder drawing was not.
- **Naming honesty.** The new name sounds like a promise of safety and this tool does not make
  one, so the README now leads its Good to know section with the gate's real third label,
  `NOTHING CONFIRMED HERE`, and the fact that it is never printed without its coverage counts.

### Added

- `P13`, untrusted bytes are never deserialized into objects. That takes the catalogue from 64
  controls to 65.
- The canonical vulnerability names are now searchable in the catalogue: IDOR and BOLA on `R4`,
  cross-tenant access on `R5`, mass assignment on `R6`, SSRF on `P6`, logging and monitoring
  failures on `V5`.
- `.github/workflows/no-ai-attribution.yml`, which fails the build if an AI attribution trailer
  reaches a commit message. A local hook cannot cover `rebase`, `--no-verify`, or anything
  composed on GitHub's servers.

### Fixed

- The link checker tried to fetch `http://127.0.0.1:22`, which is the SSRF example in `P6`, not a
  link. Loopback, RFC 1918, link-local and the RFC 2606 example domains are now excluded.

## [0.1.0] - 2026-09-06

First public release. A security audit that has to show its work: every finding carries the
request that proves it, and no fix is called done until that request fails and your own login
still works.

### Added

- **The skill** (`skills/secure-my-app/SKILL.md`): `/secure-my-app` reads the app, maps what an
  unauthenticated stranger can reach, and writes its whole audit into `.secure-my-app/` in the
  project. It runs in two phases. **AUDIT** finds and proves. **FIX** applies, one approval at a
  time, and re-verifies. The skill is Markdown only: no runtime dependency, no API key, no
  telemetry, and no network call of its own.
- **Proof or it is not a finding.** Every finding ships with the exact request that demonstrates
  it (method, path, headers, body, and the response that came back), written so a human can paste
  it into a terminal and watch it happen. A hole nobody could reproduce is reported as a suspicion
  with that word on it, never as a finding.
- **A fix is not applied until the human approves it, and not closed until it is re-run.**
  secure-my-app shows the diff for one finding, waits, applies only what was approved, then runs two
  commands: the proof request, which must now fail, and the user's own authenticated path, which
  must still work. A fix that closes the hole and locks the owner out is a broken fix, and the
  second check is what catches it.
- **Secrets by location, never by value.** When the finding is an exposed credential, the report
  names where it lives (the file, the line, the environment variable) and prints a redacted form.
  The raw value is never written into the report or anywhere else under `.secure-my-app/`.
- **`.secure-my-app/` is gitignored on creation**, and `.gitignore` is created when the project has
  none. A findings report is a map of what still works, so committing one publishes the hole
  before the fix lands.
- **Reference files** under `skills/secure-my-app/references/`, loaded only when the audit reaches
  the area they cover, so the skill body stays short and the depth is there when it is needed.
- **Evals and tests in CI**: `evals/check_skill.py` (deterministic assertions on the skill body,
  written before the skill existed and run once against the missing file to record RED),
  `tests/test_manifests.py` (manifest validity, version parity across the four manifests and the
  changelog, required files, README link and asset resolution, i18n parity), the recorded cold
  baseline in `evals/RED-baseline.md`, and the behavioral rubrics in `evals/scenarios.md`.
- **Docs**: quickstart, install in your editor, honest limits, and an FAQ.
- **README in five languages** (English, simplified Chinese, Japanese, Spanish, French) with
  absolute asset URLs and a "may lag" note in each translation.
- **Packaging**: `.claude-plugin/plugin.json` and `marketplace.json`, plus the `.cursor-plugin`
  and `.copilot-plugin` mirrors, listed in the
  [10x marketplace](https://github.com/Aboudjem/10x) and installable with
  `npx skills add Aboudjem/secure-my-app`.
