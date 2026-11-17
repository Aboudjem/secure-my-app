<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
    <img src="assets/hero-light.svg" alt="secure-my-app: find what a stranger can take from your app, then close it and prove it closed." width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml/badge.svg" alt="validate"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
</p>

<p align="center">
  <b>English</b> · <a href="READMEs/zh-CN.md">简体中文</a> · <a href="READMEs/ja.md">日本語</a> · <a href="READMEs/es.md">Español</a> · <a href="READMEs/fr.md">Français</a>
</p>

<p align="center">
  <strong>Find what a stranger can take from your app. Then close it and prove it closed.</strong>
</p>

A skill for coding agents. It reads your whole app and runs 65 named security checks.
Every hole it reports comes with the command that proves it.

## Install

**Claude Code.** Add the marketplace, then install the plugin.

```bash
claude plugin marketplace add Aboudjem/10x
```

```bash
claude plugin install secure-my-app@10x
```

**Any other agent.** One command.

```bash
npx skills add Aboudjem/secure-my-app
```

**Then run it.** Open your project in the agent and say:

```text
secure my app before I launch
```

That sentence matches the skill's description, so any agent that loads skills picks it up.
On Codex CLI 0.169.0 it started the skill on 2026-11-17. Each agent also has a short trigger:

| Agent | Short trigger |
| --- | --- |
| Claude Code | `/secure-my-app:secure-my-app` |
| Codex CLI | `$secure-my-app` |

It asks three questions, reads your code, and writes `.secure-my-app/report.md`. Then it stops.
Nothing in your app changes until you approve one fix.

### Works with

| Agent | What ran | Tested |
| --- | --- | --- |
| Claude Code 2.1.326 | Plugin loaded, full run on the fixture, [report written](examples/sample-report.md) | 2026-11-17 |
| Codex CLI 0.169.0 | `npx skills add -a codex`, full run on the fixture, [report written](examples/sample-report-codex.md) | 2026-11-17 |

Documented, not tested: Cursor, GitHub Copilot, Gemini CLI, OpenCode, Windsurf, Zed, Continue.dev and Kimi Code CLI.
The skills CLI installs the same files for them. No run on those agents is recorded here.
Per-agent paths are in [Install in your editor](docs/editors.md).

## What you get

A report that opens with the verdict, then the three things to do first.
This is the top of a real one, written on 2026-11-17:

```text
VERDICT: DO NOT LAUNCH   coverage 21 checked / 2 unproven / 42 n/a   [static + live: 127.0.0.1:4310]
findings: 3 critical  2 high  6 medium  0 low   scan: gitleaks yes, semgrep installed but not run, osv-scanner no, trufflehog no
DO FIRST
1. K3  Replace the session secret committed in server.js with a new one read from the environment
2. D3  Replace SHA-256 password hashing with a real password hash, then reset every password
3. R10 Put a sign-in check and an admin role check on GET /admin/export
```

Below the header, every finding has the same fields. This one is from the same report:

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

- **Where it comes from.** The app is [`examples/vulnerable-app/`](examples/vulnerable-app/README.md), a small API with holes left in on purpose.
- **The whole report.** [`examples/sample-report.md`](examples/sample-report.md) is the file that run wrote, unedited. The second block above is shortened from it.
- **`PROOF`** is a command and the output it gave, with secrets cut short.
- **`VERIFY`** is the command whose output must change before a fix counts.
- **Second run.** `.secure-my-app/surface.json` lets the next run say what was fixed, what came back and what is new.

For a Supabase and Next.js shape, read the [illustration](examples/illustration-supabase.md). That one is invented and says so.

### Try it on the broken app first

Clone this repo, then start the fixture:

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

65 controls in seven groups, in the order an attacker tries them ([full catalogue](docs/controls.md)).

| Group      | Covers                                                           |
| ---------- | ---------------------------------------------------------------- |
| KEYS (8)   | Secrets in the repo, key exposure, key scope, rotation           |
| DOOR (9)   | Login, sessions, cookies, password storage, tokens               |
| ROOMS (10) | Row level security, IDOR, tenant isolation, mass assignment      |
| PIPES (13) | Injection, XSS, CSRF, SSRF, CORS, redirects, webhooks, headers   |
| VAULT (8)  | Encryption at rest, response shape, error leakage, logs, backups |
| FLOOR (10) | Rate limits, bots, uploads, price tampering, AI features         |
| SUPPLY (7) | Dependencies, lockfiles, install scripts, CI permissions         |

## How it works

- **No proof, no finding.** What it cannot settle comes back `UNPROVEN`, never as a pass.
- **You approve each fix.** Nothing in your repo changes until you say yes to that one fix. There is no batch mode.
- **Every fix is proven twice.** The attacker's request now fails, and your own login still works.
- **A fix that blocks everybody is reverted.** A patch that returns `403` to all users closes the hole and closes the product.
- **It leaves history and keys alone.** It never rewrites git history and never rotates a credential. It writes the runbook, you run it.

## Proof

Every number on this page comes from a command you can run in a clone.

The tests:

```bash
make test
```

```text
79/79 checks passed for skills/secure-my-app/SKILL.md
138/138 checks passed
33/33 checks passed
```

| Suite                     | What it checks                                                                 |
| ------------------------- | ------------------------------------------------------------------------------ |
| `evals/check_skill.py`    | The skill text: the ladder, the verdict line, the RLS rules, the report header |
| `tests/test_manifests.py` | Manifests, one version everywhere, required files, this README                 |
| `tests/test_fixture.py`   | Starts the fixture and replays the request behind each sample finding          |

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
secure-my-app reads the whole app and finds the defence nobody wrote.

### Do I need gitleaks or semgrep?

No. It uses them when they are installed and names them in the header.
A missing scanner never turns a check into a pass.

More answers are in the [full FAQ](docs/faq.md).

## Limits

- **It is not a penetration test.** Nobody signs the report. It is not a compliance audit either.
- **It sees your repository, not your system.** Cloud settings, DNS, laptops and people are outside it.
- **Two runs can differ.** The rating is a fixed lookup. The scan is an agent's judgment.
- **One recorded run.** The sample is from one small fixture. No run on a production app is published here.
- **Without a URL it proves less.** Most access checks then come back `UNPROVEN`.
- **Live probes are bounded.** About 30 requests, one host you own, no `DELETE`, no load testing.

Everything it does not promise is in [Honest limits](docs/limits.md).

## Learn more

- [Quickstart](docs/quickstart.md), a first run start to finish
- [A report from a real run](examples/sample-report.md), eleven findings and the unproven appendix
- [Install in your editor](docs/editors.md) · [Contributing](CONTRIBUTING.md) · [The skill itself](skills/secure-my-app/SKILL.md)

---

<sub>Built by <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT.
Control catalogue, severity matrix and RLS semantics re-derived from the PostgreSQL, Supabase and OWASP primary docs, 2026.
Sibling of <a href="https://github.com/Aboudjem/loopify">loopify</a> and <a href="https://github.com/Aboudjem/goalify">goalify</a>. <a href="https://github.com/Aboudjem/secure-my-app/issues">Spot a gap?</a></sub>
