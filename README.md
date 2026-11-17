<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
    <img src="assets/hero-light.svg" alt="secure-my-app: what can a stranger take? Three points: fixes proven closed, proof for each hole, no surprise changes. Alice asks for bob's invoice: 200 before the fix, 404 after it." width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml/badge.svg" alt="validate"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
</p>

<p align="center">
  <b>English</b> · <a href="READMEs/zh-CN.md">简体中文</a> · <a href="READMEs/ja.md">日本語</a> · <a href="READMEs/es.md">Español</a> · <a href="READMEs/fr.md">Français</a>
</p>

<p align="center">
  <strong>Find what a stranger can take from your app.</strong>
</p>

It runs 65 named checks and shows the proof for each hole it reports.

| Fixes proven closed | Proof for each hole | No surprise changes |
|:--|:--|:--|
| A fix counts only when its VERIFY output changes. All 11 sample findings have one. | Each finding shows its proof. `make test` replays the proof behind all 11 sample findings. | It writes a report and stops. Each fix waits for your yes. |

**Works with:** any agent that reads skills. Full runs tested: Claude Code, Codex CLI. It is a Markdown skill, so it is not tied to one model.

```bash
npx skills add Aboudjem/secure-my-app -g
# then, in your agent: secure my app before I launch
```

## What you get

The top of a real report, from a run on this repo's small test app on 2026-11-17:

```text
VERDICT: DO NOT LAUNCH   coverage 21 checked / 2 unproven / 42 n/a   [static + live: 127.0.0.1:4310]
findings: 3 critical  2 high  6 medium  0 low   scan: gitleaks yes, semgrep installed but not run, osv-scanner no, trufflehog no
DO FIRST
1. K3  Replace the session secret committed in server.js with a new one read from the environment
2. D3  Replace SHA-256 password hashing with a real password hash, then reset every password
3. R10 Put a sign-in check and an admin role check on GET /admin/export
```

Can one user read another's invoice by changing a number in the URL? Here alice reads bob's:

```text
HIGH R4 Any signed-in user can read any invoice by changing the number in the URL

WHERE   server.js:83-92 (the lookup is line 89)
PROOF   [static]   server.js:89   const invoice = invoices.find((i) => i.id === id);
        [executed] alice (team_1) reads bob's invoice:
                   GET /api/invoices/1042 -> 200 {"id":1042,"owner":"u_2","team":"team_2",...}
        [executed] the list route scopes correctly: alice GET /api/invoices -> 200, invoice 1041 only
IMPACT  One team's customers, billing contacts, amounts and IBAN digits, readable by the other team.
FIX     const invoice = invoices.find((i) => i.id === id && i.owner === user.id);
VERIFY  alice:  GET /api/invoices/1042 (bob's)   -> 404 "no such invoice"
        alice:  GET /api/invoices/1041 (hers)    -> 200, the invoice
STATUS  OPEN
```

**What it is:** a skill that looks for security holes in your app.
**When to use it:** before you launch, or before strangers can sign up.
**What you get:** one report with the proof for each hole. Your code stays as it was.

**Limit:** it is not a penetration test (a paid attack by an expert). Without a live URL, most access checks stay `UNPROVEN`.

## Install

**Pick your agent.** Each command installs secure-my-app for all your projects.

<p align="center">
  <a href="#install-claude-code"><img src="https://img.shields.io/badge/Claude_Code-D97757?style=for-the-badge&logo=claude&logoColor=white" alt="Claude Code"></a>
  <a href="#install-codex"><img src="https://img.shields.io/badge/Codex-000000?style=for-the-badge&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyBmaWxsPSJ3aGl0ZSIgcm9sZT0iaW1nIiB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI%2BPHRpdGxlPk9wZW5BSTwvdGl0bGU%2BPHBhdGggZD0iTTIyLjI4MTkgOS44MjExYTUuOTg0NyA1Ljk4NDcgMCAwIDAtLjUxNTctNC45MTA4IDYuMDQ2MiA2LjA0NjIgMCAwIDAtNi41MDk4LTIuOUE2LjA2NTEgNi4wNjUxIDAgMCAwIDQuOTgwNyA0LjE4MThhNS45ODQ3IDUuOTg0NyAwIDAgMC0zLjk5NzcgMi45IDYuMDQ2MiA2LjA0NjIgMCAwIDAgLjc0MjcgNy4wOTY2IDUuOTggNS45OCAwIDAgMCAuNTExIDQuOTEwNyA2LjA1MSA2LjA1MSAwIDAgMCA2LjUxNDYgMi45MDAxQTUuOTg0NyA1Ljk4NDcgMCAwIDAgMTMuMjU5OSAyNGE2LjA1NTcgNi4wNTU3IDAgMCAwIDUuNzcxOC00LjIwNTggNS45ODk0IDUuOTg5NCAwIDAgMCAzLjk5NzctMi45MDAxIDYuMDU1NyA2LjA1NTcgMCAwIDAtLjc0NzUtNy4wNzI5em0tOS4wMjIgMTIuNjA4MWE0LjQ3NTUgNC40NzU1IDAgMCAxLTIuODc2NC0xLjA0MDhsLjE0MTktLjA4MDQgNC43NzgzLTIuNzU4MmEuNzk0OC43OTQ4IDAgMCAwIC4zOTI3LS42ODEzdi02LjczNjlsMi4wMiAxLjE2ODZhLjA3MS4wNzEgMCAwIDEgLjAzOC4wNTJ2NS41ODI2YTQuNTA0IDQuNTA0IDAgMCAxLTQuNDk0NSA0LjQ5NDR6bS05LjY2MDctNC4xMjU0YTQuNDcwOCA0LjQ3MDggMCAwIDEtLjUzNDYtMy4wMTM3bC4xNDIuMDg1MiA0Ljc4MyAyLjc1ODJhLjc3MTIuNzcxMiAwIDAgMCAuNzgwNiAwbDUuODQyOC0zLjM2ODV2Mi4zMzI0YS4wODA0LjA4MDQgMCAwIDEtLjAzMzIuMDYxNUw5Ljc0IDE5Ljk1MDJhNC40OTkyIDQuNDk5MiAwIDAgMS02LjE0MDgtMS42NDY0ek0yLjM0MDggNy44OTU2YTQuNDg1IDQuNDg1IDAgMCAxIDIuMzY1NS0xLjk3MjhWMTEuNmEuNzY2NC43NjY0IDAgMCAwIC4zODc5LjY3NjVsNS44MTQ0IDMuMzU0My0yLjAyMDEgMS4xNjg1YS4wNzU3LjA3NTcgMCAwIDEtLjA3MSAwbC00LjgzMDMtMi43ODY1QTQuNTA0IDQuNTA0IDAgMCAxIDIuMzQwOCA3Ljg3MnptMTYuNTk2MyAzLjg1NThMMTMuMTAzOCA4LjM2NCAxNS4xMTkyIDcuMmEuMDc1Ny4wNzU3IDAgMCAxIC4wNzEgMGw0LjgzMDMgMi43OTEzYTQuNDk0NCA0LjQ5NDQgMCAwIDEtLjY3NjUgOC4xMDQydi01LjY3NzJhLjc5Ljc5IDAgMCAwLS40MDctLjY2N3ptMi4wMTA3LTMuMDIzMWwtLjE0Mi0uMDg1Mi00Ljc3MzUtMi43ODE4YS43NzU5Ljc3NTkgMCAwIDAtLjc4NTQgMEw5LjQwOSA5LjIyOTdWNi44OTc0YS4wNjYyLjA2NjIgMCAwIDEgLjAyODQtLjA2MTVsNC44MzAzLTIuNzg2NmE0LjQ5OTIgNC40OTkyIDAgMCAxIDYuNjgwMiA0LjY2ek04LjMwNjUgMTIuODYzbC0yLjAyLTEuMTYzOGEuMDgwNC4wODA0IDAgMCAxLS4wMzgtLjA1NjdWNi4wNzQyYTQuNDk5MiA0LjQ5OTIgMCAwIDEgNy4zNzU3LTMuNDUzN2wtLjE0Mi4wODA1TDguNzA0IDUuNDU5YS43OTQ4Ljc5NDggMCAwIDAtLjM5MjcuNjgxM3ptMS4wOTc2LTIuMzY1NGwyLjYwMi0xLjQ5OTggMi42MDY5IDEuNDk5OHYyLjk5OTRsLTIuNTk3NCAxLjQ5OTctMi42MDY3LTEuNDk5N1oiLz48L3N2Zz4%3D" alt="Codex"></a>
  <a href="#install-cursor"><img src="https://img.shields.io/badge/Cursor-3B3B3B?style=for-the-badge&logo=cursor&logoColor=white" alt="Cursor"></a>
  <a href="#install-gemini-cli"><img src="https://img.shields.io/badge/Gemini_CLI-1A73E8?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini CLI"></a>
  <a href="#install-github-copilot"><img src="https://img.shields.io/badge/GitHub_Copilot-24292F?style=for-the-badge&logo=githubcopilot&logoColor=white" alt="GitHub Copilot"></a>
  <a href="#install-opencode"><img src="https://img.shields.io/badge/OpenCode-4A4A4A?style=for-the-badge&logo=opencode&logoColor=white" alt="OpenCode"></a>
</p>

<a id="install-claude-code"></a>**Claude Code**, tested. Installs for all your projects:

```bash
claude plugin marketplace add Aboudjem/10x && claude plugin install secure-my-app@10x
```

<a id="install-codex"></a>**Codex**, tested:

```bash
npx skills add Aboudjem/secure-my-app -g -a codex
```

<a id="install-cursor"></a>**Cursor**, install tested:

```bash
npx skills add Aboudjem/secure-my-app -g -a cursor
```

<a id="install-gemini-cli"></a>**Gemini CLI**, install tested:

```bash
npx skills add Aboudjem/secure-my-app -g -a gemini-cli
```

<a id="install-github-copilot"></a>**GitHub Copilot**, install tested:

```bash
npx skills add Aboudjem/secure-my-app -g -a github-copilot
```

<a id="install-opencode"></a>**OpenCode**, install tested:

```bash
npx skills add Aboudjem/secure-my-app -g -a opencode
```

Only this project: drop `-g`. Another agent: see its `-a` code in [Install in your editor](docs/editors.md).

**Your first command.** Open your project in your agent and say:

```text
secure my app before I launch
```

1. It asks three questions.
2. It reads your code and writes `.secure-my-app/report.md`.
3. It stops. Nothing changes until you say yes to one fix.

That sentence matches the skill's description, so any agent that loads skills picks it up.
Each agent also has a short trigger:

| Agent | Short trigger |
| --- | --- |
| Claude Code | `/secure-my-app:secure-my-app` |
| Codex CLI | `$secure-my-app` |

### Works with

| Agent | What ran | Tested |
| --- | --- | --- |
| Claude Code 2.1.326 | Plugin loaded, full run on the fixture, [report written](examples/sample-report.md) | 2026-11-17 |
| Codex CLI 0.169.0 | `npx skills add -a codex`, full run on the fixture, [report written](examples/sample-report-codex.md) | 2026-11-17 |
| Claude Code (install only) | The plugin command above, into an empty home folder: installed with scope user | 2026-11-17 |
| Cursor, Gemini CLI, GitHub Copilot, OpenCode (install only) | The `-g -a` command above, into an empty home folder: files in `~/.agents/skills/secure-my-app` | 2026-11-17 |

"Install only" means the files landed where the agent reads them. No full run on those agents is recorded here.
Documented, not tested: Windsurf, Zed, Continue.dev and Kimi Code CLI.
Per-agent paths are in [Install in your editor](docs/editors.md).

## Read the report

The report opens with the verdict, then the three things to do first.
Below the header, every finding has the same fields, like the R4 block at the top of this page.

- **Where it comes from.** The app is [`examples/vulnerable-app/`](examples/vulnerable-app/README.md), a small API with holes left in on purpose.
- **The whole report.** [`examples/sample-report.md`](examples/sample-report.md) is the file that run wrote, unedited. The R4 block above is shortened from it.
- **`PROOF`** is the evidence. `[static]` is a line read in your code. `[executed]` is a command or request that ran, and the output it gave, with secrets cut short.
- **`VERIFY`** is the command whose output must change before a fix counts.
- **Second run.** `.secure-my-app/surface.json` lets the next run say what was fixed, what came back and what is new.

For an app built with Supabase and Next.js, read the [illustration](examples/illustration-supabase.md). That one is invented and says so.

### Try it on the broken app first

Clone this repo, then start the test app (the fixture):

```bash
node examples/vulnerable-app/server.js
```

Open your agent in `examples/vulnerable-app/` and type the line for your agent:

```text
/secure-my-app:secure-my-app --report-only --live http://127.0.0.1:4310
```

In Codex CLI, start the same line with `$secure-my-app` instead.

The [fixture README](examples/vulnerable-app/README.md) has the three answers and two test accounts.

## What it checks

You launch on Monday. You built fast, maybe with an agent.
Can one signed-in user read another user's data? This checks, and shows you the proof.

65 controls in seven groups, in the order an attacker tries them ([full catalogue](docs/controls.md)).

| Group      | Covers                                                           |
| ---------- | ---------------------------------------------------------------- |
| KEYS (8)   | Secrets in the repo, key exposure, key scope, rotation           |
| DOOR (9)   | Login, sessions, cookies, password storage, tokens               |
| ROOMS (10) | Row level security, IDOR (reading records by ID), tenant isolation, mass assignment |
| PIPES (13) | Injection, XSS, CSRF, SSRF, CORS, redirects, webhooks, headers   |
| VAULT (8)  | Encryption at rest, response shape, error leakage, logs, backups |
| FLOOR (10) | Rate limits, bots, uploads, price tampering, AI features         |
| SUPPLY (7) | Dependencies, lockfiles, install scripts, CI permissions         |

## How it works

The skill's own summary: **Find what a stranger can take from your app. Then close it and prove it closed.**
The closing part starts only when you say yes to a fix. A fix counts only when that same request fails.

- **No proof, no finding.** What it cannot settle comes back `UNPROVEN`, never as a pass.
- **You approve each fix.** Nothing in your repo changes until you say yes to that one fix. There is no batch mode.
- **Every fix is proven twice.** The attacker's request now fails, and your own login still works.
- **A fix that blocks everybody is reverted.** A patch that returns `403` to all users closes the hole, but then nobody can use the app.
- **It leaves history and keys alone.** It never rewrites git history and never rotates a credential. It writes the steps (a runbook), and you run them.

## Proof

Every number on this page comes from a command you can run in a clone.

The tests:

```bash
make test
```

```text
79/79 checks passed for skills/secure-my-app/SKILL.md
152/152 checks passed
54/54 checks passed
```

| Suite                     | What it checks                                                                 |
| ------------------------- | ------------------------------------------------------------------------------ |
| `evals/check_skill.py`    | The skill text: the ladder, the verdict line, the RLS rules, the report header |
| `tests/test_manifests.py` | Manifests, one version everywhere, required files, this README                 |
| `tests/test_fixture.py`   | Starts the fixture and replays the proof behind each of the 11 sample findings |

The `VERIFY` lines in the sample report, one per finding:

```bash
grep -c '^VERIFY' examples/sample-report.md
```

```text
11
```

The sample run changed nothing: its header says `Nothing in the app was changed.`

The control count:

```bash
grep -c '^| [KDRPVFS][0-9]' skills/secure-my-app/references/controls.md
```

```text
65
```

CI runs `make test` on every push and pull request.
The tests cover the skill text and the fixture. They cannot tell you what a run will find in your app.

## FAQ

### Is it safe to run on my project?

Yes. It only reads until you approve a fix. The one thing it writes is the report under `.secure-my-app/`.

### Will it change my code?

Not on its own. Each fix needs your yes, gets a checkpoint commit first, and is reverted if your own request stops working.

### Does it send my code anywhere?

It makes no network call of its own. With a URL and your yes, it sends about 30 requests to that one host.
Your agent still sends context to its own model provider, as it does for any task.

### Does a clean report mean my app is secure?

No. The third verdict is `NOTHING CONFIRMED HERE`, always printed with its coverage counts.
It means nothing reached critical or high in what the run could check.

### How is it different from `/security-review`?

`/security-review` reads a diff and finds the flaw in code you wrote.
secure-my-app reads the whole app and finds the protection nobody wrote.

### Do I need gitleaks or semgrep?

No. It uses them when they are installed and names them in the header.
A missing scanner never turns a check into a pass.

More answers are in the [full FAQ](docs/faq.md).

## Limits

- **It is not a penetration test** (a paid attack by an expert). Nobody signs the report. It is not a compliance audit either.
- **It sees your repository, not your system.** Cloud settings, DNS, laptops and people are outside it.
- **Two runs can differ.** The rating is a fixed lookup. The scan is an agent's judgment.
- **One recorded run.** The only published run is on a small test app. No run on a production app is published here.
- **Without a URL it proves less.** Without a live URL, most access checks stay `UNPROVEN`.
- **Live checks are limited.** About 30 requests, one host you own, no `DELETE`, no load testing.

Everything it does not promise is in [Honest limits](docs/limits.md).

## Learn more

- [Quickstart](docs/quickstart.md), a first run start to finish
- [A report from a real run](examples/sample-report.md), eleven findings and the unproven appendix
- [Install in your editor](docs/editors.md) · [Contributing](CONTRIBUTING.md) · [The skill itself](skills/secure-my-app/SKILL.md)

---

<sub>Built by <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT.
Control catalogue, severity matrix and RLS semantics re-derived from the PostgreSQL, Supabase and OWASP primary docs, 2026.
Sibling of <a href="https://github.com/Aboudjem/loopify">loopify</a> and <a href="https://github.com/Aboudjem/goalify">goalify</a>. <a href="https://github.com/Aboudjem/secure-my-app/issues">Spot a gap?</a></sub>
