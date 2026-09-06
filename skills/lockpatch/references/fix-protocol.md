# The fix protocol

Load this before you change any file. Phase 5 is where this skill can do real damage, and every rule
here exists because skipping it has broken somebody's app.

## The shape of one fix

Fixes happen one at a time, in severity order, each one a complete loop before the next begins.

```
1  PROPOSE   show the diff, the blast radius, and both halves of the paired test
2  APPROVE   the human says yes to THIS fix. Not to a batch
3  CHECKPOINT commit the working tree first, so `git reset` is the undo
4  APPLY     the smallest change that closes the hole
5  RE-PROVE  run the attacker's command. It must now fail
6  RE-PROVE  run the legitimate command. It must still succeed
7  BUILD     run the project's own build and tests
8  RECORD    write the before and after into the report, then move on
```

If step 5, 6, or 7 fails, go to the rollback rules below. Do not proceed to the next finding carrying
a broken fix.

## The paired test

This is the rule that separates a fix from a regression.

```
              attacker's request      legitimate user's request
before fix    succeeds  (the bug)     succeeds  (the product works)
after fix     FAILS                   STILL SUCCEEDS
```

Three of those four cells must be checked. The fourth, the legitimate request before the fix, is
what tells you the feature worked in the first place, so check it too when it is cheap.

**A fix that only satisfies the top-right cell is not a fix.** Returning 403 to everybody closes every
hole in the application and also closes the application.

Worked example, control R4:

| | Request | Expected before | Expected after |
| --- | --- | --- | --- |
| Attacker | `GET /api/orders/<B's id>` as user A | 200 with B's order | 403 or 404 |
| Legitimate | `GET /api/orders/<A's id>` as user A | 200 with A's order | 200 with A's order |

If you cannot write the legitimate half for a control, say so and hand the fix to the human. That is
a complete and honest outcome. Applying a change you cannot prove safe is not.

## Before you touch auth code

Auth is the highest-risk category in this skill. Extra rules apply:

- If the project has no test covering the auth path, **say that out loud before editing** and offer to
  write the test first. A user who declines has made an informed choice; one who was never told has not.
- Never change more than one auth control per approval.
- Never refactor while fixing. The diff should be readable as one idea.
- If the fix touches session creation, token verification, or the login handler, print the full diff
  rather than a summary. The user needs to see this one.

## Rollback rules

| What happened | What you do |
| --- | --- |
| The attacker's request still succeeds | The fix did not work. Revert it. Mark the finding `FIX FAILED, NEEDS HUMAN` with what you tried |
| The legitimate request now fails | You broke the feature. Revert immediately, before anything else. This is the worst outcome available and it takes priority over the finding |
| The build or tests broke | Revert that fix. Report which test broke, with its output |
| You are not sure whether it worked | Treat it as failed. Revert. `UNPROVEN` is an acceptable outcome; a false "fixed" is not |

**Never stack fixes.** If fix 3 failed and you left it in place, fix 4's verification is meaningless
because you no longer know which change caused what.

Revert with the checkpoint from step 3, not by hand-editing back. Hand-reverting is how a half-fix
survives.

## What you never do on your own initiative

These require their own explicit conversation, and they are never included in a "fix everything" yes.

- **Rewriting git history.** `git filter-repo`, `git filter-branch`, `git rebase`, any force push.
  See `secrets-runbook.md`.
- **Rotating a credential.** lockpatch writes the runbook. The human runs it. You do not have the
  provider console and you cannot verify the result.
- **Changing a production database.** Migrations that enable RLS are still schema changes. Propose the
  SQL, explain the lock behaviour, let the human run it against production.
- **Deleting data.** Ever. Including data you believe is a leaked backup.
- **Changing anything outside the repository.** DNS, a provider dashboard, a cloud console.
- **Installing a package** without saying which one, why, and what it adds to the dependency tree.

## Scope discipline

The fix closes the finding. It does not improve the file.

- No renaming, no reformatting, no reorganising imports, no "while I was in here".
- Match the surrounding code's idioms even when you would write it differently. A fix that looks
  foreign is a fix that gets reverted by the next developer who reads it.
- If the correct fix is large (an authorization layer that does not exist yet), propose the design and
  stop. Do not write a framework inside a security fix.

## Recording the outcome

Every attempted fix gets one of exactly these states in the report:

| State | Meaning |
| --- | --- |
| `FIXED` | Applied, attacker's request fails, legitimate request succeeds, build green |
| `FIX FAILED` | Applied and reverted. The finding stands. Includes what was tried |
| `DECLINED` | The human said no. The finding stands, and that is their call to make |
| `HANDED OVER` | Needs a human: history rewrite, rotation, production migration, or no legitimate twin |
| `OUT OF SCOPE` | Real, but outside what this skill may touch |

Never write `FIXED` from a diff alone. `FIXED` means you ran the two commands and read their output.
