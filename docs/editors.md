# Install lockpatch in your editor

lockpatch is one Agent Skill: a `SKILL.md` with `name` and `description` frontmatter, Markdown
underneath, and a `references/` directory beside it that the skill loads on demand. There is no
server to run, no binary to compile, and no dependency to install. Claude Code has a first-party
path; every other agent installs the same directory through the skills CLI.

## Claude Code

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install lockpatch@10x
```

Then say "lockpatch this before I launch" or run `/lockpatch`.

## Any other agent, in one line

```bash
npx skills add Aboudjem/lockpatch -a <agent>
```

The agent codes below were read from the supported-agents table in
[vercel-labs/skills](https://github.com/vercel-labs/skills#supported-agents), along with the
directory each agent reads. That table lists 77 codes in all, so if yours is not here it is almost
certainly in the table.

| Agent | `-a` code | Project path | Global path |
| --- | --- | --- | --- |
| Claude Code | `claude-code` | `.claude/skills/` | `~/.claude/skills/` |
| Cursor | `cursor` | `.agents/skills/` | `~/.cursor/skills/` |
| Codex | `codex` | `.agents/skills/` | `~/.codex/skills/` |
| GitHub Copilot | `github-copilot` | `.agents/skills/` | `~/.copilot/skills/` |
| Gemini CLI | `gemini-cli` | `.agents/skills/` | `~/.gemini/skills/` |
| OpenCode | `opencode` | `.agents/skills/` | `~/.config/opencode/skills/` |
| Windsurf | `windsurf` | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |
| Zed | `zed` | `.agents/skills/` | `~/.agents/skills/` |
| Continue.dev | `continue` | `.agents/skills/` | `~/.continue/skills/` |
| Kimi Code CLI | `kimi-code-cli` | `.agents/skills/` | `~/.agents/skills/` |

So, for Cursor:

```bash
npx skills add Aboudjem/lockpatch -a cursor
```

For VS Code with GitHub Copilot, the code is the Copilot one:

```bash
npx skills add Aboudjem/lockpatch -a github-copilot
```

Three flags worth knowing:

- `-g` installs to the global path in the table instead of the project one.
- `-y` skips the confirmation prompts, which is what you want in a script.
- `--list` prints what a repository offers and installs nothing. For this repo it reports one skill.

## Copy it in by hand

The skill is a directory. Copying it works anywhere, and it is the fallback if the CLI does not know
your agent:

```bash
git clone https://github.com/Aboudjem/lockpatch
cp -R lockpatch/skills/lockpatch ~/.claude/skills/
```

Swap the destination for your agent's path from the table above. Copy the whole directory, not just
`SKILL.md`: everything under `references/` is loaded by relative path during a run, and the control
catalogue is where the DETECT and VERIFY commands live. Nothing else in the repository is needed at
run time.

## What changes outside Claude Code

The skill itself is portable. The ladder, the three outcomes, the evidence tiers, the severity
matrix, the gate, the paired test and all 65 controls are ordinary Markdown that any agent can read.

What changes is the tooling underneath, and lockpatch degrades honestly rather than silently:

- **An agent with no shell** cannot run the DETECT commands. Those controls come back `UNPROVEN`, each
  with its command written out as a tier 3 recipe for you to run. They never come back `PASS`.
- **An agent with no network** cannot run the live probe phase. The report header says `static only`,
  and most of the ROOMS group is `UNPROVEN` rather than passed.
- **An agent with no file write** still produces the on-screen report. You lose `.lockpatch/report.md`
  and `.lockpatch/surface.json`, which means the next run cannot be a diff.

All three are still useful runs. None of them is allowed to report a `PASS` it did not earn, and the
coverage line on the gate tells you which kind of run you are reading.

## Next

- [Quickstart](quickstart.md), a first run end to end
- [The control catalogue](controls.md), all 65 controls in seven groups
- [Honest limits](limits.md), what a clean run does and does not prove
