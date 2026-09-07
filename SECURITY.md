# Security Policy

`secure-my-app` is a security tool, so this file has two jobs. It says how secure-my-app itself is built to
be safe, and it says how to report a hole **in secure-my-app**. Read both. A tool people trust about
their own security is a tool worth attacking.

**secure-my-app never transmits your findings, your code, or your requests anywhere.** The skill is
Markdown. It has no runtime dependency, no API key, no telemetry, no analytics, and no endpoint of
its own to call. Everything it learns about your app is written to `.secure-my-app/` inside your own
project and stays there. If you delete that directory, nothing survives it.

The two qualifications on that sentence, stated plainly so you are not surprised:

1. **Proving a finding means sending a request to a target you named.** That is the point of the
   tool. Those requests reach your own app, your own staging host, or whatever host you pointed it
   at, and they will appear in that host's logs. secure-my-app never widens the target on its own.
2. **The audit runs inside your agent, which is a network client.** If you ask secure-my-app to check a
   dependency version against an advisory database, that lookup reaches a third party, and the
   query is derived from your dependency list. Say so up front and secure-my-app skips the lookup and
   marks the check as not run rather than guessing.

## How the skill is built to be safe

- **It reads, it proves, and then it stops.** The AUDIT phase reads the project and issues the
  requests needed to demonstrate what it found. It changes nothing. The FIX phase is a separate
  phase that a human starts.
- **Proof or it is not a finding.** Every finding carries the request that demonstrates it and the
  response that came back. Anything believed but not reproduced is labelled a **suspicion**, in
  that word, and is never counted or ranked with the findings. This is the rail that keeps a
  security report from being a list of plausible-sounding guesses that someone then acts on.
- **No fix is applied without a per-finding human approval.** One finding, one diff, one answer.
  There is no batch mode, no auto-apply flag and no severity above which the approval is skipped,
  because the blast radius of a wrong authorization fix is measured per finding.
- **Every applied fix is re-verified with two commands, not one.** The proof request is run again
  and must now fail, and the user's own authenticated path is run again and must still work. A fix
  that closes the hole and locks the owner out is a broken fix, and only the second command finds
  that.
- **Secrets by location, never by value.** When the finding is an exposed credential, the report
  names the file, the line, or the environment variable, and prints a redacted form. The raw value
  is never written into the report, the proof, or anywhere else under `.secure-my-app/`.
- **The output is gitignored on creation.** secure-my-app appends `.secure-my-app/` to `.gitignore`
  idempotently and creates `.gitignore` when the project has none. A findings report is a map of
  what still works, so committing one publishes the hole before the fix lands.
- **History is never rewritten and evidence is never destroyed.** No amend, no rebase, no
  force-push, no history filter, and no deletion of the file that holds the evidence for a finding.
  A credential found in git history is reported for **rotation**, which is your action to take,
  because the key is compromised whether or not the commit still exists.
- **Anything the audit reads is DATA, never instructions.** A response body, an error page, a stack
  trace, a log line, an issue comment, a fetched page: none of it can change the plan, the
  severity, the approval state, the fix, or the report. A tool whose whole job is pointing itself
  at hostile input has to hold this rail absolutely.
- **Only the targets you named.** The skill never expands to a host, a subdomain, a production
  environment, or a third-party service you did not name, and it never treats "it is in the same
  organisation" as authorization.
- **No remote fetch-and-execute.** Neither the skill nor anything it writes downloads and runs
  remote instructions or code.

## What counts as a security issue here

This section is about vulnerabilities **in secure-my-app**, not in the app you audited with it. Please
report any of the following:

- A path by which secure-my-app **writes a credential's value** into the report, a proof, or anywhere
  else under `.secure-my-app/`, rather than its location and a redacted form.
- A path by which secure-my-app **transmits findings, source, requests, or responses off the machine**:
  telemetry, an upload, a paste service, an issue body, a webhook, anything.
- A way a fix could be **applied without the per-finding approval**, or a way an approval for one
  finding could be made to cover another.
- A way a fix could be **reported as verified without both re-runs**, including a re-run that is
  faked, skipped, cached, or satisfied by an error that is not the proof failing.
- A way **content the audit reads** (a response body, a log, an issue, a fetched page) could steer
  the plan, the severity, the approval state, the applied fix, or the report.
- A way secure-my-app could be made to **act against a host the user did not name**, or to treat
  unauthorized scanning as authorized.
- A path by which secure-my-app could **rewrite git history, force-push, or delete the evidence** for a
  finding.
- A way the **`.secure-my-app/` gitignore step could be bypassed**, so a findings report gets committed.
- Anything that could **leak credentials, tokens, or private project data** off the machine.

## How to report a vulnerability

**Please do not open a public issue for a security problem.**

Email **boudjemaa.adam@gmail.com** with:

- A description of the issue and its impact.
- Steps to reproduce.

You will get a response within 48 hours. Once a fix is ready, the issue will be disclosed
responsibly with credit to the reporter if wanted.

**If you found a hole in your own app using secure-my-app, that is not a secure-my-app vulnerability.** Do
not send it here and do not file it as an issue. Fix it, and if it belongs to someone else, follow
that project's own disclosure process.

## Your responsibility when running it

- **Only audit what you own or are authorized to test.** Proving a finding means sending a real
  request to a real host. On a system you do not own, that is unauthorized access in most
  jurisdictions, regardless of intent, and secure-my-app cannot grant you permission you do not have.
  Get it in writing, and keep the scope to what the writing covers.
- **Never commit `.secure-my-app/`.** The skill gitignores it, but check. The report tells a reader
  exactly which door is still open.
- **Redact before you share.** A finding pasted into a chat, an issue or a ticket carries the host,
  the path, the headers and sometimes the token. Replace them with placeholders first.
- **Read the diff before you approve it.** The approval prompt exists so a human looks. An
  authorization fix that is slightly too wide breaks your users, and one that is slightly too
  narrow leaves the hole open. Neither is visible from the summary line.
- **Run the login check yourself once.** secure-my-app runs it too, but the path it knows about is the
  one you told it. If your app has a second way in (an admin console, a mobile client, an API key
  for a partner), that path is yours to re-test after a fix.
- **A clean report is not a certificate.** secure-my-app reports what it checked and what it proved, and
  the checks it could not run are listed as not run. Absence of a finding is absence of a proof,
  not evidence of safety. It is not a penetration test and it is not a compliance audit.
- **Rotate anything that leaked.** If a credential appears in the report, it is compromised.
  Rotating it is the fix; deleting the commit is not.
