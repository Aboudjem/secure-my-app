#!/usr/bin/env python3
"""
Fixture tests for examples/vulnerable-app (a release gate; runs in CI).

examples/sample-report.md is the report of a real secure-my-app run against this fixture. A report
is only worth showing while the app still has the holes it names. So this file starts the fixture
on a free port and replays the request behind each finding, with its legitimate twin:

  1. The server starts, binds to 127.0.0.1 only, and answers.
  2. Sign-in works for a real account and is refused for a wrong password.
  3. Each hole still answers the way the report recorded it.
  4. Each legitimate request beside a hole still succeeds, so a hole is a hole and not a broken app.
  5. The sample report and the fixture agree on what they name.

Standard library only, plus `node` on the PATH. Run: python3 tests/test_fixture.py   (exit 0 = all pass)
"""
import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "examples", "vulnerable-app")
SERVER = os.path.join(APP, "server.js")
REPORT = os.path.join(ROOT, "examples", "sample-report.md")

failures = []
_total = 0
replayed = set()  # finding ids with at least one replay check that ran


def check(name, ok, detail=""):
    global _total
    _total += 1
    finding = re.match(r"([A-Z]\d+) (hole|twin|control):", name)
    if finding:
        replayed.add(finding.group(1))
    tag = "PASS" if ok else "FAIL"
    print(f"{tag}: {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(port, method, path, body=None, cookie=None, raw_body=None):
    """One HTTP request. Returns (status, headers, parsed JSON or raw text)."""
    data = json.dumps(body).encode() if body is not None else None
    if raw_body is not None:
        data = raw_body.encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            status, headers, raw = res.status, res.headers, res.read().decode()
    except urllib.error.HTTPError as err:
        status, headers, raw = err.code, err.headers, err.read().decode()
    try:
        return status, headers, json.loads(raw)
    except ValueError:
        return status, headers, raw


def login(port, email, password):
    status, headers, _ = call(port, "POST", "/login", {"email": email, "password": password})
    raw = headers.get("Set-Cookie") or ""
    return status, raw, raw.split(";")[0]


def forge(secret, subject, **extra):
    """A session cookie signed with the secret committed in server.js (compact JSON, as Node writes it)."""
    payload = json.dumps({"sub": subject, **extra}, separators=(",", ":"))
    body = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"session={body}.{base64.urlsafe_b64encode(mac).rstrip(b'=').decode()}"


def decode_cookie(cookie):
    """The JSON payload of a `session=<body>.<mac>` cookie."""
    body = cookie.split("=", 1)[1].split(".")[0]
    return json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))


def main():
    source = open(SERVER, encoding="utf-8").read()
    lines = source.split("\n")
    check("examples/vulnerable-app/server.js exists and is not empty", len(source) > 500)
    check("the fixture declares no dependency (nothing to install, nothing to audit)",
          "dependencies" not in open(os.path.join(APP, "package.json"), encoding="utf-8").read())
    check("the fixture requires only node: built-ins",
          set(re.findall(r'require\("([^"]+)"\)', source)) == {"node:http", "node:crypto"})
    check("the fixture binds to 127.0.0.1, never to every interface",
          'listen(PORT, "127.0.0.1"' in source and "0.0.0.0" not in source)
    check("the fixture README says never to deploy it",
          "Never deploy this" in open(os.path.join(APP, "README.md"), encoding="utf-8").read())

    node = shutil.which("node")
    check("node is on the PATH", bool(node), "install Node.js 18 or newer to run the fixture")
    if not node:
        return finish()

    port = free_port()
    up = False
    server_output = ""
    proc = subprocess.Popen([node, SERVER], env={**os.environ, "PORT": str(port)},
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(50):
            try:
                up = call(port, "GET", "/")[0] == 200
                break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.1)
        check("the server starts and answers GET / with 200", up)
        if not up:
            return finish()

        # --- sign-in: the legitimate path, and its refusal ---
        a_status, a_raw, alice = login(port, "alice@paperboat.test", "alice-demo-pass")
        b_status, _, bob = login(port, "bob@paperboat.test", "bob-demo-pass")
        check("alice signs in with her password (200 and a session cookie)",
              a_status == 200 and alice.startswith("session="))
        check("bob signs in with his password (200 and a session cookie)",
              b_status == 200 and bob.startswith("session="))
        check("a wrong password is refused with 401 and no cookie",
              login(port, "alice@paperboat.test", "wrong")[0:2] == (401, ""))

        # --- R10: the admin export has no gate at all ---
        status, _, export = call(port, "GET", "/admin/export")
        check("R10 hole: GET /admin/export with no session returns 200", status == 200, status)
        check("R10 hole: the export holds all 3 users and all 3 invoices",
              isinstance(export, dict) and len(export.get("users", [])) == 3
              and len(export.get("invoices", [])) == 3)
        check("R10 hole: the export includes every password hash",
              isinstance(export, dict)
              and all(re.fullmatch(r"[0-9a-f]{64}", u.get("password_hash", ""))
                      for u in export.get("users", [])))
        check("R10 control: the other data routes answer 401 without a cookie",
              call(port, "GET", "/api/invoices")[0] == 401
              and call(port, "GET", "/api/invoices/1042")[0] == 401)

        # --- V2: the export sends whole user records, password_hash included ---
        check("V2 hole: every exported user has exactly the keys id,email,team,role,password_hash",
              isinstance(export, dict) and len(export.get("users", [])) == 3
              and all(list(u) == ["id", "email", "team", "role", "password_hash"]
                      for u in export["users"]))
        check("V2 hole: the export answers 200 with no session, so the hashes reach anyone",
              call(port, "GET", "/admin/export")[0] == 200)

        # --- R4: lookup by id alone, with its three-way read test ---
        status, _, own = call(port, "GET", "/api/invoices/1041", cookie=alice)
        check("R4 twin: alice reads her own invoice 1041 (200, her row)",
              status == 200 and own.get("owner") == "u_1")
        status, _, other = call(port, "GET", "/api/invoices/1042", cookie=alice)
        check("R4 hole: alice reads bob's invoice 1042 from another team (200)",
              status == 200 and other.get("owner") == "u_2" and other.get("team") == "team_2",
              status)
        check("R4 hole: the leaked row carries the customer email and the IBAN tail",
              isinstance(other, dict) and "customer_email" in other and "iban_last4" in other)
        status, _, theirs = call(port, "GET", "/api/invoices/1041", cookie=bob)
        check("R4 hole: bob reads alice's invoice 1041 the other way round (200)",
              status == 200 and theirs.get("owner") == "u_1", status)
        check("R4 twin: bob reads his own invoice 1042 (200, his row)",
              call(port, "GET", "/api/invoices/1042", cookie=bob)[2].get("owner") == "u_2")
        check("R4 control: with no session the same route answers 401",
              call(port, "GET", "/api/invoices/1042")[0] == 401)
        status, _, listing = call(port, "GET", "/api/invoices", cookie=alice)
        check("R4 twin: the list route is scoped, alice sees only her own invoice",
              status == 200 and [i["id"] for i in listing] == [1041])

        # --- V3: the error handler returns the stack ---
        status, _, err = call(port, "GET", "/api/invoices/not-a-number", cookie=alice)
        check("V3 hole: a bad id returns 500 with a stack trace in the body",
              status == 500 and isinstance(err, dict) and "stack" in err and "server.js" in err["stack"],
              status)

        status, _, err = call(port, "POST", "/login", raw_body="{")
        check("V3 hole: POST /login with the body '{' and no session returns 500 and the stack",
              status == 500 and isinstance(err, dict) and "SyntaxError" in err.get("error", "")
              and "JSON.parse" in err.get("stack", "") and "server.js:54" in err.get("stack", ""),
              status)
        check("V3 twin: POST /login with valid JSON and the right password still returns 200",
              login(port, "alice@paperboat.test", "alice-demo-pass")[0] == 200)

        # --- D2: the session cookie has no flags ---
        check("D2 hole: the session cookie is set without HttpOnly, Secure or SameSite",
              bool(a_raw) and not re.search(r"httponly|secure|samesite", a_raw, re.I), a_raw)

        # --- K3: the signing secret is a literal in the repo, so anyone can mint a session ---
        secret = re.search(r'const SESSION_SECRET = "([^"]+)"', source)
        check("K3 hole: the session signing secret is a string literal in server.js", bool(secret))
        if secret:
            check("K3 hole: the cookie forged from the repo secret for u_1 equals the one the server issued to alice",
                  forge(secret.group(1), "u_1") == alice)
            status, _, mine = call(port, "GET", "/api/invoices", cookie=forge(secret.group(1), "u_2"))
            check("K3 hole: a cookie forged with that secret is accepted as bob",
                  status == 200 and [i["id"] for i in mine] == [1042, 1043], status)
            check("K3 control: a cookie forged with another secret is refused with 401",
                  call(port, "GET", "/api/invoices", cookie=forge("not-the-secret", "u_2"))[0] == 401)

        # --- D5: the session holds only the user id, with no expiry and no way to end it ---
        check("D5 hole: the cookie the server issued to alice decodes to {\"sub\":\"u_1\"} and nothing else",
              decode_cookie(alice) == {"sub": "u_1"}, decode_cookie(alice))
        check("D5 hole: server.js has no expiry, max-age, logout or revoke",
              not re.search(r"expir|max-age|logout|revoke|\bexp\b", source, re.I))
        if secret:
            stale = forge(secret.group(1), "u_1", exp=int(time.time() * 1000) - 24 * 3600 * 1000)
            check("D5 hole: a correctly signed cookie whose exp passed a day ago is still accepted (200)",
                  call(port, "GET", "/api/invoices", cookie=stale)[0] == 200)
        check("D5 twin: a fresh sign-in cookie reads GET /api/invoices (200)",
              call(port, "GET", "/api/invoices",
                   cookie=login(port, "alice@paperboat.test", "alice-demo-pass")[2])[0] == 200)

        # --- D6: login accepts unlimited guesses ---
        check("D6 hole: server.js has no limiter, counter, lockout or 429",
              not re.search(r"429|rate.?limit|lockout|attempts|too many", source, re.I))
        emails = ["alice@paperboat.test", "nobody@paperboat.test"] * 6
        guesses = [login(port, email, f"wrong-guess-{n}")[0] for n, email in enumerate(emails)]
        check("D6 hole: 12 wrong-password POSTs, alternating alice's email and an unknown one, give 12 x 401 and no 429",
              guesses == [401] * 12, guesses)
        check("D6 twin: right after them, bob signs in with his password (200 and a cookie)",
              login(port, "bob@paperboat.test", "bob-demo-pass")[2].startswith("session="))

        # --- D3: unsalted SHA-256 for passwords ---
        alice_hash = next(u["password_hash"] for u in export["users"] if u["id"] == "u_1")
        check("D3 hole: server.js:12 hashes with one plain SHA-256",
              'const sha256 = (s) => crypto.createHash("sha256").update(s).digest("hex");' in lines[11])
        check("D3 hole: the stored hash is a bare SHA-256 of the password, no salt",
              alice_hash == hashlib.sha256(b"alice-demo-pass").hexdigest())

        # --- R6: mass assignment. Last, because it changes state. ---
        check("R6 hole: server.js:97 copies the whole body onto the user record",
              lines[96].strip() == "Object.assign(user, await readJson(req));")
        status, _, me = call(port, "PATCH", "/api/me", {}, cookie=alice)
        check("R6 twin: PATCH /api/me with {} is accepted and changes nothing (200, role member)",
              status == 200 and me == {"id": "u_1", "email": "alice@paperboat.test",
                                       "team": "team_1", "role": "member"}, me)
        status, _, me = call(port, "PATCH", "/api/me", {"role": "admin"}, cookie=alice)
        check("R6 hole: PATCH /api/me with {role: admin} makes a member an admin",
              status == 200 and me.get("role") == "admin", me)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        server_output = proc.stdout.read() if proc.stdout else ""

    # --- V5: no security event is recorded. Read after the run, so the failed sign-ins,
    # the export downloads and the 401s above all had their chance to log. ---
    console_lines = [n for n, l in enumerate(lines, 1) if "console." in l]
    check("V5 hole: the only console call in server.js is the startup line (line 115)",
          console_lines == [115] and "listening on" in lines[114], console_lines)
    if up:
        printed = [l for l in server_output.splitlines() if l.strip()]
        check("V5 hole: after 13 failed sign-ins, the export and the refusals, the server printed only its startup line",
              len(printed) == 1 and printed[0].startswith("paperboat listening on"), printed)

    # --- the sample report and the fixture name the same things ---
    report = open(REPORT, encoding="utf-8").read() if os.path.isfile(REPORT) else ""
    check("examples/sample-report.md exists", bool(report))
    top = [l for l in report.split("\n") if l.strip() and not l.startswith("```")]
    first = next((i for i, l in enumerate(top) if l.startswith("VERDICT: ")), -1)
    check("the sample report has a VERDICT line with its coverage on the same line",
          first >= 0 and bool(re.match(
              r"VERDICT: (DO NOT LAUNCH|LAUNCH WITH KNOWN GAPS|NOTHING CONFIRMED HERE)\s+"
              r"coverage \d+ checked / \d+ unproven / \d+ n/a", top[first])))
    check("the sample report says it is a real run on this fixture, with its date",
          "examples/vulnerable-app" in report and bool(re.search(r"20\d\d-\d\d-\d\d", report)))
    cov = re.search(r"coverage (\d+) checked / (\d+) unproven / (\d+) n/a", report)
    check("the sample report's coverage adds up to the 65 controls",
          bool(cov) and sum(int(x) for x in cov.groups()) == 65,
          cov.group(0) if cov else "no coverage line")
    todo = re.search(r"^DO FIRST\n((?:\d\. .+\n){1,3})", report, re.MULTILINE)
    check("the sample report lists up to three DO FIRST actions right after the counts",
          bool(todo))
    for control, route in (("R10", "/admin/export"), ("R4", "/api/invoices/")):
        check(f"the sample report names {control} and the route this test replays ({route})",
              bool(re.search(rf"\b{control}\b", report)) and route in report)
    check("the sample report quotes no full session cookie (redaction rule)",
          not re.search(r"session=[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{20,}", report))
    ids = re.findall(r"^## (?:CRITICAL|HIGH|MEDIUM|LOW) ([A-Z]\d+)\b", report, re.MULTILINE)
    missing = [i for i in ids if i not in replayed]
    check(f"every finding in the sample report's severity headings has a replay here ({len(ids) - len(missing)} of {len(ids)})",
          bool(ids) and not missing, f"no replay for {missing}")
    return finish()


def finish():
    print("-" * 60)
    print(f"{_total - len(failures)}/{_total} checks passed")
    if failures:
        print("FAILED:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
