#!/usr/bin/env python3
"""
secure-my-app skill eval: machine-checkable static assertions on skills/secure-my-app/SKILL.md.

This is the deterministic half of the eval suite. It encodes the house contract and the
secure-my-app design lock as pass/fail checks, so a regression is caught in CI rather than in
someone's security report. It was written BEFORE the skill existed and run once against the
missing file (RED: not found, exit 1); see evals/RED-baseline.md. The behavioral half, a cold
model asked to audit an app's security with no skill installed, is recorded in the same file.

What it enforces:
  - frontmatter keys present and well-formed (name, description, license, metadata.version,
    argument-hint), with the version quoted and never at the top level;
  - the description is WHEN-only, carries the story sentence verbatim, and sits in the house
    length range;
  - the required section headings are all present and in the right order;
  - no emoji in any heading, and no em dash anywhere in the file;
  - the body stays under 600 lines, so the depth lives in references/;
  - every references/*.md path the body mentions exists on disk;
  - the control sections give orders, not advice ("you should" and friends are banned there).

Usage:
    python3 evals/check_skill.py [path-to-SKILL.md]   # default: skills/secure-my-app/SKILL.md
Exit code 0 = all checks pass, 1 = at least one failed. Standard library only.
"""
import os
import re
import sys

NAME = "secure-my-app"
DEFAULT_PATH = os.path.join("skills", NAME, "SKILL.md")

# Locked byte-identical across the whole repo (README, plugin.json, both mirrors,
# marketplace.json, SKILL.md). Compared against the RAW text: the point of locking it is that
# the wording does not drift.
STORY = "Find what a stranger can take from your app. Then close it and prove it closed."

# The house section skeleton, in order. Each entry is (what the section DOES, the heading
# prefixes that count as it). Matched on the lowercased heading with backticks stripped, so a
# heading may carry a parenthetical tail, and a skill may use its own domain name for a section
# as long as the function is there. The order is the contract: the story, then how to call it,
# then when not to, then the procedure, then the rules, then the artifact, then the depth, then
# the failure modes.
REQUIRED_SECTIONS = [
    ("the overview", ["## overview"]),
    ("how it is invoked", ["## invocation"]),
    ("when to use it and when not", ["## when to use"]),
    ("the procedure", ["## the run", "## procedure"]),
    ("the hard rules", ["## what this refuses to do", "## hard rules"]),
    ("the output artifact and handoff", ["## the output", "## handoff format", "## the report"]),
    ("the depth pointer", ["## reference files", "## reuse"]),
    ("the failure modes", ["## common mistakes"]),
]

# House signatures that are required but whose position is not pinned.
UNORDERED_SECTIONS = [
    ("honest limits (what the skill does NOT promise)", ["## honest limits", "## limits"]),
    ("cross-harness (what travels to other agents)",
     ["## cross-harness", "## other agents", "## works in your editor"]),
]

# The sections that give the agent orders. Advice-shaped wording in them is a bug: a hedge in a
# control section is what a model reads as permission to skip the step.
CONTROL_SECTION_LABELS = {"the procedure", "the hard rules", "the failure modes"}
ADVICE_PHRASES = [
    "you should",
    "you may want to",
    "you might want to",
    "it is recommended",
    "it's recommended",
    "if desired",
]
# Quoted specimens: a line that quotes the banned wording in order to ban it. Pinned so the
# hatch cannot widen silently.
EXPECTED_SPECIMENS = 1

# The catalogue size. A full run ends every control in exactly one outcome, so the three coverage
# counts on a verdict line add up to this. Change it only when references/controls.md changes.
EXPECTED_CONTROLS = 65

# --- domain invariants -----------------------------------------------------------------
# Two claims in this skill are the kind that read as fine and are wrong, so they are pinned
# here rather than trusted to review. Both were caught by an adversarial review on 2026-09-06.

# 1. The gate's third label. "NO CONFIRMED EXPOSURE" was retired because a reader hears it as
#    "no exposure". The replacement says only what happened, and it is never printed alone:
#    a thoroughly checked app and a run that could barely check anything reach the same label,
#    so the coverage counts have to ride on the same line.
GATE_LABEL = "NOTHING CONFIRMED HERE"
RETIRED_GATE_LABEL = "NO CONFIRMED EXPOSURE"
GATE_WITH_COVERAGE_RE = re.compile(r"VERDICT:\s+" + GATE_LABEL + r"\s+coverage\s+\d+\s+checked")

# 2. The RLS direction. Row-level security switched ON with no matching policy DENIES. The
#    inverted claim, that a table with no policy is therefore readable, sends a user to "fix"
#    their safest table. RLS_WRONG_RE catches the inverted form; the self-tests below prove it
#    fires on the wrong sentence and stays quiet on the correct one, because a gate nobody has
#    watched fail is not a gate.
RLS_WRONG_RE = re.compile(
    r"no (?:matching )?polic(?:y|ies)[^.]{0,70}?\b(?:so|means|implies|therefore)\b"
    r"[^.]{0,70}?(?:public|exposed|readable|anyone can read)", re.I)
RLS_WRONG_SPECIMEN = ("There is no policy on this table, so the data is public.")
RLS_RIGHT_SPECIMEN = ('RLS switched ON with no matching policy denies. So "there is no policy on '
                      'this table" is not evidence of exposure on its own.')

EM_DASH = "\u2014"

# Emoji blocks. Arrows (U+2190-U+21FF), the middle dot and the maths operators the house style
# uses on purpose are deliberately NOT in here.
EMOJI_RANGES = [
    (0x1F000, 0x1FAFF),
    (0x1F1E6, 0x1F1FF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
    (0xFE0F, 0xFE0F),
    (0x2B00, 0x2BFF),
]


def has_emoji(s):
    return any(any(lo <= ord(ch) <= hi for lo, hi in EMOJI_RANGES) for ch in s)


def parse_frontmatter(block):
    """Minimal YAML parse for top-level scalars + folded/literal block scalars."""
    data = {}
    lines = block.split("\n")
    i = 0
    key_re = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or line[:1] in (" ", "\t"):
            i += 1
            continue
        km = key_re.match(line)
        if not km:
            i += 1
            continue
        key, rest = km.group(1), km.group(2).strip()
        if rest.startswith(("|", ">")):
            collected = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "":
                    collected.append("")
                    i += 1
                    continue
                if nxt[:1] in (" ", "\t"):
                    collected.append(nxt.strip())
                    i += 1
                else:
                    break
            data[key] = " ".join(c for c in collected if c != "").strip()
            continue
        val = rest
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        data[key] = val
        i += 1
    return data


def headings(body):
    """(line number, raw heading) for every ATX heading outside fenced code blocks."""
    out, fence = [], None
    fence_re = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
    for n, line in enumerate(body.split("\n"), 1):
        fm = fence_re.match(line)
        if fm:
            if fence is None:
                fence = fm.group(1)[0]
            elif fm.group(1)[0] == fence and not fm.group(2).strip():
                fence = None
            continue
        if fence is None and re.match(r"^#{1,6}\s", line):
            out.append((n, line.rstrip()))
    return out


def section_slices(body):
    """{lowercased `## ` heading: section text} for every H2, heading line included."""
    slices, current, buf = {}, None, []
    for line in body.split("\n"):
        if line.startswith("## "):
            if current is not None:
                slices[current] = "\n".join(buf)
            current = line.strip().replace("`", "").lower()
            buf = [line]
        elif current is not None:
            buf.append(line)
    if current is not None:
        slices[current] = "\n".join(buf)
    return slices


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    if not os.path.exists(path):
        print(f"FAIL: {path} not found")
        print("-" * 60)
        print(f"0 checks passed for {path} (nothing to check: RED)")
        return 1

    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not m:
        print(f"FAIL: no YAML frontmatter in {path}")
        print("-" * 60)
        print(f"0 checks passed for {path} (nothing to check: no frontmatter)")
        return 1

    block = m.group(1)
    body = text[m.end():]
    fm = parse_frontmatter(block)
    low = re.sub(r"\s+", " ", body).replace("`", "").replace("*", "").lower()
    checks = []

    # --- frontmatter ---
    fm_name = fm.get("name", "")
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    checks.append(("frontmatter: name matches ^[a-z0-9]+(-[a-z0-9]+)*$ and is <= 64 chars",
                   bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fm_name)) and len(fm_name) <= 64,
                   f"got {fm_name!r}"))
    checks.append((f"frontmatter: name equals the parent directory ({parent})", fm_name == parent,
                   f"name={fm_name!r}, directory={parent!r}"))
    desc = fm.get("description", "")
    checks.append(("frontmatter: description is present and non-empty", bool(desc.strip()), ""))
    checks.append(("frontmatter: description is <= 1024 chars (the Agent Skills spec cap)",
                   len(desc) <= 1024, f"{len(desc)} chars, {max(0, len(desc) - 1024)} over"))
    checks.append(("frontmatter: description is >= 400 chars (the house floor)",
                   len(desc) >= 400, f"{len(desc)} chars"))
    checks.append(("frontmatter: metadata.version is present AND quoted",
                   bool(re.search(r"^\s+version:\s*[\"']\d+\.\d+\.\d+[\"']\s*$", block,
                                  re.MULTILINE)),
                   "needs `metadata:` then an indented `version: \"x.y.z\"`, quotes included"))
    checks.append(("frontmatter: no bare top-level version:",
                   not re.search(r"^version:", block, re.MULTILINE),
                   "the version belongs under metadata:"))
    checks.append(("frontmatter: license is MIT",
                   bool(re.search(r"^license:\s*[\"']?MIT[\"']?\s*$", block, re.MULTILINE)), ""))
    checks.append(("frontmatter: argument-hint is declared",
                   bool(re.search(r"^argument-hint:\s*\S", block, re.MULTILINE)), ""))

    # --- description contract (WHEN-only) ---
    checks.append(("description: carries the story sentence verbatim", STORY in desc,
                   "the first sentences must be byte-identical to plugin.json and the README"))
    checks.append((f"description: names the trigger word {NAME!r}", NAME in desc.lower(), ""))
    checks.append(("description: says every finding carries a proof",
                   "prove" in desc.lower() or "proof" in desc.lower(), ""))
    checks.append(("description: says a fix waits for approval",
                   "approv" in desc.lower(), "the human approves each fix before it is applied"))
    checks.append(("description: is WHEN-only (no numbered procedure steps)",
                   not re.search(r"\b[1-9]\.\s", desc),
                   "a numbered summary in the description becomes a shortcut models follow "
                   "instead of reading the body"))

    # --- structure: the H1 and the ordered section skeleton ---
    hs = headings(body)
    h1 = next((h for _, h in hs if h.startswith("# ")), "")
    checks.append((f"structure: the H1 is `# {NAME}`", h1.strip() == f"# {NAME}", f"got {h1!r}"))

    h2s = [h.strip().replace("`", "").lower() for _, h in hs if h.startswith("## ")]

    def find_section(prefixes):
        for i, h in enumerate(h2s):
            if any(h.startswith(p) for p in prefixes):
                return i
        return None

    found = []
    for label, prefixes in REQUIRED_SECTIONS:
        idx = find_section(prefixes)
        checks.append((f"structure: a section for {label} is present", idx is not None,
                       f"{path} has no H2 starting " + " or ".join(repr(p) for p in prefixes)))
        if idx is not None:
            found.append((label, idx))
    ordered = all(found[k][1] < found[k + 1][1] for k in range(len(found) - 1))
    checks.append(("structure: the required sections appear in the house order", ordered,
                   " then ".join(f"{lbl}@{i}" for lbl, i in found)))

    for label, prefixes in UNORDERED_SECTIONS:
        checks.append((f"structure: a section for {label} is present",
                       find_section(prefixes) is not None,
                       f"{path} has no H2 starting " + " or ".join(repr(p) for p in prefixes)))

    bad_headings = [f"line {n}: {h}" for n, h in hs if has_emoji(h)]
    checks.append(("structure: no emoji in any heading", not bad_headings,
                   "; ".join(bad_headings[:4])))

    em_lines = [str(n) for n, line in enumerate(text.split("\n"), 1) if EM_DASH in line]
    checks.append((f"style: no em dash anywhere in {os.path.basename(path)}", not em_lines,
                   f"{path}: em dash on line(s) " + ", ".join(em_lines[:8])
                   + " (use a comma, a full stop, or parentheses)"))

    line_count = body.count("\n")
    checks.append(("structure: body is under 600 lines (the depth lives in references/)",
                   line_count < 600, f"{line_count} lines"))
    checks.append((f"structure: the body documents /{NAME}", f"/{NAME}" in body, ""))
    checks.append(("structure: the body documents $ARGUMENTS", "$ARGUMENTS" in body, ""))
    checks.append((f"structure: the body names the .{NAME}/ output directory",
                   f".{NAME}/" in body, ""))
    checks.append(("structure: a ```markdown template block is fenced in the body",
                   bool(re.search(r"^```markdown\s*$", body, re.MULTILINE)),
                   "the report template must be one fenced ```markdown block"))

    # --- references: every path the body names has to exist ---
    ref_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "references")
    refs = sorted(set(re.findall(r"(?:skills/" + NAME + r"/)?references/([A-Za-z0-9._\-]+\.md)",
                                 body)))
    checks.append(("references: the body names at least one references/*.md file", bool(refs),
                   "a body under 600 lines needs the depth to live somewhere"))
    for ref in refs:
        target = os.path.join(ref_dir, ref)
        checks.append((f"references: references/{ref} exists on disk", os.path.isfile(target),
                       f"{target} is missing"))

    # --- domain invariants: the gate label and the RLS direction ---
    ref_texts = {}
    if os.path.isdir(ref_dir):
        for fn in sorted(os.listdir(ref_dir)):
            if fn.endswith(".md"):
                ref_texts[f"references/{fn}"] = open(os.path.join(ref_dir, fn),
                                                     encoding="utf-8").read()
    corpus = {os.path.basename(path): text, **ref_texts}

    checks.append((f"gate: the third label is {GATE_LABEL!r}", GATE_LABEL in text, ""))
    retired = [f for f, t in corpus.items() if RETIRED_GATE_LABEL in t]
    checks.append((f"gate: the retired label {RETIRED_GATE_LABEL!r} appears nowhere",
                   not retired, "still in " + ", ".join(retired)))
    checks.append(("gate: the rule that it is never printed without coverage is stated",
                   "on the same line" in low and "coverage" in low,
                   "the gate alone is misleading and the skill has to say so"))
    checks.append(("gate: a worked example prints the label with its coverage counts inline",
                   bool(GATE_WITH_COVERAGE_RE.search(text)),
                   f"no line matching `VERDICT: {GATE_LABEL}   coverage N checked ...`"))

    # --- the report header: verdict first, then what to do, and coverage that adds up ---
    header = re.search(r"^VERDICT: (?:DO NOT LAUNCH|LAUNCH WITH KNOWN GAPS|NOTHING CONFIRMED HERE)"
                       r"\s+coverage[^\n]*\nfindings:[^\n]*\nDO FIRST\n((?:\d\. [^\n]+\n)+)",
                       text, re.MULTILINE)
    checks.append(("output: a worked header opens VERDICT, then findings, then DO FIRST",
                   bool(header), "the first three lines of a report are fixed, in that order"))
    todo = header.group(1).strip().split("\n") if header else []
    checks.append(("output: the worked DO FIRST list holds exactly three numbered lines",
                   len(todo) == 3, f"{len(todo)} line(s)"))
    checks.append(("output: every DO FIRST line starts with a control id",
                   bool(todo) and all(re.match(r"\d\. [KDRPVFS]\d{1,2}  \S", l) for l in todo),
                   "each line is `<n>. <ID>  <action>`"))
    checks.append(("output: the rule that DO FIRST is never padded is stated",
                   "never pad it" in low, "an action with no finding behind it is advice"))
    checks.append(("output: no report example opens on the retired `gate:` header",
                   not any(re.search(r"^SECURE-MY-APP\s+gate:", t, re.MULTILINE)
                           for t in corpus.values()), "the header starts with VERDICT"))
    cov = [(f, m.group(0), sum(int(x) for x in m.groups()))
           for f, t in corpus.items()
           for m in re.finditer(r"coverage (\d+) checked / (\d+) unproven / (\d+) n/a", t)]
    off = [f"{f}: {line} = {total}" for f, line, total in cov if total != EXPECTED_CONTROLS]
    checks.append((f"output: every coverage example adds up to {EXPECTED_CONTROLS} controls",
                   bool(cov) and not off, "; ".join(off) or "no coverage example found"))
    checks.append(("output: surface.json keys a finding by control id plus WHERE",
                   "control id plus its where" in low,
                   "a positional key makes every re-run report the same finding as new"))

    rls_deny = [f for f, t in corpus.items()
                if re.search(r"no matching policy\s+denies", t, re.I)]
    checks.append(("RLS: the deny direction is stated in the skill body",
                   bool(re.search(r"no matching policy\s+denies", text, re.I)),
                   "RLS switched ON with no matching policy DENIES; getting this backwards "
                   "sends a user to fix their safest table"))
    checks.append(("RLS: the deny direction is stated in a reference file too",
                   any(f.startswith("references/") for f in rls_deny),
                   "expected it in references/controls.md as well as the body"))
    checks.append(("RLS: absence of a policy is stated not to be evidence of exposure",
                   any(re.search(r"not (?:by itself )?evidence of exposure", t, re.I)
                       for t in corpus.values()), ""))
    inverted = [f for f, t in corpus.items()
                if any(RLS_WRONG_RE.search(w) and " not " not in w.lower()
                       for w in re.sub(r"\s+", " ", t).split(". "))]
    checks.append(("RLS: the inverted claim appears nowhere", not inverted,
                   "found in " + ", ".join(inverted)))
    checks.append(("gate self-test: the inverted RLS claim is caught",
                   bool(RLS_WRONG_RE.search(RLS_WRONG_SPECIMEN)), ""))
    checks.append(("gate self-test: the correct RLS sentence is not caught",
                   not any(RLS_WRONG_RE.search(w) and " not " not in w.lower()
                           for w in RLS_RIGHT_SPECIMEN.split(". ")), ""))

    # --- control sections give orders, not advice ---
    # A phrase inside quotation marks is a specimen: the line is quoting the wrong form in order
    # to ban it, which is the only legitimate use. Those are counted and the count is pinned, so
    # the hatch cannot be widened silently. Bumping it is a deliberate act: confirm the line
    # really TEACHES the wrong form, then change the constant in the same commit.
    slices = section_slices(body)
    quoted_specimens = 0
    for want_label, want_prefixes in [(lbl, pre) for lbl, pre in REQUIRED_SECTIONS
                                      if lbl in CONTROL_SECTION_LABELS]:
        sec = next((v for k, v in slices.items()
                    if any(k.startswith(p) for p in want_prefixes)), None)
        if sec is None:
            continue
        for phrase in ADVICE_PHRASES:
            hits = []
            for ln, line in enumerate(sec.split("\n"), 1):
                if phrase not in line.lower():
                    continue
                if re.search(r'["\u201c\u2018][^"\u201d\u2019]*' + re.escape(phrase)
                             + r'[^"\u201d\u2019]*["\u201d\u2019]', line, re.I):
                    quoted_specimens += 1
                    continue
                hits.append(ln)
            checks.append((f"control section for {want_label} gives orders, not advice: "
                           f"no {phrase!r}", not hits,
                           f"{path}, inside the {want_label} section, relative line(s) "
                           + ", ".join(str(h) for h in hits[:4])))
        checks.append((f"control section for {want_label} is not empty",
                       len(sec.strip().split("\n")) > 2, f"the {want_label} section has no body"))
    checks.append((f"control sections: quoted wrong-form specimens stay pinned at "
                   f"{EXPECTED_SPECIMENS} ({quoted_specimens} in use)",
                   quoted_specimens == EXPECTED_SPECIMENS,
                   "confirm the line TEACHES the wrong form, then change EXPECTED_SPECIMENS "
                   "in evals/check_skill.py in the same commit"))

    failed = [c for c in checks if not c[1]]
    for nm, ok, detail in checks:
        tag = "PASS" if ok else "FAIL"
        extra = f"  ({detail})" if detail and not ok else ""
        print(f"{tag}: {nm}{extra}")
    print("-" * 60)
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed for {path}")
    if failed:
        print(f"{len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
