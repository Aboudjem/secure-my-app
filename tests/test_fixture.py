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


def check(name, ok, detail=""):
    global _total
    _total += 1
    tag = "PASS" if ok else "FAIL"
    print(f"{tag}: {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(port, method, path, body=None, cookie=None):
    """One HTTP request. Returns (status, headers, parsed JSON or raw text)."""
    data = json.dumps(body).encode() if body is not None else None
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


def forge(secret, subject):
    """A session cookie signed with the secret committed in server.js."""
    body = base64.urlsafe_b64encode(json.dumps({"sub": subject}).encode()).rstrip(b"=").decode()
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"session={body}.{base64.urlsafe_b64encode(mac).rstrip(b'=').decode()}"


def main():
    source = open(SERVER, encoding="utf-8").read()
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
    proc = subprocess.Popen([node, SERVER], env={**os.environ, "PORT": str(port)},
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        up = False
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

        # --- D2: the session cookie has no flags ---
        check("D2 hole: the session cookie is set without HttpOnly, Secure or SameSite",
              bool(a_raw) and not re.search(r"httponly|secure|samesite", a_raw, re.I), a_raw)

        # --- K3: the signing secret is a literal in the repo, so anyone can mint a session ---
        secret = re.search(r'const SESSION_SECRET = "([^"]+)"', source)
        check("K3 hole: the session signing secret is a string literal in server.js", bool(secret))
        if secret:
            status, _, mine = call(port, "GET", "/api/invoices", cookie=forge(secret.group(1), "u_2"))
            check("K3 hole: a cookie forged with that secret is accepted as bob",
                  status == 200 and [i["id"] for i in mine] == [1042, 1043], status)
            check("K3 control: a cookie forged with another secret is refused with 401",
                  call(port, "GET", "/api/invoices", cookie=forge("not-the-secret", "u_2"))[0] == 401)

        # --- D3: unsalted SHA-256 for passwords ---
        alice_hash = next(u["password_hash"] for u in export["users"] if u["id"] == "u_1")
        check("D3 hole: the stored hash is a bare SHA-256 of the password, no salt",
              alice_hash == hashlib.sha256(b"alice-demo-pass").hexdigest())

        # --- R6: mass assignment. Last, because it changes state. ---
        status, _, me = call(port, "PATCH", "/api/me", {"role": "admin"}, cookie=alice)
        check("R6 hole: PATCH /api/me with {role: admin} makes a member an admin",
              status == 200 and me.get("role") == "admin", me)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

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
