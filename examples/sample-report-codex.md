> **A real run on Codex CLI, not an illustration.** OpenAI Codex CLI 0.169.0 (`codex exec`, model
> gpt-6.1-sol, reasoning effort low) wrote this report on 2026-11-17, against a copy of
> [`examples/vulnerable-app/`](vulnerable-app/README.md) committed as the only commit of a fresh git
> repo and served on 127.0.0.1:4311.
> Install: `npx skills add <this repo's local clone> -a codex`, which copied the skill to
> `.agents/skills/secure-my-app/`. That copy matched v0.3.0 except the `metadata.version` line,
> which still said 0.2.0 because the run came before the version bump.
> Prompt: use the secure-my-app skill with `--report-only --live http://127.0.0.1:4311`, plus the
> answers to the three phase 0 questions, since `codex exec` cannot ask them.
> The text below is the file the run wrote to `.secure-my-app/report.md`. One edit: its 47 em dashes,
> all list separators in the appendix and the ledger, became a colon or a period, because this repo
> bans em dashes. The redactions inside (the key, the path, hashes) were made by the run itself.
> The [Claude Code sample](sample-report.md) reported 11 findings on the same fixture. This run
> reported 5. It folded D3 and V2 into R10, and left D2, D5, D6 and V5 in the unproven appendix
> because it did not demonstrate them. The rating is deterministic, the scan is not.

VERDICT: DO NOT LAUNCH   coverage 18 checked / 6 unproven / 41 n/a   [static + live: http://127.0.0.1:4311]
findings: 2 critical  2 high  1 medium  0 low   scan: gitleaks yes, osv-scanner no, semgrep yes (2 local rules), trufflehog no
DO FIRST
1. R10  Require an authenticated admin for export and exclude password hashes.
2. K3  Replace the committed signing key and invalidate old sessions.
3. R4  Scope invoice lookups to the authenticated owner.

Report-only audit, 2026-11-17. No application changes, data mutations, dependency installation, commits, rotations or history rewrites. This is not a penetration test or compliance assessment. All data is synthetic; the launch gate describes the fixture, not a claim of Internet exposure. Bound to loopback; reachable by a stranger means a process/person able to reach the authorized local listener.

Scope: Node built-ins http/crypto; six routes; in-memory users/invoices; no database, browser bundle, uploads, webhooks, LLM, external providers, CI or npm dependencies. PORT is the only referenced environment variable; no .env files found. Repo public and two teams confirmed by the user. No git remote configured; one tracked commit. Existing .agents/ and skills-lock.json preserved.

Evidence: 23 HTTP requests total, all to the named host; 16 saved results plus 7 requests before two local collection errors. No redirects or automatic retries; repeated sign-ins only resulted from collecting headers correctly. No failed-password burst, PATCH or DELETE. Proof labels distinguish executed results, static code and unrun recipes. HTTP results are in surface.json with cookies, secrets and password hashes redacted.

## CRITICAL  R10  Anonymous export exposes both teams and password hashes

WHAT     Anyone who reaches the local fixture can download every user and invoice without signing in.

WHERE    server.js:101

PROOF    [executed] curl -s http://127.0.0.1:4311/admin/export | python3 -c 'import sys,json; d=json.load(sys.stdin); print({"users":len(d["users"]),"invoices":len(d["invoices"]),"user_fields":list(d["users"][0])})'
Observed equivalent request: HTTP 200; users=3; invoices=3; user_fields=[id,email,team,role,password_hash]. Hash values redacted. [static] server.js:101-102 returns { users, invoices } without session or role checks; lines 12,15-17 use unsalted SHA-256.

IMPACT   All invoice customers, emails, amounts, team membership and password hashes for both teams. PUBLIC/ALL_DATA maps to CRITICAL. D1, D3, V2, V6 and F10 link here rather than inflate the finding count.

FIX      At the start of the export handler: `const user = sessionUser(req); if (!user) return send(res,401,{error:"sign in first"}); if (user.role !== "admin") return send(res,403,{error:"forbidden"});` Replace `{ users, invoices }` with explicit safe projections and a bounded page, e.g. `{ users: users.slice(0,100).map(({id,email,team,role}) => ({id,email,team,role})), invoices: invoices.slice(0,100).map(({id,owner,team,customer,total_cents}) => ({id,owner,team,customer,total_cents})) }`. This assumes a global admin is intended; confirm team-admin scope before implementation. Replace password digests with per-user salted scrypt/Argon2id and migrate fixture auth together; do not merely hide hashes and leave weak storage.

VERIFY   [recipe, NOT RUN] Repeat anonymous export -> 401; Alice and Bob cookies -> 403; authorized admin -> 200 with approved field list, no password_hash and at most the chosen page size. Test tenant-admin scoping if applicable. Recheck after R6 is closed so members cannot set role=admin.

STATUS   OPEN

## CRITICAL  K3  Committed signing secret still forges accepted sessions

WHAT     The public source contains the active cookie-signing secret, allowing a visitor to impersonate a known user.

WHERE    server.js:10

PROOF    [static] server.js:10 defines SESSION_SECRET="pape..." (redacted); lines 26-40 sign and verify with it. Tracked in sole commit 2c1d13c. [executed] A Python urllib request computed a valid HMAC using the source value and GET /api/invoices with sub=u_2. HTTP 200; returned invoices 1042 and 1043, owner=u_2, team=team_2, without a password or a login session. Cookie/key omitted. Gitleaks tree/history scans found no leaks: a demonstrated scanner miss, not a pass.

IMPACT   Bob’s invoice data via a forged identity. The live-unrotated-credential override makes this CRITICAL; the direct matrix would also place PUBLIC/OTHER_USERS at CRITICAL. K4 and K5 are the same credential.

FIX      Replace line 10 with `const SESSION_SECRET = process.env.SESSION_SECRET; if (!SESSION_SECRET) throw new Error("SESSION_SECRET required");`. Operator: generate a fresh random secret, inject it privately and restart the app, invalidating every old cookie. Prove the old cookie is refused before optionally scrubbing history. Never rotate automatically; never rewrite history before rotation. Collaborators must re-clone if history is rewritten.

VERIFY   [recipe, NOT RUN] Replay the previously forged cookie -> 401, not 500; sign in as each legitimate account using the new server secret -> 200, own list unchanged. A stale committed-key-generated cookie must also return 401. See the safe reproducer below.

STATUS   OPEN

## HIGH  R4  Invoice IDs bypass ownership and team isolation

WHAT     Any signed-in member can read an invoice belonging to the other team by changing the ID.

WHERE    server.js:89

PROOF    [executed] GET /api/invoices/1042 with Alice cookie -> 200, id=1042 owner=u_2 team=team_2. Bob own list confirms 1042 exists. GET /api/invoices/1041 with Bob cookie -> 200, owner=u_1 team=team_1. Alice own /1041 -> 200; anonymous /1042 -> 401. [static] invoices.find((i) => i.id === id) at server.js:89 lacks owner or team predicate.

IMPACT   The other team’s customer emails, invoice totals and bank-account suffixes. ANY_USER/OTHER_USERS maps to HIGH. The current API list is owner-scoped, so propose matching that intended behavior.

FIX      Replace line 89 with `const invoice = invoices.find((i) => i.id === id && i.owner === user.id);` and retain the existing 404. If team-wide sharing is intended, use `i.team === user.team` instead after locking profile team changes under R6.

VERIFY   [recipe, NOT RUN] After sign-ins using the README accounts, `curl -i -b "$ALICE_COOKIE" http://127.0.0.1:4311/api/invoices/1042` and Bob /1041 -> 404 or 403. Alice /1041 and Bob /1042 -> 200. Anonymous both -> 401. No record creation/deletion needed.

STATUS   OPEN

## HIGH  R6  Profile update accepts role and identity fields

WHAT     A signed-in member can overwrite their own server-side role, identity, team and password hash through the profile body.

WHERE    server.js:97

PROOF    [executed] Local Semgrep rule `Object.assign(user, await readJson(req))` matched server.js:97 (exit 0, no errors). [static] lines 94-98 gate only on a session, parse arbitrary JSON and assign every field to the shared user object; no schema, allowlist or downstream setter blocks role="admin". This establishes stored privilege-field overwrite, not access to a protected admin action. No PATCH was executed.

IMPACT   Member role becomes admin and identity/team fields become attacker-controlled. ANY_USER/SELF_ESCALATION maps to HIGH. Static reach/control/impact are complete, but runtime mutation remains deliberately untested.

FIX      Replace line 97 with `const body = await readJson(req); if (Object.keys(body).some(k => k !== "email") || typeof body.email !== "string" || body.email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email)) return send(res,400,{error:"invalid profile"}); user.email = body.email;`. This defines email as the sole editable fixture field; a production email change also needs verification and uniqueness. Keep role, id, team and password_hash server-controlled.

VERIFY   [recipe, NOT RUN; mutates data, use disposable fixture only] PATCH /api/me as Alice with {"role":"admin"} -> 400 and authoritative in-memory role unchanged; legitimate allowed email update -> 200 and readback matches. Repeat forbidden id/team/password_hash. No automatic mutation tests were installed under report-only scope.

STATUS   OPEN

## MEDIUM  V3  Malformed login reveals absolute paths and stack frames

WHAT     An anonymous malformed JSON login returns a full server exception stack.

WHERE    server.js:110

PROOF    [executed] `curl -i -H "Content-Type: application/json" --data-binary "{" http://127.0.0.1:4311/login` -> HTTP 500; error SyntaxError: Expected property name or ...; stack includes IncomingMessage.<anonymous> (.../paperboat/server.js:54:28), node:events and node:internal/streams/readable. Exact returned stack is in surface.json. Authenticated GET /api/invoices/not-an-integer also returned 500 with server.js:88:38. [static] line 110 serializes err.stack.

IMPACT   Source layout, framework/runtime internals and parser details to any visitor. PUBLIC/INFO maps to MEDIUM. P2 shares this demonstrated malformed-input failure.

FIX      Replace line 110 with `send(res, err instanceof SyntaxError || err instanceof TypeError ? 400 : 500, {error: err instanceof SyntaxError || err instanceof TypeError ? "invalid request" : "internal error"});`. Validate route IDs and login bodies before use; use internal redacted logging instead of returning exception strings.

VERIFY   [recipe, NOT RUN] Repeat malformed login and bad invoice ID -> 400 JSON without stack, filesystem path or runtime name; correct login -> 200 and legitimate invoice -> 200. A genuine unexpected server error -> generic 500, not a fake success.

STATUS   OPEN

## Reproduction helpers

[recipe] Set URL and session cookies locally; do not print or commit cookies. Obtain Alice/Bob cookies with POST /login JSON using their README test credentials. For example `curl -s -c "$COOKIE_JAR" -H "Content-Type: application/json" --data-binary @/path/to/private-login.json http://127.0.0.1:4311/login`, then `curl -i -b "$COOKIE_JAR" http://127.0.0.1:4311/api/invoices/1042`. Use one jar per account. No helper file or test suite was added because this run ends with the two report artifacts.

Signing-key proof, equivalent to executed probe; reads the key without displaying it. This helper is PRE-FIX ONLY: after the proposed environment-variable change the literal lookup will no longer work. For after-fix verification, retain the old forged cookie securely outside these artifacts and replay that same old cookie; never regenerate it with the new key. This command is a reproduction recipe, not an additional request executed by the report:

```python
import re, pathlib, json, base64, hmac, hashlib, urllib.request
key = re.search(r'const SESSION_SECRET = "([^\"]+)"', pathlib.Path("server.js").read_text()).group(1)
b64 = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
body = b64(b'{"sub":"u_2"}')
mac = b64(hmac.new(key.encode(), body.encode(), hashlib.sha256).digest())
req = urllib.request.Request("http://127.0.0.1:4311/api/invoices", headers={"Cookie": "session="+body+"."+mac})
with urllib.request.urlopen(req) as response:
    print(response.status, [row["id"] for row in json.load(response)])
# pre-fix observed: 200 [1042, 1043]; replay the securely retained OLD cookie after rotation -> 401
```

## UNPROVEN appendix

- **D2**: Both login cookies lack HttpOnly, Secure, SameSite; no browser theft/CSRF demonstrated. Settle: [recipe] Inspect Set-Cookie evidence; demonstrate a browser-readable session in a same-origin browser context; do not infer CSRF.
- **D5**: No expiry/revocation fields in sign/sessionUser; no aged/revoked-session experiment. Settle: [recipe] On a disposable instance issue a session, invalidate it through a designed revocation mechanism and replay GET /api/invoices; no mechanism exists currently.
- **D6**: No limiter in complete source; no repeated-attempt consent/probe. Settle: [recipe] With separate consent, send at most 12 invalid POST /login attempts and check per-account and per-IP counters; expect 429 before twelfth.
- **P4**: Only protected write is PATCH; cookie has no explicit SameSite but browser defaults and lack of CORS limit attackability. Settle: [recipe] In a separate disposable browser fixture test a foreign-origin PATCH with credentials; inspect preflight and stored state. Do not run a write in this report-only audit.
- **V5**: No security-event logging in complete source; no independent audit-integrity or incident impact demonstrated. Settle: [recipe] Inspect failed-login/denial events in an operator-provided sink after POST /login with invalid credentials; no sink is configured here.
- **F9**: Same generic failure body statically; account timing distinctions not measured. Settle: [recipe] On an isolated instance compare known-email/wrong-password and unknown-email latency distributions at an agreed request budget.

## Coverage ledger

Checked means PASS plus FAIL, not a claim all controls passed. Linked FAILs do not create duplicate findings. PASS controls contribute to the summary count; detailed control outcomes and evidence are in surface.json.

5 PASS; 13 FAIL; 6 UNPROVEN; 41 N/A = 65 controls.

- K1: N/A. No browser or admin-provider keys.
- K2: N/A. No public env prefixes or client bundle.
- K6: N/A. No client database key.
- K7: N/A. No config/secrets/credentials file; literal key covered by K3.
- K8: N/A. No third-party provider keys.
- D4: N/A. Custom HMAC tokens, no JWT.
- D7: N/A. No reset or magic link.
- D8: N/A. No MFA.
- R1: N/A. In-memory arrays; no RLS database.
- R2: N/A. No RLS.
- R3: N/A. No RLS.
- R7: N/A. No database enforcing privileged columns; in-memory write at R6.
- R8: N/A. No storage buckets.
- R9: N/A. No database views/functions.
- P1: N/A. No SQL/ORM.
- P3: N/A. No HTML/client render sink.
- P6: N/A. No outbound URL fetch.
- P7: N/A. No redirects.
- P8: N/A. No webhooks.
- P9: N/A. All responses application/json, no HTML surface.
- P10: N/A. Authorized target is loopback-only HTTP fixture; no public TLS deployment.
- P11: N/A. No GraphQL.
- P12: N/A. No file-serving reads.
- V1: N/A. No full IBAN/cards/provider tokens; iban_last4 is minimized. Password hashes covered D3; signing key K3.
- V7: N/A. No delete feature or retention promise.
- V8: N/A. No third-party scripts/analytics.
- F1: N/A. No paid calls, mail or unbounded external queries; fixed in-memory rows.
- F2: N/A. No public signup/contact submission; login covered D6.
- F3: N/A. No uploads.
- F4: N/A. No checkout or invoice-price write route.
- F5: N/A. No payment/order-state/coupon workflow.
- F6: N/A. No LLM.
- F7: N/A. No model output.
- F8: N/A. No model spend.
- S1: N/A. No third-party app packages; no advisory lookup needed. Node runtime advisories unassessed.
- S2: N/A. No package installs; skills-lock.json concerns installed skill, not app dependencies.
- S3: N/A. No dependency hooks; sole start script node server.js was read, not executed.
- S4: N/A. No CI workflows.
- S5: N/A. No preview or external DB configuration.
- S6: N/A. No workflow permissions.
- S7: N/A. No actions/container images.

## Scanner coverage

[executed] `gitleaks detect --no-git --redact --no-banner --source .`: no leaks found, about 202002 bytes including installed skill files. `gitleaks detect --redact --no-banner --source .`: 1 commit, about 6560 bytes, no leaks found. Manual tracing found the active custom SESSION_SECRET despite both scans. No clean-scan PASS was inferred.

[executed] Semgrep 1.157.0, two temporary local JavaScript rules, no registry config; metrics and version check disabled for the scan. Patterns for Object.assign(user, await readJson(req)) and stack-bearing send matched lines 97 and 110; exit 0, no errors. Other controls used source/DETECT inspection, not a claimed OWASP ruleset scan. Temporary rules removed. osv-scanner and trufflehog absent; dependency fallback is manifest inspection (zero third-party packages), secrets fallback is manual source/history trace plus gitleaks. No provider verification or advisory network calls. No advisory data date applies because no advisory scan was run; installed Node runtime version/advisories remain unassessed. Snyk skipped because account required; BFG/history cleaning and commercial DAST/cloud posture tools outside this report.

## Not checked, and why

No mutations, destructive probes, rate-limit bursts, load, exploit chaining, infrastructure testing, browser CSRF/XSS demonstration, expiry/revocation timing experiment or runtime advisory lookup. No build/test script exists beyond start; the existing server was used and never restarted. The two-account reads ran against existing fixture rows; write/delete checks and a persistent test-suite addition were omitted to honor report-only and the requested two-artifact stop.

Outside visibility: cloud IAM roles/trust policies; network boundaries, security groups and firewalls; DNS, registrar access and subdomain takeover; physical/device security; social engineering/support-desk takeover; insider access; services or logins not supplied; third-party systems; race conditions and timing attacks requiring load; cryptographic implementation review (including HMAC timing leakage); and the team’s incident-response capability. A clean report would not certify safety; this report confirms specific exposures only. All findings remain OPEN. No fixes offered or applied.

Independent review: a separate read-only agent checked evidence, severity mapping, 65-control coverage, redaction and scope. Its two documentation corrections (saved request count and pre-fix-only signing-key helper) were applied. No fix was executed.
