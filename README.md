# Forming Insight

Surfaceを入力とし、決定論的なプレス解析と根拠に基づくLLMの解釈を分離してレポートを生成する、配布可能なCodex用Agentの開発リポジトリです。

リポジトリ: https://github.com/YutaYamamoto1990/Forming-Insight

## 現在の状態

初期フォルダー構成を準備しました。解析機能はまだ実装していません。
Surface形式、計算内容・解析エンジン、解析条件、Raw形式、最終レポート形式は未決定です。

## 構成

- `AGENTS.md`: 開発用の常設指示。
- `design/`: 開発用の設計文書と意思決定記録。
- `tests/`: 開発用のテスト。fixturesには配布・管理の許可があるテストデータのみ配置。
- `distribution/press-analysis-agent/`: 配布対象のルート。
  - `AGENTS.md`: 通常の解析運用用の指示。
  - `.agents/skills/press-analysis/`: Skillの配置先。SKILL.mdは今後作成。
  - `docs/`: 専門知識と評価基準。
  - `scripts/`: 決定論的な解析・検証処理。
  - `schemas/`: データ契約。
  - `defaults/`: バージョン管理する設定テンプレート。
  - `config/`: Git管理しない利用者設定。
  - `workspace/input/`, `workspace/work/`, `workspace/output/`: Git管理しない入力と実行生成物。

通常運用では定義領域を変更しません。書き込み権限による保護やハッシュ検証は今後実装します。
GitタグとGitHub Releasesによる配布を予定しています。ライセンスとリリース手順は未決定です。
