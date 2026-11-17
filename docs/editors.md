# Install secure-my-app in your editor

One Agent Skill: a `SKILL.md` with frontmatter, Markdown underneath, and a `references/` directory
beside it. No server, no binary, no dependency. Claude Code has a first-party path; every other agent
installs the same directory through the skills CLI.

## Claude Code

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install secure-my-app@10x
```

Then say "secure my app before I launch", or run `/secure-my-app:secure-my-app`.

## Any other agent

```bash
npx skills add Aboudjem/secure-my-app -g -a <agent>
```

Replace `<agent>` with a code from this table, read from the supported-agents table in
[vercel-labs/skills](https://github.com/vercel-labs/skills#supported-agents). That table lists 77 codes
in all, so if yours is missing here it is almost certainly there.

| Agent | `-a` code | Project path | Global path |
| --- | --- | --- | --- |
| Claude Code | `claude-code` | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `cursor` | `.agents/skills/` | `~/.agents/skills/` |
| Codex | `codex` | `.agents/skills/` | `~/.agents/skills/` |
| GitHub Copilot | `github-copilot` | `.agents/skills/` | `~/.agents/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` | `~/.agents/skills/` |
| OpenCode | `opencode` | `.agents/skills/` | `~/.agents/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |
| Zed | `zed` | `.agents/skills/` | `~/.agents/skills/` |
| Continue.dev | `continue` | `.agents/skills/` | `~/.continue/skills/` |
| Kimi Code CLI | `kimi-code-cli` | `.agents/skills/` | `~/.agents/skills/` |

So for Cursor, and for VS Code with GitHub Copilot:

```bash
npx skills add Aboudjem/secure-my-app -g -a cursor
npx skills add Aboudjem/secure-my-app -g -a github-copilot
```

`-g` installs to the global path, for all your projects. Drop `-g` to install for this project only. Add `-y` to skip the prompts in a
script, or `--list` to print what a repository offers and install nothing. For this repo, `--list`
reports one skill.

Then open your project and say "secure my app before I launch". In Codex CLI you can also type
`$secure-my-app`. Both started the skill in Codex CLI 0.169.0 on 2026-11-17.

## Copy it in by hand

The fallback if the CLI does not know your agent:

```bash
git clone https://github.com/Aboudjem/secure-my-app
cp -R secure-my-app/skills/secure-my-app ~/.claude/skills/
```

Swap the destination for your agent's path from the table. Copy the whole directory, not just
`SKILL.md`, because everything under `references/` is loaded by relative path during a run. Nothing
else in the repository is needed at run time.

## What changes outside Claude Code

The skill is portable. The ladder, the three outcomes, the evidence tiers, the severity matrix, the
gate, the paired test and all 65 controls are ordinary Markdown that any agent can read. What changes
is the tooling underneath, and it degrades honestly rather than silently.

- An agent with no shell cannot run the DETECT commands, so those controls come back `UNPROVEN`, each
  with its command written out as a tier 3 recipe for you to run. They never come back `PASS`.
- An agent with no network cannot run the live probes, so the report header says `static only` and most
  of the ROOMS group is `UNPROVEN` rather than passed.
- An agent with no file write still prints the report. You lose `.secure-my-app/report.md` and
  `.secure-my-app/surface.json`, so the next run cannot be a diff.

All three are still useful runs. None may report a `PASS` it did not earn, and the coverage line on the
gate tells you which kind of run you are reading.

## Next

- [Quickstart](quickstart.md), a first run end to end
- [The control catalogue](controls.md), all 65 controls in seven groups
- [Honest limits](limits.md), what a clean run does and does not prove
