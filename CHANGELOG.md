# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-06

First public release. A security audit that has to show its work: every finding carries the
request that proves it, and no fix is called done until that request fails and your own login
still works.

### Added

- **The skill** (`skills/lockpatch/SKILL.md`): `/lockpatch` reads the app, maps what an
  unauthenticated stranger can reach, and writes its whole audit into `.lockpatch/` in the
  project. It runs in two phases. **AUDIT** finds and proves. **FIX** applies, one approval at a
  time, and re-verifies. The skill is Markdown only: no runtime dependency, no API key, no
  telemetry, and no network call of its own.
- **Proof or it is not a finding.** Every finding ships with the exact request that demonstrates
  it (method, path, headers, body, and the response that came back), written so a human can paste
  it into a terminal and watch it happen. A hole nobody could reproduce is reported as a suspicion
  with that word on it, never as a finding.
- **A fix is not applied until the human approves it, and not closed until it is re-run.**
  lockpatch shows the diff for one finding, waits, applies only what was approved, then runs two
  commands: the proof request, which must now fail, and the user's own authenticated path, which
  must still work. A fix that closes the hole and locks the owner out is a broken fix, and the
  second check is what catches it.
- **Secrets by location, never by value.** When the finding is an exposed credential, the report
  names where it lives (the file, the line, the environment variable) and prints a redacted form.
  The raw value is never written into the report or anywhere else under `.lockpatch/`.
- **`.lockpatch/` is gitignored on creation**, and `.gitignore` is created when the project has
  none. A findings report is a map of what still works, so committing one publishes the hole
  before the fix lands.
- **Reference files** under `skills/lockpatch/references/`, loaded only when the audit reaches
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
  `npx skills add Aboudjem/lockpatch`.
