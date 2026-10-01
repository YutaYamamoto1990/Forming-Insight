# 解析プロセスの登録と編集

配布後も利用者が `processes/<process-id>/` を追加・編集できます。Agentに編集を依頼する場合は対象と変更内容を明示します。通常の解析依頼をプロセス原本の変更許可とは扱いません。

## 原本の構成

```text
processes/<process-id>/
  process.json       # GH入出力、配置、待機時間、ポスト処理設定
  gh/                # GH原本
  assets/            # cal_setup.kなど固定資材（必要な場合）
  post/              # cfile原本
  originals.json     # 初回保管時のSHA-256記録
  README.md          # 入出力契約、依存環境、確認状況
```

`process-test` と `press-z` の現時点の原本を同梱しています。入力形状や解析結果、ソフトウェア本体は含めません。process-testには独立したcal_setup.kがなく、入力kに解析設定を含みます。

`process.json` のGH・資材・cfileの相対パスは**配布ルート基準**です。通常は同梱原本を使用し、必要な場合のみconfigのprocesses.<id>で上書きします。Rhino、プラグイン、Dyna、LS-PrePostのインストールとライセンス、GH内部の環境設定は利用先で確認してください。

## 追加・編集手順

1. 実行中の解析がないことを確認し、既存フォルダーまたは `_template/` を新しいIDへコピーします。
2. GH、固定資材、cfileを配置し、process.jsonのパス、公開入力名、出力配置、timeout_seconds、必要ならpostprocessを更新します。
3. 原本の変更をGit等で記録します。originals.jsonは初回コピーの記録であり、編集後の強制照合値ではありません。
4. prepare-onlyで配置を確認し、GHの入出力を確認してからテスト入力で実行検証します。cfileの画像出力名とexpected_imagesを一致させます。

解析実行中はprocessesを変更しません。GH・資材・cfileは各実行のworkspaceへコピーし、原本を上書きしません。実行前後の定義ハッシュ確認は維持します。既存runのRawや確定レポートを新しいプロセス内容で上書きしません。

press-zのポスト処理原本は `post/press_z_post.cfile` です。旧lspost.cfileは使用しません。新原本には画像・グラフの出力が含まれますが、process.jsonのpostprocessに登録済みです。
