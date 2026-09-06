<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-light.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg" alt="lockpatch：找出陌生人能从你的应用里拿走什么，然后把它堵上，并证明它确实堵上了。" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Aboudjem/lockpatch/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
  <a href="https://github.com/Aboudjem/lockpatch/stargazers"><img src="https://img.shields.io/github/stars/Aboudjem/lockpatch?color=2BE8C8&labelColor=0A0F1C" alt="stars"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <b>简体中文</b> · <a href="ja.md">日本語</a> · <a href="es.md">Español</a> · <a href="fr.md">Français</a>
</p>

<p align="center">
  <strong>找出陌生人能从你的应用里拿走什么。然后把它堵上，并证明它确实堵上了。</strong>
</p>

<p align="center">
  <a href="#它做什么">它做什么</a> · <a href="#安装">安装</a> · <a href="#怎么用">怎么用</a> · <a href="#工作原理">工作原理</a> · <a href="#在你的编辑器里">在你的编辑器里</a> · <a href="https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md">诚实的边界</a> · <a href="#了解更多">了解更多</a>
</p>

<p align="center"><sub>本翻译可能落后于英文原文。<!-- may-lag --></sub></p>

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install lockpatch@10x        # Claude Code
npx skills add Aboudjem/lockpatch          # Cursor, Codex, Copilot, Gemini CLI, and 70+ others
```

## 它做什么

Claude Code 已经自带 `/security-review`，而且它做得很好：读一份 diff，找出那里的代码里的缺陷。但是没有人是
在一份你能审阅的 diff 里"忘了"给 `profiles` 表写行级安全策略的，因为这条策略的缺席根本不出现在任何 diff 中。
它是你交付出去的东西的形状。**`/security-review` 找的是你写过的代码里的 bug。lockpatch 找的是你从来没有
写过的那道防线。**

所以它读的是整个应用而不是一次改动，运行 65 项有名字的控制项检查，并在你的项目里写下两个文件。

- **`.lockpatch/report.md`，报告。** 每一条发现都是同样的七个字段、同样的顺序：是什么、在哪里、证据、影响、
  修复、验证、状态。`PROOF` 是一条真实的命令和它真实的输出，密钥已做遮蔽。`VERIFY` 是那条命令：在任何东西被
  称为"已修复"之前，它的输出必须先发生变化。
- **`.lockpatch/surface.json`，清单。** 你的路由、表、策略和发现以数据形式保存，这样第二次运行会告诉你
  "修好 3 个，回归 1 个，新增 1 个"，而不是再递给你一堵新的文字墙。

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero.svg" alt="lockpatch 的四个步骤：绘制攻击面、运行控制项检查、沿阶梯升到一条发现、然后修复并重新证明。" width="100%">
</p>

整件事只立在一条规则上：**没有证据就不是发现；没有重新证明就不算修好。** 一条你无法演示的发现只是猜测，而把
猜测发给一个信任你的人，比沉默更糟。

## 安装

顶部那两条 Claude Code 命令会添加 10x 市场并安装插件。任何其他智能体都可以通过
[skills CLI](https://github.com/vercel-labs/skills) 用一行命令安装同一个技能目录：

```bash
npx skills add Aboudjem/lockpatch
```

没有别的东西要装：没有依赖，没有服务端，没有账号。如果 `gitleaks`、`trufflehog`、`semgrep` 或
`osv-scanner` 已经在你机器上，它就会使用它们，并在报告头部说明；如果没有，它就运行有文档记录的替代方案，
同样会说明。

## 怎么用

### 1. 把它指向应用

```text
/lockpatch
```

它会读取你的清单文件，打印一屏之内的技术栈卡片，然后只问三个问题，因为只有这三个会改变后面运行的内容：这个
应用现在是否在线并且陌生人可以访问；仓库是不是公开的，或者曾经公开过；是否有不止一个客户共用这个数据库。给不给
URL 是可选的，但它是一份扎实报告和一份薄弱报告之间最大的差别。

### 2. 读那一行结论

```text
LOCKPATCH   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
scan: gitleaks yes, osv yes, semgrep no, trufflehog no
findings: 2 critical  1 high  1 medium  0 low
```

然后它就停下来问你。一份你并没有要求它去动手的报告，本身就是一次完整的交付。

### 3. 一次修一条

```text
fix R1
```

每一次修复都会带着它的 diff 提出来，由你针对这一条单独批准，在一次检查点提交之后应用，然后在两个方向上重新
证明。没有让你一次性批准全部的批量模式，也没有任何修复会仅凭一份 diff 就被标记为已完成。

## 工作原理

**阶梯。** 每个候选项都要爬四级台阶才能成为一条发现，这正是让报告不至于变成四十条没人看的清单的机制。

```
Rung 4  IMPACT    Name the asset in plain words
Rung 3  CONTROL   Show that nothing stops it, through the actual calling role
Rung 2  REACH     Show who can get there: unauthenticated, any account, another tenant
Rung 1  EXISTS    file:line
Rung 0  ABSTAIN   UNPROVEN, with the reason and the command that would settle it
```

第 0 级是一等结果。一条自信但错误的发现是这个技能能产出的最糟糕的东西，因为它会在上线前夜的半夜，把人派去
"修"一个本来好好的登录。

**三种结果，从来不是两种。** 每项检查都以 `PASS`、`FAIL`、`UNPROVEN` 或 `N/A` 结束。grep 没搜到并不能
证明某个控制项存在，所以它永远不会变成 `PASS`。

**证据分层级，每一行证据都带标签。** `static` 是在仓库里读到的。`executed` 是在这里跑过的，这就是它的输出。
`recipe` 是写给你去跑的命令，没有人跑过它，所以它永远不能支撑一个 `PASS`，也不能关闭一条发现。

**成对测试。** 每次修复都要在相反的两个方向上各证明一次。这是大多数安全工具会跳过的一条规则。

```
Before   attacker's request succeeds      legitimate user's request succeeds
Fix      the control is added
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

一个对所有人都返回 `403` 的补丁堵住了漏洞，也堵死了产品。而且"失败"具体指的是被拒绝：超时、500，或者因为
测试数据行根本不存在而返回的空结果，看起来都像失败，却什么都没证明。

**结论行永远和覆盖率一起出现。** 这里没有百分制评分，因为一个数字会诱导人说"我们从 62 提到了 78"，而任何
加权求和都能靠多加几个通过的控制项来刷分。真正交付的是一个计数和三个按规则算出来的标签，而且任何标签都不会在
没有同一行覆盖率数字的情况下被打印出来：

```text
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

这些数字不是装饰。没有它们，一次彻底的运行和一次几乎什么都没能检查的运行会打印出同样的标签。而第三个标签之所以
刻意就是 `NOTHING CONFIRMED HERE` 这几个字，而不是"安全"或"通过"，是因为它主张的全部内容只是：在这次运行
能够检查到的范围内，没有任何一条升到 CRITICAL 或 HIGH。

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/how-it-works.svg" alt="lockpatch 的流程：确定范围、绘制攻击面、运行控制项检查、实时探测、出报告，然后在批准后修复。" width="100%">
</p>

## 它检查什么

七个分组共 65 项控制，按攻击者会先试什么排序。带每项 `DETECT` 和 `VERIFY` 命令的完整目录在
[skills/lockpatch/references/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/references/controls.md)，
便于阅读的索引在
[docs/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md)。

| 分组 | 覆盖 | 为什么在这个位置 |
| --- | --- | --- |
| **KEYS** (8) | 密钥、密钥暴露与作用域、轮换 | 排在最前，因为一旦密钥泄露，损害可能已经发生，而且时钟正在走 |
| **DOOR** (9) | 认证 | 会话、Cookie、口令存储、令牌、登录限流 |
| **ROOMS** (10) | 授权 | 行级安全、IDOR、租户隔离、批量赋值、特权字段 |
| **PIPES** (12) | 边界与链路 | 注入、XSS、CSRF、SSRF、CORS、重定向、Webhook、响应头、HTTPS |
| **VAULT** (8) | 静态数据，以及正在离开的数据 | 加密、响应形状、报错泄露、日志、备份、导出 |
| **FLOOR** (10) | 滥用与业务逻辑 | 限流、机器人、上传、价格篡改、状态机、AI 功能 |
| **SUPPLY** (7) | 你所依赖的东西 | 依赖、锁文件、安装脚本、CI 权限、预览环境 |

ROOMS 是那些代价高昂的入侵真正发生的地方，也是智能体写出的代码最薄弱的地方，因为一个缺失的授权检查，在开发者
为自己写的每一个测试里，看起来都和正常工作的代码一模一样。

## 在你的编辑器里

通过 `npx skills add`，可在 Claude Code、Cursor、Codex、Copilot、Gemini CLI 以及 70 多个其他智能体中
使用。

| 在哪里 | 怎么装 |
| --- | --- |
| Claude Code | `claude plugin install lockpatch@10x` |
| Cursor, Codex, Gemini CLI, OpenCode, Windsurf, Zed, Continue.dev | `npx skills add Aboudjem/lockpatch -a <agent>` |
| VS Code 和 GitHub Copilot | `npx skills add Aboudjem/lockpatch -a github-copilot` |
| 其他所有情况 | 把 `skills/lockpatch/` 复制到你的智能体的技能目录 |

这个技能是 Markdown，所以它能到处走。不同宿主之间变化的只是底下的工具，而 lockpatch 是诚实地降级而不是悄悄
降级：没有 shell 的智能体跑不了 `DETECT` 命令，于是那些控制项会以 `UNPROVEN` 返回，并把命令写出来给你；
没有网络的智能体会在报告头部写上 `static only`。两种都仍然是有用的运行。两种都不允许报告一个它没有挣到的
`PASS`。每个智能体的 `-a` 代码见
[docs/editors.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md)。

## 值得先知道的事

> [!IMPORTANT]
> 一次干净的运行并不意味着你的应用是安全的。第三个结论标签的字面就是 `NOTHING CONFIRMED HERE`，不是"安全"
> 也不是"通过"，因为它说的只是：在这次运行真正能检查到的控制项里，没有任何一条升到 CRITICAL 或 HIGH。请读
> 同一行上的覆盖率数字，并在你告诉任何人"应用过了"之前，先读
> [诚实的边界](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md)。

- **在你批准修复之前它只读。** 阶段 0 到 4 会读文件、跑命令，并且只有在你明确同意的情况下，才会向一个你确认
  自己拥有的主机发出最多约 30 次无害请求。没有 `DELETE`，没有会修改数据的请求，没有压力测试。
- **它从不替你轮换凭据，也从不重写 git 历史。** 轮换手册由它来写，由你来执行。先轮换，再清理历史，因为一把
  公开过五分钟的密钥就是永久失陷的。
- **任何密钥的值都不会进入报告。** 一律遮蔽到"服务商前缀加四个字符"，例如 `sk_live_51Nq...`。
- **它不是渗透测试，也不是合规审计。** 没有人会为它签字。如果你的应用涉及支付、健康数据，或者别人系统的
  凭据，请去做一次真正的评估。
- **评级是确定的，扫描不是。** 发现和分类都是判断，所以两次运行可能找到不同的东西，`surface.json` 正是为此
  存在。

## 了解更多

- [快速上手](https://github.com/Aboudjem/lockpatch/blob/main/docs/quickstart.md)，一次从头到尾的运行，
  附上你真正会看到的输出
- [在你的编辑器里安装](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md)，`-a` 代码和
  skills CLI 的两条路径
- [一份完整报告](https://github.com/Aboudjem/lockpatch/blob/main/examples/sample-report.md)，一个完整的
  `.lockpatch/report.md`，包含四条发现、未证明附录，以及"没有检查什么，以及为什么"一节
- [诚实的边界](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md)，lockpatch 不承诺的
  一切，详细版
- [控制项目录](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md)，七个分组共 65 项控制
- [FAQ](https://github.com/Aboudjem/lockpatch/blob/main/docs/faq.md) · [更新日志](https://github.com/Aboudjem/lockpatch/blob/main/CHANGELOG.md) · [参与贡献](https://github.com/Aboudjem/lockpatch/blob/main/CONTRIBUTING.md) · [安全策略](https://github.com/Aboudjem/lockpatch/blob/main/SECURITY.md) · [技能本身](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/SKILL.md)

已在 CI 中通过 162 项检查验证：`python3 tests/test_manifests.py` 提供 90 项，
`python3 evals/check_skill.py skills/lockpatch/SKILL.md` 提供 72 项。

---

<sub>由 <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> 构建 · MIT。控制项目录、严重度矩阵与
RLS 语义均重新依据 PostgreSQL、Supabase 和 OWASP 的一手文档推导，2026 年。它是
<a href="https://github.com/Aboudjem/loopify">loopify</a> 和
<a href="https://github.com/Aboudjem/goalify">goalify</a> 的姊妹项目。
<a href="https://github.com/Aboudjem/lockpatch/issues">发现遗漏了吗？</a></sub>

<sub>机器辅助翻译，随后经过校对。以英文 <a href="../README.md">README.md</a> 为准。</sub>
