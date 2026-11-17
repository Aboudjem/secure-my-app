<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-dark.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/secure-my-app/main/assets/hero-light.svg" alt="secure-my-app: 見知らぬ他人があなたのアプリから何を持ち出せるかを見つけ、それを塞ぎ、塞がったことを証明する。" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/secure-my-app/actions/workflows/validate.yml/badge.svg" alt="validate"></a> <a href="https://github.com/Aboudjem/secure-my-app/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <a href="zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="es.md">Español</a> · <a href="fr.md">Français</a>
  <br><sub>この翻訳は英語の原文より古い場合があります。<!-- may-lag --></sub>
</p>

<p align="center">
  <strong>見知らぬ他人があなたのアプリから何を持ち出せるかを見つけてください。そしてそれを塞ぎ、塞がったことを証明してください。</strong>
</p>

アプリを読み、名前の付いた 65 個のチェックを実行し、報告するすべての穴について証拠を示します。

```bash
npx skills add Aboudjem/secure-my-app
```

エージェントでプロジェクトを開き、こう言います。

```text
secure my app before I launch
```

## 得られるもの

`.secure-my-app/report.md` を書いて止まります。以下は 2026-11-17 の実際のレポートの冒頭です。

```text
VERDICT: DO NOT LAUNCH   coverage 21 checked / 2 unproven / 42 n/a   [static + live: 127.0.0.1:4310]
findings: 3 critical  2 high  6 medium  0 low   scan: gitleaks yes, semgrep installed but not run, osv-scanner no, trufflehog no
DO FIRST
1. K3  Replace the session secret committed in server.js with a new one read from the environment
2. D3  Replace SHA-256 password hashing with a real password hash, then reset every password
3. R10 Put a sign-in check and an admin role check on GET /admin/export
```

URL の数字を変えるだけで、あるユーザーが別のユーザーの請求書を読めるでしょうか。ここでは alice が bob の請求書を読んでいます。

```text
HIGH R4 Any signed-in user can read any invoice by changing the number in the URL

WHERE   server.js:83-92 (the lookup is line 89)
PROOF   [static]   server.js:89   const invoice = invoices.find((i) => i.id === id);
        [executed] alice (team_1) reads bob's invoice:
                   GET /api/invoices/1042 -> 200 {"id":1042,"owner":"u_2","team":"team_2",...}
        [executed] the list route scopes correctly: alice GET /api/invoices -> 200, invoice 1041 only
IMPACT  One team's customers, billing contacts, amounts and IBAN digits, readable by the other team.
FIX     const invoice = invoices.find((i) => i.id === id && i.owner === user.id);
VERIFY  alice:  GET /api/invoices/1042 (bob's)   -> 404 "no such invoice"
        alice:  GET /api/invoices/1041 (hers)    -> 200, the invoice
STATUS  OPEN
```

修正が認められるのは、同じリクエストが通らなくなったときだけです。
これはペネトレーションテストではありません。稼働中の URL がなければ、ほとんどのアクセスチェックは `UNPROVEN` になります。公開済みの実行は小さなテスト用アプリの 1 件だけです。

月曜にリリースする。エージェントも使って急いで作った。
ログイン済みのユーザーが他人のデータを読めるかどうか、わからない。このツールがそれを確かめ、根拠を見せます。

## 使う理由

- **推測ではなく証拠。** 各検出結果は `PROOF` を示します。コードの行と、稼働中の URL があればリクエストとその実際の出力です。`make test` はサンプルの各検出結果の裏にあるリクエストを再実行します。
- **確かめられる修正。** 各検出結果には、出力が変わらなければならない `VERIFY` コマンドがあります。[サンプルレポート](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md)の 11 件すべてにあります。`grep -c '^VERIFY' examples/sample-report.md` は 11 を出力します。
- **決めるのはあなた。** レポートを書いて止まります。修正を一つ承認するまで、アプリは何も変わりません。サンプルレポートには `Nothing in the app was changed.` とあります。

## インストール

**Claude Code。** マーケットプレイスを追加し、プラグインをインストールします。

```bash
claude plugin marketplace add Aboudjem/10x
```

```bash
claude plugin install secure-my-app@10x
```

**その他のエージェント。** このページ冒頭の skills CLI コマンドでインストールできます。
そのあと `secure my app before I launch` と言います。
この文はスキルの説明と一致するので、スキルを読み込むエージェントならどれでも反応します。
Codex CLI 0.169.0 では 2026-11-17 にこの文でスキルが起動しました。各エージェントには短いトリガーもあります。

| エージェント | 短いトリガー |
| --- | --- |
| Claude Code | `/secure-my-app:secure-my-app` |
| Codex CLI | `$secure-my-app` |

三つの質問をし、コードを読み、`.secure-my-app/report.md` を書きます。そして止まります。

### 対応エージェント

| エージェント | 実行内容 | テスト日 |
| --- | --- | --- |
| Claude Code 2.1.326 | プラグインを読み込み、テスト用アプリで全工程を実行、[レポート出力](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md) | 2026-11-17 |
| Codex CLI 0.169.0 | `npx skills add -a codex`、テスト用アプリで全工程を実行、[レポート出力](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report-codex.md) | 2026-11-17 |

文書化済み・未テスト: Cursor、GitHub Copilot、Gemini CLI、OpenCode、Windsurf、Zed、Continue.dev、Kimi Code CLI。
skills CLI はこれらにも同じファイルをインストールします。これらのエージェントでの実行記録はここにはありません。
エージェントごとのパスは[エディターへのインストール](https://github.com/Aboudjem/secure-my-app/blob/main/docs/editors.md)にあります。

## レポートの読み方

レポートは判定から始まり、次に最初にやるべき三つが続きます。
ヘッダーの下では、各検出結果が同じ項目を持ちます。このページ冒頭の R4 ブロックと同じです。

- **出どころ。** アプリは [`examples/vulnerable-app/`](https://github.com/Aboudjem/secure-my-app/blob/main/examples/vulnerable-app/README.md) で、わざと穴を残した小さな API です。
- **レポート全文。** [`examples/sample-report.md`](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md) はその実行が書いたファイルで、無編集です。上の R4 ブロックはそこから短くしたものです。
- **`PROOF`** は証拠です。`[static]` はコードから読んだ行。`[executed]` はリクエストとその出力で、秘密情報は短く切ってあります。
- **`VERIFY`** は、修正が認められる前に出力が変わらなければならないコマンドです。
- **2 回目の実行。** `.secure-my-app/surface.json` により、次の実行は何が直り、何が戻り、何が新しいかを言えます。

Supabase と Next.js の構成については[イラストレーション](https://github.com/Aboudjem/secure-my-app/blob/main/examples/illustration-supabase.md)を読んでください。そちらは架空のもので、そう明記しています。

### まず壊れたアプリで試す

このリポジトリをクローンし、テスト用アプリを起動します。

```bash
node examples/vulnerable-app/server.js
```

`examples/vulnerable-app/` でエージェントを開き、使っているエージェント用の行を入力します。

```text
/secure-my-app:secure-my-app --report-only --live http://127.0.0.1:4310
```

Codex CLI では、同じ行を `$secure-my-app` で始めてください。

[テスト用アプリの README](https://github.com/Aboudjem/secure-my-app/blob/main/examples/vulnerable-app/README.md) に三つの回答と二つのテストアカウントがあります。

## チェック内容

65 個のコントロールを七つのグループに分け、攻撃者が試す順に並べています（[完全なカタログ](https://github.com/Aboudjem/secure-my-app/blob/main/docs/controls.md)）。

| グループ | 対象 |
| --- | --- |
| KEYS (8) | リポジトリ内の秘密情報、鍵の露出、鍵の権限範囲、ローテーション |
| DOOR (9) | ログイン、セッション、Cookie、パスワードの保存、トークン |
| ROOMS (10) | 行レベルセキュリティ、IDOR、テナント分離、マスアサインメント |
| PIPES (13) | インジェクション、XSS、CSRF、SSRF、CORS、リダイレクト、Webhook、ヘッダー |
| VAULT (8) | 保存時の暗号化、レスポンスの形、エラーからの漏えい、ログ、バックアップ |
| FLOOR (10) | レート制限、ボット、アップロード、価格の改ざん、AI 機能 |
| SUPPLY (7) | 依存関係、ロックファイル、インストールスクリプト、CI の権限 |

## 仕組み

- **証拠がなければ検出結果なし。** 判断できないものは `UNPROVEN` として返り、合格にはなりません。
- **修正は一つずつ承認。** その修正にあなたが同意するまで、リポジトリは何も変わりません。一括モードはありません。
- **修正は二度証明されます。** 攻撃者のリクエストは失敗し、あなた自身のログインは引き続き動きます。
- **全員を締め出す修正は元に戻します。** 全ユーザーに `403` を返すパッチは、穴と一緒に製品も閉じてしまいます。
- **履歴と鍵には触れません。** git の履歴を書き換えず、認証情報もローテーションしません。手順書を書き、実行するのはあなたです。

## 証拠

このページの数字はすべて、クローンで実行できるコマンドから出ています。

テスト:

```bash
make test
```

```text
79/79 checks passed for skills/secure-my-app/SKILL.md
152/152 checks passed
33/33 checks passed
```

| スイート | チェック内容 |
| --- | --- |
| `evals/check_skill.py` | スキルの本文: 証拠のはしご、判定行、RLS のルール、レポートのヘッダー |
| `tests/test_manifests.py` | マニフェスト、全体で一つのバージョン、必須ファイル、この README |
| `tests/test_fixture.py` | テスト用アプリを起動し、サンプルの各検出結果の裏にあるリクエストを再実行 |

コントロールの数:

```bash
grep -c '^| [KDRPVFS][0-9]' skills/secure-my-app/references/controls.md
```

```text
65
```

CI はすべての push と pull request で `make test` を実行します。
テストが対象にするのはスキルの本文とテスト用アプリです。あなたのアプリで実行が何を見つけるかは教えてくれません。

## FAQ

### 自分のプロジェクトで実行しても安全ですか?

はい。修正を承認するまでは読むだけです。書き込むのは `.secure-my-app/` の下のレポートだけです。

### コードを書き換えますか?

勝手には書き換えません。各修正にはあなたの同意が必要で、先にチェックポイントのコミットを作り、あなた自身のリクエストが動かなくなれば元に戻します。

### コードをどこかに送りますか?

独自のネットワーク通信はしません。URL とあなたの同意があれば、その一つのホストに約 30 件のリクエストを送ります。
エージェント自体は、どの作業でも同じように、自分のモデル提供元にコンテキストを送ります。

### きれいなレポートなら、アプリは安全ということですか?

いいえ。三つ目の判定は `NOTHING CONFIRMED HERE` で、必ずカバレッジの数と一緒に出力されます。
実行で確認できた範囲で、critical や high に達したものがなかったという意味です。

### `/security-review` とどう違いますか?

`/security-review` は diff を読み、あなたが書いたコードの欠陥を見つけます。
secure-my-app はアプリ全体を読み、誰も書かなかった防御を見つけます。

### gitleaks や semgrep は必要ですか?

いいえ。インストールされていれば使い、ヘッダーに名前を出します。
スキャナーがないことで、チェックが合格になることはありません。

その他の回答は[完全な FAQ](https://github.com/Aboudjem/secure-my-app/blob/main/docs/faq.md)にあります。

## 制限事項

- **ペネトレーションテストではありません。** レポートに誰も署名しません。コンプライアンス監査でもありません。
- **見るのはリポジトリで、システムではありません。** クラウド設定、DNS、ノート PC、人は対象外です。
- **2 回の実行で結果が違うことがあります。** 評価は固定の表で決まります。スキャンはエージェントの判断です。
- **記録された実行は 1 件。** サンプルは小さなテスト用アプリのものです。本番アプリでの実行はここに公開していません。
- **URL がなければ証明できることは減ります。** その場合、ほとんどのアクセスチェックは `UNPROVEN` になります。
- **稼働中のアプリへの調査には上限があります。** 約 30 リクエスト、あなたが所有する一つのホスト、`DELETE` なし、負荷テストなし。

約束しないことはすべて[正直な制限事項](https://github.com/Aboudjem/secure-my-app/blob/main/docs/limits.md)にあります。

## さらに詳しく

- [クイックスタート](https://github.com/Aboudjem/secure-my-app/blob/main/docs/quickstart.md)、最初の実行を最初から最後まで
- [実際の実行によるレポート](https://github.com/Aboudjem/secure-my-app/blob/main/examples/sample-report.md)、 11 件の検出結果と未証明の付録
- [エディターへのインストール](https://github.com/Aboudjem/secure-my-app/blob/main/docs/editors.md) · [コントリビュート](https://github.com/Aboudjem/secure-my-app/blob/main/CONTRIBUTING.md) · [スキル本体](https://github.com/Aboudjem/secure-my-app/blob/main/skills/secure-my-app/SKILL.md)

---

<sub>作者 <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT。
コントロールのカタログ、深刻度の表、RLS の意味論は、PostgreSQL、Supabase、OWASP の一次資料から 2026 年に導き直したものです。
姉妹ツール: <a href="https://github.com/Aboudjem/loopify">loopify</a>、<a href="https://github.com/Aboudjem/goalify">goalify</a>。<a href="https://github.com/Aboudjem/secure-my-app/issues">抜けを見つけましたか?</a></sub>

<sub>機械支援による翻訳です。基準となるのは英語の <a href="../README.md">README.md</a> です。</sub>
