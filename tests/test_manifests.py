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
  9. No tracked file matches a credential pattern.

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

# --- 9. no secrets (the CI patterns, mirrored so a local run catches them too) ---
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
