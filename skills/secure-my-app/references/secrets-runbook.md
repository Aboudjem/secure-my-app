# The secrets runbook

Load this for any KEYS finding. The order in this file is the whole point, and almost everyone gets
it backwards.

## The order. Do not reorder it.

```
1  FIND      what leaked, and where
2  ASSESS    is it still live, and how bad is what it opens
3  ROTATE    issue a new credential, invalidate the old one     <-- the human does this
4  REPLACE   update the app to use the new one, deploy
5  SCRUB     only now, remove it from git history                <-- the human does this
6  RE-CLONE  tell everyone with a copy of the repo
7  PREVENT   gitignore, pre-commit hook, CI scan
```

**Rotation comes before scrubbing, always.**

A secret that was pushed to a public repository is compromised the moment it lands. Bots scrape new
commits within seconds. GitHub keeps unreferenced objects reachable by SHA, and forks, mirrors, CI
caches, and anyone's local clone keep their own copies. Rewriting history removes the secret from
*your* branch and from nowhere else.

Scrubbing without rotating produces the worst possible outcome: a repository that looks clean, a
developer who believes the problem is solved, and a live key in somebody's collection.

Say this to the user in plain words when you report a KEYS finding. It is the single most valuable
sentence in this file.

## Step 1. Find

Run K3 and K4 from `controls.md`. Prefer `gitleaks` when it is installed. Where you fall back to grep,
say so in the report, because grep over history is shallower and the user should know.

**Redaction is not optional.** Every reference to a found secret in a report, a log, a commit message,
or a chat line is the provider prefix plus four characters and nothing more:

```
found: sk_live_51H...   (Stripe secret key, .env.local:3, commit 4a91c2e)
```

Never the full value. Never "for confirmation". A findings file that quotes secrets is a second,
better-organised copy of the leak, and it usually ends up in a shared folder.

## Step 2. Assess

Two questions decide the urgency, and both are answered by the human:

1. **Is it still live?** A rotated key is a cleanup task. A live key is an incident.
2. **What does it open?** A read-only analytics key and a Stripe secret key are not the same finding
   even though both are "a leaked key".

Rank by what the key opens, not by how it was found. Order the user's work that way.

If the repository is or ever was public, treat every secret in it as compromised. Do not soften this
with "probably fine". You do not know, and the failure mode is expensive.

## Step 3. Rotate. The human does this.

secure-my-app never rotates a credential. You do not have the provider console, you cannot see whether
the new key propagated, and a rotation you get half-right takes the app down.

Write the runbook instead. One block per leaked credential:

```
CREDENTIAL   Stripe secret key
FOUND        .env.local:3, still present in history at 4a91c2e
OPENS        charge cards, refund, read the full customer list
ROTATE AT    https://dashboard.stripe.com/apikeys  ->  Roll key
ORDER        create the new key, deploy it, THEN revoke the old one
DOWNTIME     none if you deploy before revoking. Revoking first breaks checkout
AFTER        confirm the old key returns 401
```

The create-then-revoke order matters. Revoking first is the standard way a rotation becomes an outage.

For a key you believe was actively used by an attacker, the order inverts: revoke immediately and
accept the downtime. Say which situation you think this is, and let the human decide.

## Step 4. Replace

The app reads the new value from the environment. If the fix requires a code change, it goes through
the normal fix protocol with its own approval.

Verify the app works on the new credential before anyone touches history.

## Step 5. Scrub. Also the human, with an explicit yes.

Only after rotation is confirmed. This step is optional; a rotated key in history is inert. Scrub
because you do not want the string there, not because it makes you safe.

**Never run any of this yourself. Print it.**

```bash
# git-filter-repo is the maintained tool. git filter-branch is deprecated and slow
pip install git-filter-repo

# back up first. this rewrites every commit hash
git clone --mirror git@github.com:you/repo.git repo-backup.git

git filter-repo --path .env.local --invert-paths
# or, to replace a literal wherever it appears:
git filter-repo --replace-text secrets.txt

git push --force --all
git push --force --tags
```

State the consequences before the user runs it:

- Every commit SHA changes. Open pull requests break. Anything referencing a commit by SHA breaks.
- Every collaborator must delete their clone and clone again. A `git pull` on an old clone
  reintroduces the deleted objects.
- Forks keep the secret. You cannot reach them.
- The provider may already have cached views. GitHub keeps unreferenced objects; ask their support to
  purge if it matters.

## Step 6. Tell everyone

A history rewrite that half the team does not know about undoes itself the next time somebody pushes.
Give the user the message to send:

> I rewrote the history of `<repo>` to remove a leaked credential. Delete your local clone and clone
> again. Do not pull or push from your old copy, and do not merge a branch based on it without
> rebasing onto the new history first.

## Step 7. Prevent

Cheap, and it is the only step that stops the next one.

```bash
# .gitignore
.env
.env.*
!.env.example

# already tracked? stop tracking without deleting the file
git rm --cached .env

# a pre-commit hook, if gitleaks is installed
gitleaks protect --staged --redact
```

Add the scan to CI so it fails a pull request rather than being noticed a year later. Commit a
`.env.example` with the key *names* and empty values, so nobody needs the real file to run the project.

## Things that are not fixes

- Deleting the file in a new commit. The old commit still has it.
- A force push over one commit. The object is still reachable by SHA.
- Making the repository private. Every existing clone and fork keeps its copy.
- Renaming the variable.
- Rewriting history without rotating. This is the one that feels like a fix and is not.
