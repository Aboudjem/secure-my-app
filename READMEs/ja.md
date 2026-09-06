<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-light.svg">
    <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero-dark.svg" alt="lockpatch: 見知らぬ他人があなたのアプリから何を持ち出せるかを見つけ、それを塞ぎ、塞がったことを証明する。" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml"><img src="https://github.com/Aboudjem/lockpatch/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Aboudjem/lockpatch/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license"></a>
  <a href="https://github.com/Aboudjem/lockpatch/stargazers"><img src="https://img.shields.io/github/stars/Aboudjem/lockpatch?color=2BE8C8&labelColor=0A0F1C" alt="stars"></a>
</p>

<p align="center">
  <a href="../README.md">English</a> · <a href="zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="es.md">Español</a> · <a href="fr.md">Français</a>
</p>

<p align="center">
  <strong>見知らぬ他人があなたのアプリから何を持ち出せるかを見つけてください。そしてそれを塞ぎ、塞がったことを証明してください。</strong>
</p>

<p align="center">
  <a href="#できること">できること</a> · <a href="#インストール">インストール</a> · <a href="#使い方">使い方</a> · <a href="#仕組み">仕組み</a> · <a href="#各エディタで使う">各エディタで使う</a> · <a href="https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md">正直な限界</a> · <a href="#もっと詳しく">もっと詳しく</a>
</p>

<p align="center"><sub>この翻訳は英語の原文より古い場合があります。<!-- may-lag --></sub></p>

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install lockpatch@10x        # Claude Code
npx skills add Aboudjem/lockpatch          # Cursor, Codex, Copilot, Gemini CLI, and 70+ others
```

## できること

Claude Code には既に `/security-review` があり、その仕事はよくこなします。差分を読み、そこにあるコードの
欠陥を見つけます。しかし、`profiles` テーブルの行レベルセキュリティポリシーを書き忘れたことは、あなたが
レビューできる差分の中には現れません。そのポリシーが「無い」ことは、どの差分にも書かれていないからです。
それは出荷したものの形そのものです。**`/security-review` はあなたが書いたコードのバグを見つけます。
lockpatch はあなたが一度も書かなかった防御を見つけます。**

そのため lockpatch は差分ではなくアプリ全体を読み、名前の付いた 65 個のコントロールを実行し、プロジェクトに
2 つのファイルを書き出します。

- **`.lockpatch/report.md`、レポート。** すべての検出結果が同じ 7 つのフィールドを同じ順序で持ちます。
  何が、どこに、証拠、影響、修正、検証、状態。`PROOF` は実際のコマンドとその実際の出力で、シークレットは
  伏せられています。`VERIFY` は、何かを「直った」と呼ぶ前に出力が変わらなければならないコマンドです。
- **`.lockpatch/surface.json`、インベントリ。** ルート、テーブル、ポリシー、検出結果をデータとして持つので、
  2 回目の実行は新しい大量のテキストではなく「3 件修正、1 件退行、1 件新規」と言えます。

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/hero.svg" alt="lockpatch の 4 ステップ: 攻撃面を地図にする、コントロールを実行する、はしごを登って検出結果にする、修正して再証明する。" width="100%">
</p>

すべては 1 つのルールの上に立っています。**証拠が無ければ検出結果ではない。再証明が無ければ修正ではない。**
実演できない検出結果は推測であり、あなたを信頼している相手に送られた推測は、沈黙よりも悪いものです。

## インストール

冒頭の 2 つの Claude Code コマンドが 10x マーケットプレイスを追加し、プラグインをインストールします。他の
エージェントは [skills CLI](https://github.com/vercel-labs/skills) で同じスキルディレクトリを 1 行で
インストールできます。

```bash
npx skills add Aboudjem/lockpatch
```

他に入れるものはありません。依存関係なし、サーバーなし、アカウントなし。`gitleaks`、`trufflehog`、
`semgrep`、`osv-scanner` が既に入っていればそれらを使い、レポートのヘッダーにそう書きます。入っていなければ
文書化された代替手段を実行し、それもヘッダーに書きます。

## 使い方

### 1. アプリに向ける

```text
/lockpatch
```

マニフェストを読み、1 画面に収まるスタックカードを表示し、ちょうど 3 つだけ質問します。この 3 つだけが
後続の実行内容を変えるからです。アプリは今この瞬間、見知らぬ人から到達可能な状態で動いているか。リポジトリは
公開されているか、あるいは過去に公開されていたか。1 つのデータベースを複数の顧客が共有しているか。URL を
渡すかどうかは任意ですが、強いレポートと弱いレポートを分ける最大の要因です。

### 2. ゲート行を読む

```text
LOCKPATCH   gate: DO NOT LAUNCH
coverage 47 checked / 8 unproven / 4 n/a   [static + live: tidemark-preview.vercel.app]
scan: gitleaks yes, osv yes, semgrep no, trufflehog no
findings: 2 critical  1 high  1 medium  0 low
```

そこで止まって尋ねます。行動を依頼されていないレポートは、それだけで完全な成果物です。

### 3. 1 件ずつ修正する

```text
fix R1
```

各修正は差分とともに提案され、その修正について個別にあなたが承認し、チェックポイントのコミットの後に適用され、
両方向で再証明されます。まとめて一括承認するモードはありませんし、差分だけを見て「完了」と記録される修正も
ありません。

## 仕組み

**はしご。** すべての候補は、検出結果として現れる前に 4 段のはしごを登ります。これがレポートを、誰も読まない
40 項目の一覧にしない仕組みです。

```
Rung 4  IMPACT    Name the asset in plain words
Rung 3  CONTROL   Show that nothing stops it, through the actual calling role
Rung 2  REACH     Show who can get there: unauthenticated, any account, another tenant
Rung 1  EXISTS    file:line
Rung 0  ABSTAIN   UNPROVEN, with the reason and the command that would settle it
```

第 0 段も一級の結果です。自信満々の誤った検出結果は、このスキルが生み出しうる最悪のものです。ローンチ前夜の
真夜中に、動いているログインを「直しに」行かせてしまうからです。

**結果は 3 つ、決して 2 つではない。** すべてのチェックは `PASS`、`FAIL`、`UNPROVEN`、`N/A` のいずれかで
終わります。grep が空だったことはコントロールが存在する証拠ではないので、決して `PASS` にはなりません。

**証拠には段階があり、すべての証拠行にタグが付きます。** `static` はリポジトリで読んだもの。`executed` は
ここで実行し、これがその出力であるもの。`recipe` はあなたのために書き出したコマンドで、誰も実行していません。
だから `PASS` を支えることも、検出結果を閉じることもできません。

**対になったテスト。** すべての修正は反対方向に 2 回証明されます。ほとんどのセキュリティツールが飛ばす
ルールです。

```
Before   attacker's request succeeds      legitimate user's request succeeds
Fix      the control is added
After    attacker's request FAILS         legitimate user's request STILL SUCCEEDS
```

全員に `403` を返すパッチは、穴を塞ぐと同時に製品も塞ぎます。そして「失敗する」とは、具体的には拒否される
ことです。タイムアウト、500、あるいはフィクスチャの行が最初から無かったための空の結果は、失敗のように見えて
何も証明しません。

**ゲートは常にカバレッジと一緒に。** 100 点満点のスコアはありません。数値は「62 から 78 になった」という
語り方を招きますし、加重合計はパスするコントロールを増やすだけで操作できるからです。代わりに出るのは件数と、
ルールで計算された 3 つのラベルで、どのラベルも同じ行のカバレッジの数字なしに表示されることはありません。

```text
GATE: NOTHING CONFIRMED HERE   coverage 41 checked / 9 unproven / 6 n/a   [static only, no live probes]
```

この数字は飾りではありません。これが無いと、隅々まで確認できた実行と、ほとんど何も確認できなかった実行が同じ
ラベルを表示してしまいます。そして 3 番目のラベルが意図的に `NOTHING CONFIRMED HERE` という言葉であって
「secure」でも「passed」でもないのは、それが主張しているのが、この実行が確認できた範囲では CRITICAL と
HIGH に達したものが無かった、ということだけだからです。

<p align="center">
  <img src="https://raw.githubusercontent.com/Aboudjem/lockpatch/main/assets/how-it-works.svg" alt="lockpatch のパイプライン: スコープ、攻撃面の地図、コントロールの実行、ライブプローブ、レポート、承認後の修正。" width="100%">
</p>

## 何を確認するか

7 つのグループに 65 個のコントロール。攻撃者が先に試す順に並んでいます。コントロールごとの `DETECT` と
`VERIFY` コマンドを含む完全なカタログは
[skills/lockpatch/references/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/references/controls.md)
にあり、読みやすい索引は
[docs/controls.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md) です。

| グループ | 対象 | なぜこの位置か |
| --- | --- | --- |
| **KEYS** (8) | シークレット、鍵の露出と範囲、ローテーション | 最初。鍵が漏れていれば被害は既に始まっていて、時計が動いているから |
| **DOOR** (9) | 認証 | セッション、Cookie、パスワード保存、トークン、ログインのレート制限 |
| **ROOMS** (10) | 認可 | 行レベルセキュリティ、IDOR、テナント分離、マスアサインメント、特権カラム |
| **PIPES** (12) | 境界と通信路 | インジェクション、XSS、CSRF、SSRF、CORS、リダイレクト、Webhook、ヘッダー、HTTPS |
| **VAULT** (8) | 保存されたデータと出ていくデータ | 暗号化、レスポンスの形、エラーからの漏洩、ログ、バックアップ、エクスポート |
| **FLOOR** (10) | 悪用とビジネスロジック | レート制限、ボット、アップロード、価格改ざん、状態遷移、AI 機能 |
| **SUPPLY** (7) | 土台にしているもの | 依存関係、ロックファイル、インストールスクリプト、CI 権限、プレビュー環境 |

ROOMS は高くつく侵害が起きる場所であり、エージェントが書いたコードが最も弱い場所でもあります。抜けている
認可チェックは、開発者が自分のために書くどのテストでも、動いているコードとまったく同じに見えるからです。

## 各エディタで使う

`npx skills add` により Claude Code、Cursor、Codex、Copilot、Gemini CLI、その他 70 以上のエージェントで
動きます。

| どこで | どうやって |
| --- | --- |
| Claude Code | `claude plugin install lockpatch@10x` |
| Cursor, Codex, Gemini CLI, OpenCode, Windsurf, Zed, Continue.dev | `npx skills add Aboudjem/lockpatch -a <agent>` |
| VS Code と GitHub Copilot | `npx skills add Aboudjem/lockpatch -a github-copilot` |
| それ以外すべて | `skills/lockpatch/` をエージェントのスキルディレクトリにコピー |

スキルは Markdown なので持ち運べます。ハーネスごとに変わるのは下回りのツールだけで、lockpatch は黙って
劣化するのではなく正直に劣化します。シェルの無いエージェントは `DETECT` コマンドを実行できないので、それらの
コントロールはコマンドを書き出したうえで `UNPROVEN` として返ります。ネットワークの無いエージェントは
レポートのヘッダーに `static only` と書きます。どちらも有用な実行です。どちらも、得ていない `PASS` を
報告することは許されていません。エージェントごとの `-a` コードは
[docs/editors.md](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md) にあります。

## 知っておくこと

> [!IMPORTANT]
> きれいな実行結果は、アプリが安全であることを意味しません。3 番目のゲートラベルは「secure」でも「passed」でも
> なく `NOTHING CONFIRMED HERE` という言葉です。それが言っているのは、この実行が実際に確認できたコントロールの
> 範囲では CRITICAL と HIGH に達したものが無かった、ということだけだからです。同じ行のカバレッジの数字を読み、
> 誰かに「通った」と伝える前に
> [正直な限界](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md) を読んでください。

- **修正を承認するまでは読み取り専用です。** フェーズ 0 から 4 はファイルを読み、コマンドを実行し、あなたの
  明示的な同意がある場合にかぎり、所有を確認した 1 つのホストに対して最大でおよそ 30 回の無害なリクエストを
  送ります。`DELETE` はなし、データを変更するリクエストもなし、負荷テストもなし。
- **資格情報のローテーションも git 履歴の書き換えも決して行いません。** ローテーションの手順書を書くのは
  lockpatch、実行するのはあなたです。先にローテーション、履歴の掃除は後。5 分でも公開された鍵は、永久に
  侵害されたものだからです。
- **シークレットの値がレポートに載ることはありません。** すべてプロバイダの接頭辞と 4 文字まで伏せられます。
  たとえば `sk_live_51Nq...` のように。
- **ペネトレーションテストでもコンプライアンス監査でもありません。** 誰も署名しません。決済、医療データ、
  他者のシステムの資格情報を扱うなら、本物の評価を受けてください。
- **評価は決定的ですが、スキャンは決定的ではありません。** 発見と分類は判断なので、2 回の実行が別のものを
  見つけることがあります。`surface.json` があるのはそのためです。

## もっと詳しく

- [クイックスタート](https://github.com/Aboudjem/lockpatch/blob/main/docs/quickstart.md)、最初の実行を
  最後まで、実際に見える出力つきで
- [エディタへのインストール](https://github.com/Aboudjem/lockpatch/blob/main/docs/editors.md)、`-a`
  コードと skills CLI の 2 つのパス
- [実際のレポート例](https://github.com/Aboudjem/lockpatch/blob/main/examples/sample-report.md)、4 件の
  検出結果、未証明の付録、「確認していないこと、その理由」を含む完全な `.lockpatch/report.md`
- [正直な限界](https://github.com/Aboudjem/lockpatch/blob/main/docs/limits.md)、lockpatch が約束しない
  ことのすべて
- [コントロールカタログ](https://github.com/Aboudjem/lockpatch/blob/main/docs/controls.md)、7 グループ
  65 コントロール
- [FAQ](https://github.com/Aboudjem/lockpatch/blob/main/docs/faq.md) · [変更履歴](https://github.com/Aboudjem/lockpatch/blob/main/CHANGELOG.md) · [コントリビュート](https://github.com/Aboudjem/lockpatch/blob/main/CONTRIBUTING.md) · [セキュリティポリシー](https://github.com/Aboudjem/lockpatch/blob/main/SECURITY.md) · [スキル本体](https://github.com/Aboudjem/lockpatch/blob/main/skills/lockpatch/SKILL.md)

CI で 162 件のチェックにより検証されています。`python3 tests/test_manifests.py` から
90 件、`python3 evals/check_skill.py skills/lockpatch/SKILL.md` から 72 件です。

---

<sub>作者 <a href="https://github.com/Aboudjem">Adam Boudjemaa</a> · MIT。コントロールカタログ、深刻度
マトリクス、RLS のセマンティクスは PostgreSQL、Supabase、OWASP の一次資料から再導出しています (2026 年)。
<a href="https://github.com/Aboudjem/loopify">loopify</a> と
<a href="https://github.com/Aboudjem/goalify">goalify</a> の姉妹プロジェクトです。
<a href="https://github.com/Aboudjem/lockpatch/issues">抜けを見つけましたか?</a></sub>

<sub>機械翻訳のうえで校正しています。基準となるのは英語の <a href="../README.md">README.md</a> です。</sub>
