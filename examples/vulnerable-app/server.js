// Paperboat: a deliberately vulnerable invoice API. It exists so secure-my-app has
// something real to find. Never deploy it. It binds to 127.0.0.1 only, has no
// dependency, and keeps its data in memory, so every start is the same state.
"use strict";

const http = require("node:http");
const crypto = require("node:crypto");

const PORT = Number(process.env.PORT || 4310);
const SESSION_SECRET = "paperboat-dev-secret";

const sha256 = (s) => crypto.createHash("sha256").update(s).digest("hex");

const users = [
  { id: "u_1", email: "alice@paperboat.test", team: "team_1", role: "member", password_hash: sha256("alice-demo-pass") },
  { id: "u_2", email: "bob@paperboat.test", team: "team_2", role: "member", password_hash: sha256("bob-demo-pass") },
  { id: "u_3", email: "root@paperboat.test", team: "team_1", role: "admin", password_hash: sha256("root-demo-pass") },
];

const invoices = [
  { id: 1041, owner: "u_1", team: "team_1", customer: "Harbor Bakery", customer_email: "accounts@harbor-bakery.test", total_cents: 18400, iban_last4: "4471" },
  { id: 1042, owner: "u_2", team: "team_2", customer: "Northside Dental", customer_email: "billing@northside-dental.test", total_cents: 92000, iban_last4: "0038" },
  { id: 1043, owner: "u_2", team: "team_2", customer: "Kite and Co", customer_email: "pay@kite-and-co.test", total_cents: 4150, iban_last4: "7712" },
];

function sign(payload) {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const mac = crypto.createHmac("sha256", SESSION_SECRET).update(body).digest("base64url");
  return `${body}.${mac}`;
}

function sessionUser(req) {
  const cookie = (req.headers.cookie || "").split(";").map((c) => c.trim()).find((c) => c.startsWith("session="));
  if (!cookie) return null;
  const [body, mac] = cookie.slice("session=".length).split(".");
  if (!body || !mac) return null;
  const want = crypto.createHmac("sha256", SESSION_SECRET).update(body).digest("base64url");
  if (mac !== want) return null;
  const { sub } = JSON.parse(Buffer.from(body, "base64url").toString("utf8"));
  return users.find((u) => u.id === sub) || null;
}

function send(res, status, data, headers = {}) {
  res.writeHead(status, { "content-type": "application/json", ...headers });
  res.end(JSON.stringify(data));
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk) => (raw += chunk));
    req.on("end", () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch (err) {
        reject(err);
      }
    });
  });
}

async function route(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const path = url.pathname;

  if (req.method === "GET" && path === "/") {
    return send(res, 200, { app: "paperboat", note: "deliberately vulnerable fixture, local use only" });
  }

  if (req.method === "POST" && path === "/login") {
    const { email, password } = await readJson(req);
    const user = users.find((u) => u.email === email && u.password_hash === sha256(String(password)));
    if (!user) return send(res, 401, { error: "wrong email or password" });
    return send(res, 200, { ok: true }, { "set-cookie": `session=${sign({ sub: user.id })}; Path=/` });
  }

  if (req.method === "GET" && path === "/api/invoices") {
    const user = sessionUser(req);
    if (!user) return send(res, 401, { error: "sign in first" });
    return send(res, 200, invoices.filter((i) => i.owner === user.id));
  }

  const byId = path.match(/^\/api\/invoices\/([^/]+)$/);
  if (req.method === "GET" && byId) {
    const user = sessionUser(req);
    if (!user) return send(res, 401, { error: "sign in first" });
    const id = Number(byId[1]);
    if (!Number.isInteger(id)) throw new TypeError(`invoice id must be an integer, got "${byId[1]}"`);
    const invoice = invoices.find((i) => i.id === id);
    if (!invoice) return send(res, 404, { error: "no such invoice" });
    return send(res, 200, invoice);
  }

  if (req.method === "PATCH" && path === "/api/me") {
    const user = sessionUser(req);
    if (!user) return send(res, 401, { error: "sign in first" });
    Object.assign(user, await readJson(req));
    return send(res, 200, { id: user.id, email: user.email, team: user.team, role: user.role });
  }

  if (req.method === "GET" && path === "/admin/export") {
    return send(res, 200, { users, invoices });
  }

  return send(res, 404, { error: "not found" });
}

const server = http.createServer((req, res) => {
  route(req, res).catch((err) => {
    send(res, 500, { error: String(err), stack: err.stack });
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`paperboat listening on http://127.0.0.1:${PORT}`);
});
