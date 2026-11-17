#!/usr/bin/env python3
"""
Manifest + contract tests for secure-my-app (a release gate; runs in CI).

  1. All four manifests parse and carry the required fields, and every one of them names
     the plugin "secure-my-app".
  2. One version, everywhere: .claude-plugin/plugin.json, .claude-plugin/marketplace.json,
     .cursor-plugin/plugin.json, .copilot-plugin/plugin.json, the latest CHANGELOG.md entry
     and SKILL.md's metadata.version. The two editor mirrors must otherwise match
     .claude-plugin/plugin.json field for field.
  3. Every required repo file exists.
  4. skills/secure-my-app/SKILL.md has frontmatter with name, description, license and a quoted
     metadata.version, and that version matches plugin.json.
  5. Every relative link in README.md resolves to a file that exists.
  6. Every asset README.md references resolves to a file that exists.
  7. Every references/*.md path SKILL.md mentions exists on disk.
  8. READMEs/{es,fr,ja,zh-CN}.md exist and carry the may-lag marker.
  9. The README contract: the install commands, what to type next, the section order, a FAQ,
     no star badge, a works-with table with dates, and a sample that is the header of the
     committed real report, line for line. The counts it quotes are the counts the suites print.
 10. `make test` runs the three suites and CI runs `make test`. Every action is pinned to a
     commit sha. No manifest carries an email. The icon and the social preview have the right size.
 11. No em dash in any text file.
 12. No tracked file matches a credential pattern.

Standard library only. Run: python3 tests/test_manifests.py   (exit 0 = all pass)
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

failures = []
_total = 0

NAME = "secure-my-app"
# The story sentence is not hardcoded here. .claude-plugin/plugin.json owns it, and every
# other place that carries it is compared against that one, so a copy cannot silently
# drift. evals/check_skill.py pins it independently as a Python literal, and the last
# check in section 1 compares the two, which is what closes the loop.

SKILL_MD = f"skills/{NAME}/SKILL.md"

# The file list every 10x skill-plugin repo ships. A missing entry is named by the failing
# check, so the fix is always obvious from the CI log alone.
REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    ".copilot-plugin/plugin.json",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/validate.yml",
    ".github/workflows/release.yml",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "llms.txt",
    "docs/quickstart.md",
    "docs/editors.md",
    "docs/faq.md",
    "docs/limits.md",
    "evals/README.md",
    "evals/RED-baseline.md",
    "evals/scenarios.md",
    "evals/check_skill.py",
    "tests/test_manifests.py",
    "tests/test_fixture.py",
    "Makefile",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/social-preview.png",
    ".claude-plugin/icon.png",
    "examples/sample-report.md",
    "examples/sample-surface.json",
    "examples/illustration-supabase.md",
    "examples/vulnerable-app/server.js",
    "examples/vulnerable-app/package.json",
    "examples/vulnerable-app/README.md",
    SKILL_MD,
]
REQUIRED_DIRS = ["assets", "examples", f"skills/{NAME}/references"]
TRANSLATIONS = ["es", "fr", "ja", "zh-CN"]


def check(name, ok, detail=""):
    global _total
    _total += 1
    tag = "PASS" if ok else "FAIL"
    msg = f"{tag}: {name}"
    if detail and not ok:
        msg += f"  ({detail})"
    print(msg)
    if not ok:
        failures.append(name)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def load_json(rel):
    """Returns (data, error_string). A missing or malformed file yields ({}, why)."""
    try:
        return json.loads(read(rel)), ""
    except FileNotFoundError:
        return {}, f"{rel} not found"
    except json.JSONDecodeError as e:
        return {}, f"{rel} is not valid JSON: {e}"


# --- 1. the four manifests ---
plugin, plugin_err = load_json(".claude-plugin/plugin.json")
mkt, mkt_err = load_json(".claude-plugin/marketplace.json")
cursor, cursor_err = load_json(".cursor-plugin/plugin.json")
copilot, copilot_err = load_json(".copilot-plugin/plugin.json")

check(".claude-plugin/plugin.json parses as valid JSON", not plugin_err, plugin_err)
check(".claude-plugin/marketplace.json parses as valid JSON", not mkt_err, mkt_err)
check(".cursor-plugin/plugin.json parses as valid JSON", not cursor_err, cursor_err)
check(".copilot-plugin/plugin.json parses as valid JSON", not copilot_err, copilot_err)

check(f".claude-plugin/plugin.json name == {NAME!r}", plugin.get("name") == NAME,
      f"got {plugin.get('name')!r}")
check(".claude-plugin/plugin.json has 'version'", bool(plugin.get("version")),
      ".claude-plugin/plugin.json is missing 'version'")
check(".claude-plugin/plugin.json has 'description' >= 10 chars",
      len(plugin.get("description", "")) >= 10, ".claude-plugin/plugin.json description too short")
check(".claude-plugin/plugin.json 'author' is a dict with 'name'",
      isinstance(plugin.get("author"), dict) and bool((plugin.get("author") or {}).get("name")),
      ".claude-plugin/plugin.json author must be an object carrying a name")
check(".claude-plugin/plugin.json 'keywords' is a list", isinstance(plugin.get("keywords"), list),
      ".claude-plugin/plugin.json keywords must be an array, not a string")
check(f".claude-plugin/plugin.json keywords include 'claude-code' and {NAME!r}",
      {"claude-code", NAME} <= set(plugin.get("keywords") or []),
      f"got {plugin.get('keywords')!r}")
check(".claude-plugin/plugin.json 'license' == 'MIT'", plugin.get("license") == "MIT",
      f"got {plugin.get('license')!r}")
check(".claude-plugin/plugin.json homepage points at the repo",
      f"github.com/Aboudjem/{NAME}" in plugin.get("homepage", ""),
      f"got {plugin.get('homepage')!r}")

# The story sentence, read from the one manifest that owns it.
STORY = plugin.get("description", "")

check(f".claude-plugin/marketplace.json name == '{NAME}-marketplace'",
      mkt.get("name") == f"{NAME}-marketplace", f"got {mkt.get('name')!r}")
check(".claude-plugin/marketplace.json owner.name present",
      bool((mkt.get("owner") or {}).get("name")),
      ".claude-plugin/marketplace.json is missing owner.name")
_p0 = (mkt.get("plugins") or [{}])[0]
check(f".claude-plugin/marketplace.json plugins[0].name == {NAME!r}", _p0.get("name") == NAME,
      f"got {_p0.get('name')!r}")
check(".claude-plugin/marketplace.json plugins[0].source == './'", _p0.get("source") == "./",
      f"got {_p0.get('source')!r}")
check(".claude-plugin/marketplace.json plugins[0] has description >= 10 and version",
      len(_p0.get("description", "")) >= 10 and bool(_p0.get("version")),
      ".claude-plugin/marketplace.json plugins[0] is missing description or version")
check(".claude-plugin/marketplace.json plugins[0].description matches the story sentence",
      _p0.get("description") == STORY,
      "plugins[0].description drifted from .claude-plugin/plugin.json")
check(".claude-plugin/marketplace.json metadata.description matches the story sentence",
      (mkt.get("metadata") or {}).get("description") == STORY,
      "metadata.description drifted from .claude-plugin/plugin.json")

# The editor mirrors are the same plugin under another agent's directory name, so nothing but
# the path may differ. A mirror that drifts installs a different description than the
# marketplace shows.
for rel, m in ((".cursor-plugin/plugin.json", cursor), (".copilot-plugin/plugin.json", copilot)):
    check(f"{rel} names the plugin {NAME!r}", m.get("name") == NAME, f"got {m.get('name')!r}")
    check(f"{rel} description matches .claude-plugin/plugin.json",
          m.get("description") == plugin.get("description"), f"{rel} description drifted")
    check(f"{rel} license matches .claude-plugin/plugin.json",
          m.get("license") == plugin.get("license"), f"{rel} license drifted")
    check(f"{rel} keywords match .claude-plugin/plugin.json",
          m.get("keywords") == plugin.get("keywords"), f"{rel} keywords drifted")
    check(f"{rel} declares skills == [{NAME!r}]", m.get("skills") == [NAME],
          f"{rel} skills is {m.get('skills')!r}")
    check(f"{rel} declares no mcp key ({NAME} ships no server)", "mcp" not in m,
          f"{rel} carries an mcp key")

# evals/check_skill.py pins the story sentence as a Python literal, so the skill eval can assert
# it without reading a manifest. That literal and .claude-plugin/plugin.json are two copies of one
# string, so they are compared here: without this check they drift apart and both suites stay
# green while the repo says two different things.
try:
    _cs = read("evals/check_skill.py")
    _csm = re.search(r'^STORY = (.*?)\n\n', _cs, re.DOTALL | re.MULTILINE)
    _cs_story = "".join(re.findall(r'"([^"]*)"', _csm.group(1))) if _csm else None
    check("evals/check_skill.py STORY matches .claude-plugin/plugin.json description",
          _cs_story == STORY,
          f"check_skill.py has {(_cs_story or '')[:60]!r}, plugin.json has {STORY[:60]!r}")
except FileNotFoundError:
    check("evals/check_skill.py is readable", False, "evals/check_skill.py is missing")


# --- 2. one version, everywhere it is declared ---
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def skill_frontmatter():
    try:
        text = read(SKILL_MD)
    except FileNotFoundError:
        return None, None
    m = FRONTMATTER_RE.match(text)
    return (m.group(1) if m else None), text


def changelog_version():
    try:
        m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.MULTILINE)
        return m.group(1) if m else None
    except FileNotFoundError:
        return None


_fm_block, _skill_text = skill_frontmatter()
_skill_version = None
if _fm_block:
    _vm = re.search(r"^\s+version:\s*[\"'](\d+\.\d+\.\d+)[\"']", _fm_block, re.MULTILINE)
    _skill_version = _vm.group(1) if _vm else None

versions = {
    ".claude-plugin/plugin.json version": plugin.get("version"),
    ".claude-plugin/marketplace.json plugins[0].version": _p0.get("version"),
    ".cursor-plugin/plugin.json version": cursor.get("version"),
    ".copilot-plugin/plugin.json version": copilot.get("version"),
    "CHANGELOG.md latest entry": changelog_version(),
}
_distinct = set(versions.values())
check("version is identical across all four manifests and CHANGELOG.md",
      len(_distinct) == 1 and None not in _distinct,
      "; ".join(f"{k}={v!r}" for k, v in versions.items()))
check(f"{SKILL_MD} metadata.version matches .claude-plugin/plugin.json",
      _skill_version is not None and _skill_version == plugin.get("version"),
      f"{SKILL_MD} metadata.version={_skill_version!r}, plugin.json={plugin.get('version')!r}")

# --- 3. required files ---
for rel in REQUIRED_FILES:
    check(f"required file exists: {rel}", os.path.isfile(os.path.join(ROOT, rel)),
          f"{rel} is missing")
for rel in REQUIRED_DIRS:
    path = os.path.join(ROOT, rel)
    check(f"required directory exists: {rel}/", os.path.isdir(path), f"{rel}/ is missing")
_examples = os.path.join(ROOT, "examples")
check("examples/ ships at least one worked example (.md)",
      os.path.isdir(_examples) and any(f.endswith(".md") for f in os.listdir(_examples)),
      "examples/ holds no .md file")

# --- 4. SKILL.md frontmatter contract ---
if _fm_block is None:
    check(f"{SKILL_MD} has YAML frontmatter", False,
          f"{SKILL_MD} is missing or has no `---` frontmatter block")
else:
    _name_m = re.search(r"^name:\s*(\S+)\s*$", _fm_block, re.MULTILINE)
    _fm_name = _name_m.group(1).strip("\"'") if _name_m else None
    check(f"{SKILL_MD} frontmatter declares name: {NAME}", _fm_name == NAME,
          f"{SKILL_MD} name={_fm_name!r}, must match the skills/{NAME}/ directory")
    _desc_m = re.search(r"^description:\s*(.*)$", _fm_block, re.MULTILINE)
    check(f"{SKILL_MD} frontmatter declares a description", bool(_desc_m),
          f"{SKILL_MD} has no description key")
    check(f"{SKILL_MD} frontmatter declares license: MIT",
          bool(re.search(r"^license:\s*[\"']?MIT[\"']?\s*$", _fm_block, re.MULTILINE)),
          f"{SKILL_MD} must declare `license: MIT`")
    check(f"{SKILL_MD} frontmatter declares a quoted metadata.version",
          _skill_version is not None,
          f"{SKILL_MD} needs `metadata:` then an indented `version: \"x.y.z\"` (quoted)")
    check(f"{SKILL_MD} declares no bare top-level version:",
          not re.search(r"^version:", _fm_block, re.MULTILINE),
          f"{SKILL_MD} must carry the version under metadata:, not at the top level")

# --- 5 + 6. every relative link and asset README.md points at must resolve ---
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
SRC_RE = re.compile(r"(?:src|srcset|href)\s*=\s*[\"']([^\"']+)[\"']")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#", "ftp://", "data:")


def relative_targets(text):
    """Markdown links plus HTML src/srcset/href, outside fenced blocks, relative only."""
    targets, fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            fence = not fence
            continue
        if fence:
            continue
        for raw in LINK_RE.findall(line) + SRC_RE.findall(line):
            t = raw.strip().strip("<>")
            if not t or t.lower().startswith(SKIP_PREFIXES):
                continue
            targets.append(t.split("#", 1)[0].split("?", 1)[0])
    return [t for t in targets if t]


ASSET_EXT = (".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4")
try:
    readme = read("README.md")
    check("README.md carries the story sentence verbatim", STORY in readme,
          "README.md must open on the same sentence plugin.json and SKILL.md carry")
    targets = relative_targets(readme)
    check("README.md has at least one relative link to check", bool(targets),
          "README.md carries no relative link at all, which is not the house shape")
    missing = [t for t in targets
               if not os.path.exists(os.path.join(ROOT, os.path.normpath(t)))]
    check(f"every relative link in README.md resolves ({len(targets)} checked)", not missing,
          "missing: " + ", ".join(sorted(set(missing))[:8]))
    assets = [t for t in targets if t.lower().endswith(ASSET_EXT)]
    missing_assets = [t for t in assets
                      if not os.path.exists(os.path.join(ROOT, os.path.normpath(t)))]
    check(f"every asset README.md references exists ({len(assets)} checked)",
          bool(assets) and not missing_assets,
          "missing: " + ", ".join(sorted(set(missing_assets))[:8]) if missing_assets
          else "README.md references no image asset")
except FileNotFoundError:
    check("README.md is readable", False, "README.md is missing")

# --- 7. every references/*.md SKILL.md names must exist ---
REFERENCE_RE = re.compile(r"(?:skills/secure-my-app/)?references/([A-Za-z0-9._\-]+\.md)")
if _skill_text is None:
    check(f"{SKILL_MD} is readable", False, f"{SKILL_MD} is missing")
else:
    refs = sorted(set(REFERENCE_RE.findall(_skill_text)))
    check(f"{SKILL_MD} names at least one reference file", bool(refs),
          f"{SKILL_MD} loads no references/*.md, so the depth has nowhere to live")
    missing_refs = [r for r in refs
                    if not os.path.isfile(os.path.join(ROOT, "skills", NAME, "references", r))]
    check(f"every references/*.md {SKILL_MD} names exists ({len(refs)} checked)",
          not missing_refs,
          "missing under skills/secure-my-app/references/: " + ", ".join(missing_refs[:8]))

# --- 8. translations ---
for lang in TRANSLATIONS:
    rel = f"READMEs/{lang}.md"
    exists = os.path.isfile(os.path.join(ROOT, rel))
    check(f"{rel} exists", exists, f"{rel} is missing")
    if not exists:
        continue
    t = read(rel)
    check(f"{rel} links back to ../README.md", "../README.md" in t[:1500],
          f"{rel} has no language switcher pointing at ../README.md")
    check(f"{rel} carries the may-lag marker", "<!-- may-lag -->" in t,
          f"{rel} must carry the literal `<!-- may-lag -->` marker")

# The translations describe the committed sample by its finding count. That count is the
# number of severity headings in examples/sample-report.md, so a new sample cannot leave a
# translation quoting a stale number.
SAMPLE_FINDINGS = len(re.findall(r"^## (?:CRITICAL|HIGH|MEDIUM|LOW) ",
                                 read("examples/sample-report.md"), re.M))
_FR = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
       "onze", "douze", "treize", "quatorze", "quinze", "seize"]
_ES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
       "once", "doce", "trece", "catorce", "quince", "dieciséis"]
_ZH = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三",
       "十四", "十五", "十六"]
COUNT_PATTERNS = {
    "fr": (r"sample-report\.md\),\s*(\S+)\s+constats", lambda w: _FR.index(w)),
    "es": (r"sample-report\.md\),\s*(\S+)\s+hallazgos", lambda w: _ES.index(w)),
    "zh-CN": (r"sample-report\.md\)，\s*(\S+?)条发现", lambda w: _ZH.index(w)),
    "ja": (r"sample-report\.md\)、\s*(\d+)\s*件の検出結果", int),
}
for lang, (pattern, to_int) in COUNT_PATTERNS.items():
    rel = f"READMEs/{lang}.md"
    if not os.path.isfile(os.path.join(ROOT, rel)):
        continue
    m = re.search(pattern, read(rel))
    try:
        quoted = to_int(m.group(1)) if m else None
    except ValueError:
        quoted = None
    check(f"{rel} quotes the sample's finding count ({SAMPLE_FINDINGS})",
          quoted == SAMPLE_FINDINGS,
          f"{rel} says {m.group(1) if m else 'no count'}; examples/sample-report.md has "
          f"{SAMPLE_FINDINGS} severity headings")

# --- 9. the README contract: a reader can install it, run it, and trust the sample ---
def fenced_blocks(text):
    """(lang, body) for every fenced block."""
    return [(m.group(1).strip().lower(), m.group(2))
            for m in re.finditer(r"^```([^\n]*)\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)]


def png_size(rel):
    """(width, height) read from the PNG header, or None when the file is not a PNG."""
    with open(os.path.join(ROOT, rel), "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


try:
    readme = read("README.md")
    blocks = fenced_blocks(readme)
    shell = "\n".join(body for lang, body in blocks if lang in ("bash", "sh"))
    check("README.md shows the Claude Code install command in a code block",
          f"claude plugin install {NAME}@10x" in shell)
    check("README.md shows the skills CLI install command in a code block",
          f"npx skills add Aboudjem/{NAME}\n" in shell)
    check("README.md shows what to type after installing, in a code block",
          any(body.strip() == "secure my app before I launch" for _, body in blocks),
          "a reader who installed it must see the plain-language trigger on a line of its own")
    # The short trigger differs per agent. These two are the ones the dated runs used:
    # Claude Code namespaces a plugin skill, Codex CLI mentions a skill with `$`.
    check("README.md gives the per-agent short triggers",
          f"`/{NAME}:{NAME}`" in readme and f"`${NAME}`" in readme,
          f"README.md must name `/{NAME}:{NAME}` (Claude Code) and `${NAME}` (Codex CLI)")
    first_h2 = [m.start() for m in re.finditer(r"^## ", readme, re.MULTILINE)]
    check("README.md gives a command before its second section",
          len(first_h2) >= 2 and "```bash" in readme[:first_h2[1]])
    check("README.md carries no star badge and no stargazers link",
          "stargazers" not in readme and "github/stars" not in readme,
          "a star count is a number this repo cannot re-run")
    order = [readme.find(h) for h in ("\n## Install", "\n## How it works", "\n## Proof",
                                      "\n## FAQ", "\n## Limits")]
    check("README.md has Install, How it works, Proof, FAQ and Limits, in that order",
          all(i >= 0 for i in order) and order == sorted(order), str(order))
    faq = readme[order[3]:order[4]] if order[3] >= 0 and order[4] >= 0 else ""
    check("README.md FAQ asks at least 5 questions",
          len(re.findall(r"^### .+\?$", faq, re.MULTILINE)) >= 5)
    check("README.md names `make test` as the test command", "make test" in shell)

    # The sample in the README is the top of the committed real report, line for line. A sample
    # that drifts from its source is how a fictional report got called real output once.
    sample = read("examples/sample-report.md")
    report_head = next((body for _, body in fenced_blocks(sample)
                        if body.startswith("VERDICT: ")), "")
    readme_head = next((body for _, body in blocks if body.startswith("VERDICT: ")), "")
    check("examples/sample-report.md opens with the VERDICT block",
          sample.lstrip().startswith("```") and bool(report_head))
    check("README.md sample is the header of examples/sample-report.md, line for line",
          bool(readme_head) and readme_head == report_head,
          "copy the first fenced block of examples/sample-report.md into the README")
    lines = [l for l in readme_head.split("\n") if l.strip()]
    check("the sample opens VERDICT, then findings, then DO FIRST with three actions",
          len(lines) >= 6 and lines[0].startswith("VERDICT: ") and lines[1].startswith("findings:")
          and lines[2] == "DO FIRST" and all(re.match(r"\d\. \S", l) for l in lines[3:6]))
    check("examples/sample-report.md says it is a real run and names the fixture",
          "A real run, not an illustration" in sample and "examples/vulnerable-app/" in sample)
    illustration = read("examples/illustration-supabase.md")
    check("examples/illustration-supabase.md says it is an illustration in its first lines",
          "This is an illustration, not a run" in "\n".join(illustration.split("\n")[:4]))
    check("README.md never calls the invented report real",
          "illustration" in readme and "That one is invented" in readme)
    counts = re.findall(r"^(\d+)/(\d+) checks passed", readme, re.MULTILINE)
    check("README.md quotes three `N/N checks passed` lines, one per suite",
          len(counts) == 3 and all(a == b for a, b in counts), str(counts))
    for rel, quoted in (("evals/check_skill.py", counts[0] if counts else None),
                        ("tests/test_fixture.py", counts[2] if len(counts) > 2 else None)):
        args = [sys.executable, os.path.join(ROOT, rel)]
        if rel.startswith("evals/"):
            args.append(os.path.join(ROOT, SKILL_MD))
        out = subprocess.run(args, capture_output=True, text=True, cwd=ROOT).stdout
        got = re.findall(r"^(\d+)/(\d+) checks passed", out, re.MULTILINE)
        check(f"the count README.md quotes for {rel} is the count it prints",
              bool(got) and quoted == got[-1], f"README {quoted}, suite prints {got[-1:]}")
    controls = len(re.findall(r"^\| [KDRPVFS]\d+ \|", read(f"skills/{NAME}/references/controls.md"),
                              re.MULTILINE))
    check("the catalogue holds 65 controls, the number every doc quotes", controls == 65,
          f"{controls} rows")
    table = re.search(r"^\| Agent \|.*\| Tested \|\n\|[- |]+\|\n((?:\|.*\|\n)+)", readme, re.MULTILINE)
    rows = table.group(1).strip().split("\n") if table else []
    check("README.md works-with table gives every row a test date",
          bool(rows) and all(re.search(r"\| 20\d\d-\d\d-\d\d \|$", r) for r in rows),
          "an agent nobody ran goes in the sentence under the table")
except FileNotFoundError as e:
    check("README.md and the examples are readable", False, str(e))

# --- 10. the test command, the supply chain, the listing images ---
makefile = read("Makefile") if os.path.isfile(os.path.join(ROOT, "Makefile")) else ""
recipe = re.search(r"^test:\n((?:\t.+\n)+)", makefile, re.MULTILINE)
check("Makefile `test` runs the three suites",
      bool(recipe) and all(s in recipe.group(1) for s in
                           ("evals/check_skill.py", "tests/test_manifests.py",
                            "tests/test_fixture.py")))
workflow = read(".github/workflows/validate.yml")
check("CI runs `make test` on push and on pull request",
      "run: make test" in workflow and bool(re.search(r"^on:\n  push:\n  pull_request:", workflow,
                                                     re.MULTILINE)))
uses = []
for wf in sorted(os.listdir(os.path.join(ROOT, ".github", "workflows"))):
    uses += re.findall(r"uses:\s*(\S+)", read(f".github/workflows/{wf}"))
loose = [u for u in uses if not re.search(r"@[0-9a-f]{40}$", u)]
check(f"every GitHub action is pinned to a commit sha ({len(uses)} checked)",
      bool(uses) and not loose, ", ".join(loose))
check("CI installs a pinned Claude Code and a pinned skills CLI, never @latest",
      "@latest" not in workflow and bool(re.search(r"skills@\d+\.\d+\.\d+", workflow))
      and bool(re.search(r"@anthropic-ai/claude-code@\d+\.\d+\.\d+", workflow)))
for rel in (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json",
            ".copilot-plugin/plugin.json", ".claude-plugin/marketplace.json"):
    check(f"{rel} carries no email address", "@" not in read(rel).replace("@10x", ""),
          "the author is a name and a URL")
icon = png_size(".claude-plugin/icon.png") if os.path.isfile(
    os.path.join(ROOT, ".claude-plugin/icon.png")) else None
check(".claude-plugin/icon.png is a square PNG, 512 to 2048 px, under 2 MB",
      bool(icon) and icon[0] == icon[1] and 512 <= icon[0] <= 2048
      and os.path.getsize(os.path.join(ROOT, ".claude-plugin/icon.png")) < 2 * 1024 * 1024,
      str(icon))
card = png_size(".github/social-preview.png") if os.path.isfile(
    os.path.join(ROOT, ".github/social-preview.png")) else None
check(".github/social-preview.png is a 1280x640 PNG under 1 MB",
      card == (1280, 640)
      and os.path.getsize(os.path.join(ROOT, ".github/social-preview.png")) < 1024 * 1024,
      str(card))
try:
    surface = json.loads(read("examples/sample-surface.json"))
    keys = [f.get("key", "") for f in surface.get("findings", [])]
    check("examples/sample-surface.json keys every finding by control id plus location",
          bool(keys) and all(re.match(r"[KDRPVFS]\d{1,2}:\S", k) for k in keys), str(keys[:3]))
except (OSError, ValueError) as e:
    check("examples/sample-surface.json parses as JSON", False, str(e))

# --- 11. house style: no em dash in any tracked text file ---
EM = "\u2014"
TEXT_EXT = {".md", ".txt", ".json", ".yml", ".yaml", ".svg", ".html", ".py", ".js", ".toml", ""}
dashed = []
for rel in subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                          capture_output=True, text=True, cwd=ROOT).stdout.splitlines():
    if os.path.splitext(rel)[1].lower() not in TEXT_EXT:
        continue
    try:
        if EM in read(rel):
            dashed.append(rel)
    except (OSError, UnicodeDecodeError):
        continue
check("no em dash in any text file of the repo", not dashed, ", ".join(dashed[:8]))

# --- 12. no secrets (the CI patterns, mirrored so a local run catches them too) ---
SECRETS = [re.compile(p) for p in (
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----",
    r"ghp_[A-Za-z0-9]{36}", r"github_pat_[A-Za-z0-9_]{22,}", r"gh[osur]_[A-Za-z0-9]{36}",
    r"sk-ant-[A-Za-z0-9_\-]{24,}", r"sk-(?:proj-)?[A-Za-z0-9]{32,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"https://hooks\.slack\.com/services/[A-Za-z0-9/+]{20,}", r"AIza[0-9A-Za-z_\-]{35}",
    r"sk_live_[0-9a-zA-Z]{24,}", r"npm_[A-Za-z0-9]{36}",
    r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{40,}\.[A-Za-z0-9_\-]{20,}")]
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".woff", ".woff2", ".ico",
              ".pdf", ".zip", ".ttf", ".otf"}
tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                         cwd=ROOT).stdout.splitlines()
if not tracked:
    # Before the first commit `git ls-files` is empty, and a secrets scan over nothing passes
    # vacuously. Walk the working tree instead, so a local run catches a leak the same way CI
    # will once the file is tracked.
    for _dir, _subdirs, _files in os.walk(ROOT):
        _subdirs[:] = [d for d in _subdirs
                       if d not in (".git", ".omc", "node_modules", "__pycache__")]
        tracked += [os.path.relpath(os.path.join(_dir, f), ROOT) for f in _files]
leaks = []
for rel in tracked:
    if os.path.splitext(rel)[1].lower() in BINARY_EXT:
        continue
    try:
        for ln, line in enumerate(read(rel).splitlines(), 1):
            if any(rx.search(line) for rx in SECRETS):
                leaks.append(f"{rel}:{ln}")
    except (OSError, UnicodeDecodeError):
        continue
check(f"no tracked file matches a credential pattern ({len(tracked)} tracked)", not leaks,
      ", ".join(leaks[:5]))

print("-" * 60)
passed = _total - len(failures)
print(f"{passed}/{_total} checks passed")
print(f"{len(failures)} failed" if failures else "All checks passed.")
sys.exit(1 if failures else 0)
