<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-dark.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-light.svg" alt="secure-my-app：找出陌生人能从你的应用里拿走什么，然后把它堵上，并证明它确实堵上了。" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml/badge.svg" alt="validate"></a> <a href="https://github.com/Aboudjem/secure-my-app/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a> <a href="https://github.com/Aboudjem/secure-my-app/stargazers"><img src="https://img.shields.io/github/stars/Aboudjem/secure-my-app?color=2BE8C8&labelColor=0A0F1C" alt="stars"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <b>简体中文</b> · <a href="ja.md">日本語</a> · <a href="es.md">Español</a> · <a href="fr.md">Français</a>
  <br><sub>本翻译可能落后于英文原文。<!-- may-lag --></sub>
</p>

<p align="center">
  <strong>找出陌生人能从你的应用里拿走什么。然后把它堵上，并证明它确实堵上了。</strong>
</p>

## 它做什么

- 读的是整个应用，不是一段 diff，并对它运行 65 项有名字的安全检查。
- 只有拿得出证明它的命令和那条命令的真实输出，才会报出一个洞。
- 一次修一个，每一个都先经你批准，然后重新证明它已经堵上。

## 安装

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install secure-my-app@10x       # Claude Code
npx skills add Aboudjem/secure-my-app         # Cursor, Codex, Copilot, Gemini CLI, 70+ others
```

## 你会得到什么

`.secure-my-app/report.md` 以一行判定开头，之后每条发现都按同样顺序带同样的七个字段。

```text
SECURE-MY-APP   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
findings: 2 critical  1 high  1 medium  0 low
CRITICAL  R1  Anyone can read every row of bookings
WHAT     Row level security is off on public.bookings, so the publishable key reads it all.
WHERE    supabase/migrations/0002_bookings.sql:11
PROOF    [executed] curl -s "$URL/rest/v1/bookings?select=*" -H "apikey: sb_publishable_7f2a..."
                    -> 200, 1204 rows: id, user_id, email, phone, address_line1, total_cents
IMPACT   Every customer's email, phone, address and what they paid, to anyone with devtools.
FIX      alter table public.bookings enable row level security;
         create policy "own" on public.bookings for select to authenticated
           using ((select auth.uid()) = user_id);
VERIFY   anon curl returns []; user A reads their own row; user B gets empty, not an error.
STATUS   OPEN
```

`PROOF` 是一条真实的命令和它真实的输出，密钥已打码。`VERIFY` 是那条命令：它的输出必须先变化，才能说某件事修好了。
有了 `.secure-my-app/surface.json`，第二次运行给你的是一份差异，而不是又一堵文字墙。

## 它检查什么

七个组共 65 项控制，顺序就是攻击者尝试的顺序（[完整目录](https://github.com/Aboudjem/secure-my-app/blob/main/docs/controls.md)）。

| 分组 | 涵盖 |
| --- | --- |
| KEYS (8) | 仓库里的密钥、密钥泄露、密钥权限范围、轮换 |
| DOOR (9) | 登录、会话、Cookie、密码存储、令牌 |
| ROOMS (10) | 行级安全、IDOR、租户隔离、批量赋值 |
| PIPES (13) | 注入、XSS、CSRF、SSRF、CORS、重定向、Webhook、响应头 |
| VAULT (8) | 静态加密、响应的形状、报错泄露、日志、备份 |
| FLOOR (10) | 限流、机器人、上传、价格篡改、AI 功能 |
| SUPPLY (7) | 依赖、锁文件、安装脚本、CI 权限 |

## 工作原理

- 没有证明就不报。在这里定不下来的，回来时是 `UNPROVEN`，绝不会算作通过。
- 在你批准那一处修复之前，你的仓库不会有任何改动。没有批量模式。
- 每处修复都要正反两个方向各证明一次：攻击者的请求现在失败，而你自己的登录照常可用。
  一个对所有人都返回 `403` 的补丁，堵上了洞，也堵死了产品。
- 它从不重写 git 历史，也从不替你轮换凭据。它写出轮换手册，由你来执行。

## 需要知道的

- 一次干净的运行不等于你的应用是安全的。第三种判定写的是 `NOTHING CONFIRMED HERE`，而且从不脱离覆盖率
  计数单独出现：它只是说，在这次运行能查到的范围里，没有东西升到 CRITICAL 或 HIGH。
- 在你批准修复之前，它只读。得到你明确同意后，它最多向一台你确认属于自己的主机发出约 30 个无害请求。
  不发 `DELETE`，不做压力测试。
- 它不是渗透测试，也没有人为它签字。其余的都在 [诚实的边界](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md)。

## 了解更多

- [快速上手](https://github.com/Aboudjem/secure-my-app/blob/main/docs/quickstart.md)，第一次运行从头到尾
- [一份完整报告](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md)，四条发现和未定项附录
- [诚实的边界](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md)，secure-my-app 不承诺的一切
- [在你的编辑器里安装](https://github.com/Aboudjem/secure-my-app/blob/main/docs/editors.md) · [FAQ](https://github.com/Aboudjem/secure-my-app/blob/main/docs/faq.md) · [参与贡献](https://github.com/Aboudjem/secure-my-app/blob/main/CONTRIBUTING.md) · [技能本体](https://github.com/Aboudjem/secure-my-app/blob/main/skills/secure-my-app/SKILL.md)

---

<sub>作者 <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT。已由 CI 的 162 项检查验证，其中 90 项来自 <code>tests/test_manifests.py</code>，72 项来自 <code>evals/check_skill.py</code>。
控制目录、严重度矩阵与 RLS 语义均重新推导自 PostgreSQL、Supabase 和 OWASP 的一手文档（2026 年）。<a href="https://github.com/Aboudjem/loopify">loopify</a> 与 <a href="https://github.com/Aboudjem/goalify">goalify</a> 的姊妹项目。<a href="https://github.com/Aboudjem/secure-my-app/issues">发现遗漏？</a></sub>

<sub>本文为机器辅助翻译并经人工校对，以英文 <a href="../README.md">README.md</a> 为准。</sub>
