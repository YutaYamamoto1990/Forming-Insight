# Forming Insight

Surfaceを入力とし、決定論的なプレス解析と根拠に基づくLLMの解釈を分離してレポートを生成する、配布可能なCodex用Agentの開発リポジトリです。

リポジトリ: https://github.com/YutaYamamoto1990/Forming-Insight

## 現在の状態

入力はkファイル、解析実行は既存のGrasshopperフローが担当します。入力コピー、ローカルRhino.Computeへの呼び出し、既定600秒の応答待ち、Raw保存を実装し、共有されたテストGH/kファイルで実行確認しました。
利用者との合意により、通常のGH応答を受信したら成功と扱います。ソルバー内部の正常終了を検証したとは扱いません。解析実行と結果案内を担当するpress-analysis Skillを追加しました。LS-PrePost画像出力を実機検証し、共通HTMLレポートのテンプレート・生成スクリプトを追加しました。GHからポスト処理への自動連結と専門的な評価基準は今後実装します。

## 構成

- `AGENTS.md`: 開発用の常設指示。
- `design/`: 開発用の設計文書と意思決定記録。
- `tests/`: 開発用のテスト。fixturesには配布・管理の許可があるテストデータのみ配置。
- `distribution/press-analysis-agent/`: 配布対象のルート。
  - `AGENTS.md`: 通常の解析運用用の指示。
  - `.agents/skills/press-analysis/`: 解析実行・入力準備・既存結果確認のSkillと設定手順。
  - `docs/`: 専門知識・評価基準・レポート記載基準。
  - `assets/report/`: 共通HTMLテンプレートとJSON記載例。
  - `scripts/`: 決定論的な解析・検証処理。
  - `processes/`: 解析種類ごとのGH定義と固定資材。`_template/` は開発用の配置ひな形。
  - `schemas/`: データ契約。
  - `defaults/`: 設定テンプレートと実行用フォルダーのひな形。
  - `config/`: Git管理しない利用者設定。
  - `workspace/runs/<process-id>/<run-id>/`: Git管理しない実行ごとの入力、作業データ、結果。

配布先での配置とGH連携の論点は `distribution/press-analysis-agent/README.md` を参照してください。

通常運用では定義領域を変更しません。実行前後のハッシュ検証は実装済み、OS権限による書き込み保護は今後整備します。
GitタグとGitHub Releasesによる配布を予定しています。ライセンスとリリース手順は未決定です。
