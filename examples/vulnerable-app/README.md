# Paperboat, a deliberately vulnerable app

**Never deploy this.** It is a small invoice API with holes left in on purpose, so you can try
secure-my-app on something that is not yours to lose.

- One file, [`server.js`](server.js). No dependency, nothing to install.
- It listens on `127.0.0.1` only. Data lives in memory, so every start is the same state.
- Every name, email and amount in it is made up.

## Run it

```bash
node examples/vulnerable-app/server.js
```

```text
paperboat listening on http://127.0.0.1:4310
```

Set `PORT` to use another port.

## Point secure-my-app at it

Open your agent in `examples/vulnerable-app/`, with the server running in another terminal. Then type:

```text
/secure-my-app --report-only --live http://127.0.0.1:4310
```

It asks three questions. For this fixture the answers are:

1. Live? Yes, at `http://127.0.0.1:4310`. It is a local fixture and you own it.
2. Public repo? Yes.
3. Shared by more than one team? Yes, two teams share the data.

Two test accounts, so the two-account checks can run:

| Email | Password | Team |
| --- | --- | --- |
| `alice@paperboat.test` | `alice-demo-pass` | `team_1` |
| `bob@paperboat.test` | `bob-demo-pass` | `team_2` |

## What a run found

[`../sample-report.md`](../sample-report.md) is the report from a real run on this fixture. Your run
can differ: the rating is deterministic, the scan is not.

[`../../tests/test_fixture.py`](../../tests/test_fixture.py) starts this server and replays the request
behind each finding. It fails if a hole the report names stops answering the same way.
