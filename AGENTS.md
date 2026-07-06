# AGENTS.md

エージェント/コントリビュータ向けの作業ガイド。プロジェクトの規約・構成・
データ設計の不変条件をまとめる。企画は [`docs/spec.md`](docs/spec.md)、設計は
[`docs/design.md`](docs/design.md)、フローは [`docs/game_flow.md`](docs/game_flow.md)。

## プロダクト概要

「バラの本数の花言葉」を恋リア風シチュエーションのクイズで学べる Web ゲーム。
GitHub Pages でホスティングするフロントエンド完結構成。1 プレイ数分のライトな
知的エンタメ。

## 技術スタック

- Vite + React 19 + TypeScript(`type: module`)
- 物理 RDB なし。データは `data/` 配下の CSV(確定ソース)。
- ホスティング: GitHub Pages(`.github/workflows/deploy.yml`)

## コマンド

```bash
pnpm install        # 依存インストール(lockfile は pnpm)
pnpm dev            # 開発サーバ
pnpm build          # tsc -b && vite build
pnpm lint           # eslint .
python3 .claude/skills/validate-rose-data/validate.py data   # データ整合性検証
```

`data/` を触ったら**必ず**最後にデータ検証を実行すること。

## ディレクトリ構成

```
data/                 確定データ(source of truth) — 正規化 CSV 3 枚
  rose_meaning.csv        本数マスタ (id PK, count UK, quiz_enabled, description)
  meaning_variants.csv    花言葉 (1NF, FK -> rose_meaning.id)
  quiz_titles.csv         結果画面の称号バンド
docs/                 企画・設計ドキュメント
src/                  アプリ本体 (React/TS)
.claude/skills/       プロジェクト skill(データ検証・追加運用)
```

## データ設計の原則(本 PoC の本命: G2)

RDB を使わないが、**いつでも RDB 移行・マッピング可能な正規化設計**を徹底する。
安易な 1 枚の巨大 JSON を作らず、概念ごとにエンティティを分け、PK/FK を意識する。

守るべき不変条件(詳細と根拠は `docs/design.md` §3):

1. **サロゲート PK は安定**。`rose_meaning.id` / `meaning_variants.id` は行順に
   依存しない。**欠番を詰めるための再採番は禁止**(FK が壊れる)。
2. **`count` は UNIQUE な自然キー**。本数と PK は別物。
3. **1NF**: `meaning` は単一値。1 セルに複数の花言葉(`/` 区切り)を入れない。
   複数意味は `meaning_variants` の複数行で表す。
4. **FK 整合**: `meaning_variants.rose_meaning_id` は必ず実在する
   `rose_meaning.id` を指す。親を消すときは子(variants)も消す。
5. **出題プールの一意性**: パターンA(4択)の正解が一意になるよう、酷似する
   花言葉を持つ本数は片方の `quiz_enabled` を `false` にする(`docs/design.md` §3.2)。
   除外側もコレクションには全 38 本表示する。

データ編集は skill を使うと安全:
- 追加/編集: `.claude/skills/add-rose-meaning`
- 検証: `.claude/skills/validate-rose-data`

## ゲーム仕様の要点(確定事項)

- 出題は **案B**(パターンA=本数→意味4択 / パターンB=シチュエーション→本数)。
- カード獲得は **正解時のみ**。ライフ(♡)なし。1 ラウンド 5 問固定。
- シェアは **X + LINE**。
- 出題は `quiz_enabled=true`(33 本)のみ。コレクションは全 38 本。
- 静的 questions テーブルは持たず、**マスタから動的生成**(`docs/design.md` §5)。

## コーディング規約

- 既存コードのスタイル/命名/コメント密度に合わせる。
- コミット前に `pnpm lint` と `pnpm build` を通す。
- データ変更を含む場合はデータ検証も通す。
