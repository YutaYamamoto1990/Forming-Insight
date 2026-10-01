# Press Analysis Agent

## 現在の状態

入力コピー、ローカルRhino.Compute経由でのGH呼び出し、既定600秒の応答待ち、Raw保存を実装しています。Rhino 8と共有テストGH/kファイルで実行確認済みです。解析実行・入力準備・既存結果確認を担当するpress-analysis Skillを用意しています。LS-PrePostによる画像生成を実機検証済みです。共通HTMLテンプレートとレポート生成スクリプトを用意しています。GHから画像出力・下書き生成までの接続を実装しています。専門的な評価基準は未整備です。

## Codexへの依頼

この配布フォルダー全体を作業対象として開き、入力パスと解析種類を指定します。[press-analysis Skill](.agents/skills/press-analysis/SKILL.md) が設定確認から結果案内までを担当します。例えば「process-testで E:/data/model.k を解析してください」「入力を準備するだけにしてください」「run-idを指定してd3plotの場所を教えてください」のように依頼できます。明示的にSkillを指定する場合は `$press-analysis` を使用します。

Skillは同梱のscripts・processes・configを参照するため、Skillフォルダー単体では配布しません。初回はGHファイルの場所など利用環境の設定が必要です。

## 責務

- 利用者: 入力kファイルのパスと使用する解析プロセス、必要な条件を指定する。
- Agent: 実行用フォルダーを用意し、入力をコピーし、GHを外部から起動して完了を待つ。
- GH: 入力kファイルを読み、解析処理を行い、解析終了まで待って応答を返す。
- Agent: 通常のGH応答を受信したら成功とみなし、結果を保存してポスト処理へ引き渡す。明示的なdone値は要求しない。

解析内容は各GHフローに保持します。Agent側で同じ解析ロジックを再実装しません。

## 配置

```text
press-analysis-agent/
├── AGENTS.md
├── .agents/skills/press-analysis/
├── assets/report/                 # HTMLテンプレート・JSON記載例
├── docs/
├── scripts/
├── schemas/
├── processes/                      # 利用者が明示的に追加・編集できる解析定義
│   ├── README.md
│   ├── _template/                  # 実行対象ではない配置ひな形
│   │   ├── README.md
│   │   ├── gh/                     # GH定義
│   │   └── assets/                 # GHが参照する固定資材
│   └── <process-id>/               # 実際の解析プロセス追加時に作成
├── defaults/
│   └── run-template/              # 実行用フォルダーのひな形
│       ├── input/
│       ├── work/
│       ├── raw/
│       ├── logs/
│       ├── exchange/
│       ├── post/
│       └── report/
├── config/                         # 利用者の環境・解析条件
└── workspace/
    └── runs/
        └── <process-id>/
            └── <run-id>/           # 実行ごとにrun-templateから作成
                ├── input/         # コピーした入力原本
                ├── work/          # 解析用kファイル・中間ファイル
                ├── raw/           # GH/解析エンジンが出力する結果
                ├── logs/          # 起動・解析・待機のログ
                ├── exchange/      # 起動要求・応答の記録用領域
                ├── post/          # Rawから生成した派生データ
                └── report/        # 最終レポート
```

山括弧付きのディレクトリは実行時またはプロセス追加時に作成します。現在は `process-test` の接続設定を登録しています。GHファイル本体は利用者設定で指定します。`.gitkeep` は空フォルダーをGitに保持するためのファイルで、解析入力ではありません。

従来の入力・作業・出力を別々に置く案から、1回の実行に必要なデータを1つのrunフォルダーにまとめる構成へ変更しています。

## 実行用フォルダーの扱い

1. 使用するprocess-idを確定する。複数候補がある場合は推測で選ばない。
2. 新しいrun-idを発行し、`defaults/run-template/` と同じディレクトリ構成を `workspace/runs/<process-id>/<run-id>/` に作成する。既存runは再利用しない。
3. 利用者指定のkファイルを `input/` へコピーする。コピー元とファイル名は保持する。関連ファイルを必要とする入力のコピー範囲は事前に確認する。
4. GHもinputへコピーし、入力・GHのハッシュ、プロセス設定、実効タイムアウト、要求と応答を `exchange/` に記録する。
5. 実行用コピー `work/solver/input.k` を用意し、そのパスをGHの公開入力へ渡す。GHと各要求は1つのrun-idに対応付ける。GHは入力の隣に結果を出す構成を前提とする。
6. HTTPの正常応答かつComputeの結果JSON（values配列を含む）を受信したら成功扱いとする。GH応答中のerrors・warningsは記録するが、利用者指定の判定ではそれ自体を失敗条件にしない。HTTPエラー、通信切断、不正な応答、タイムアウトは状態未確定とする。
7. GHの未加工応答を `raw/gh-response.json`、作業結果のコピーを `raw/solver/` に保存し、ハッシュ一覧を確定する。現在はポスト処理待ちの状態まで進む。確定したRawは変更しない。

GHの既存フローが別の出力配置を必要とする場合は、その配置との対応をプロセス単位で定義します。接続のために既存GHを無断で改変しません。

## GH連携で決める事項

GHが解析終了まで待ち、その通常応答の受信を成功と扱う方針です。成功根拠は `gh_response_received`、`solver_success_verified` はfalseと記録します。ソルバー内部の成功確認やコンポーネントのソースコード共有は要求しません。接続の根拠は [調査メモ](processes/gh-integration.md) を参照してください。

- 別の解析種類を追加するときは、GHの公開入力名と結果の出力配置を確認する。
- 初版は入力パス1つを受け取るGHに対応。追加パラメーター・複数入力の引き渡しは今後拡張する。
- ポスト処理で必須とする結果ファイルは解析種類ごとに今後決める。必要なファイルが不足した場合はポスト処理エラーとして別に記録する。
- 完了応答の待機上限は既定600秒（10分）とし、利用者設定で変更可能にする。テスト解析の所要時間は利用者申告で約30秒。具体的なタイムアウト設定、GH/解析側の異常検出、キャンセル方法は接続時に確認する。
- 結果ファイルの一覧と出力先、入力に関連ファイルがある場合の受け渡し範囲。
- 複数runの同時実行可否。確認までは同時起動しない。

`exchange/` に実行記録、送信JSON、接続確認の応答、定義ハッシュ、Rawハッシュを保存します。doneファイルは使いません。

応答待ちの上限に達しても、解析プロセスが停止したとはみなしません。状態未確定として記録し、同じ解析を自動で再起動しません。

## 定義の保護とGit管理

`processes/` と `defaults/` を含む定義領域は通常運用で変更しません。GHの保存先やキャッシュ等も作業領域へ向けることを連携時に確認します。環境固有のパスや解析条件は `config/`、実行時のデータは `workspace/` に置きます。

利用者設定と実行データは開発リポジトリの `.gitignore` で管理対象外です。実行前後の定義・入力ハッシュ照合、確定Rawのハッシュ記録を実装しています。ポスト処理前後のRaw再照合も実装済みです。OS権限による書き込み防止は今後実装します。

## 実行方法

必要環境はWindows、Rhino 8、対応するHops、GHの依存プラグインと解析エンジン、Python 3.11以降です。Python側の追加パッケージは不要です。初版は同じPCのComputeのみ対応します。

1. `defaults/user-config.example.json` を `config/user-config.json` にコピーし、GHファイルのパスとCompute URLを指定します。JSON内のWindowsパスは `/` を使うか `\\` と記載します。共有テストGHとソルバーの実行条件はこのリポジトリに同梱していません。
2. 未起動の場合、PowerShellで `scripts/start_compute.ps1 -ComputeExe <インストール済みrhino.compute.exeのパス> -Port 6500` を実行します。起動ログは `workspace/services/` 以下です。既に起動したComputeを使う場合は、そのURLを設定します。
3. Pythonで次を実行します（配布フォルダーを作業ディレクトリとした例）。

```powershell
python scripts/run_analysis.py --process process-test --input 'E:/path/to/model.k'
```

`--prepare-only` を付けると、入力コピーとフォルダー準備だけで終了します。`--config <path>` で設定ファイルを指定できます。コンソールにはrunの保存先と状態をJSONで表示します。実行記録は `exchange/run.json` です。

入力は単一のkファイルに対応します。`*INCLUDE` 系の参照がある入力は、関連ファイルのコピー漏れを防ぐため初版では実行前に停止します。

Compute側のタイムアウトも600秒以上に設定してください。起動スクリプトはプロセス限定の設定で660秒を指定し、マシン全体の環境変数を変更しません。APIキーを使う場合は `api_key_environment` にキーを格納した環境変数名を設定します。キー自体は実行記録へ保存しません。

## 日本語パスへの対応

共有GHが起動するソルバーでは、日本語を含む実行パスが文字化けすることをテストで確認しました。必要な場合は `execution_path_alias_root` に、英数字のみ・空白なしの絶対パス（例: 利用者のTemp配下）を指定します。

実行ごとに、その場所へ `work/solver/` を指すWindowsのjunctionを作成し、GHへは別名パスを渡します。入力・計算結果の実体は配布フォルダー内です。別名は実行記録に残し、状態未確定の解析を壊さないよう自動削除しません。原本GHは変更せず、process-testは検証済みのHidden設定GHを配布原本として使用します。

## 失敗・再実行

1度の呼び出しで `/io` による接続確認と `/grasshopper` による実行要求を各1回送ります。解析要求は自動再送しません。同時実行は `workspace/.analysis.lock` で防止します。

解析要求の送信後に応答が不明になった場合は `unknown` を保存してロックを残します。次の解析を開始する前に、そのrunのログと解析プロセスの状態を確認し、停止・完了を確認できた場合だけ運用担当者がロックを解除してください。タイムアウト自体はソルバーを停止しません。

## HTMLレポート

[レポート記載基準](docs/report-guidelines.md) と [JSON記載例](assets/report/report-data.example.json) に従ってデータを作成し、`scripts/render_report.py` でHTMLを生成します。画像は埋め込み形式で、HTML単体を共有できます。生成先は各runの `report/<report-id>/`。再生成には別IDを使用します。Skillは下記パイプラインとAgentによる画像確認・レポート仕上げを組み合わせます。


## 入力からレポート下書きまで

利用者設定に `lsprepost_executable` と `processes.<id>.postprocess.cfile` を指定し、`python scripts/run_pipeline.py --process process-test --input <kファイル>` を実行します。画像出力待ちは `post_timeout_seconds`（既定600秒）です。GH・固定資材cal_setup.k・cfileの原本はprocessesに同梱します。入力形状kやソフトウェア実行ファイルは同梱しません。

登録cfileのコマンドはLS-PrePostへ渡します。スクリプトはd3plot・PNGのパス置換と出力検証を担当します。PNG欠損・破損・終了コード異常はエラー、タイムアウトは状態未確定です。Rawと定義のハッシュを実行前後に照合します。

生成したHTMLは下書きです。Codexが各画像を確認し、根拠付きコメントを記述して別report-idへ最終版を出力します。解析スクリプトからLLMを呼び出す仕組みや、固定文による専門評価は実装しません。通常の解析依頼でこの仕上げを行う手順をSkillに定義しています。

## 一般的な評価知識

[プレス成形の評価項目と注意点](docs/evaluation-criteria.md) に公開資料の要約・必要な出力・適用限界を整理しています。材料・製品固有の合否しきい値は未設定です。


## 複数フォルダー構成のプロセス

`processes/press-z/README.md` に形状入力・実行用k・cal_setup.kの配置契約を記載しています。`layout.input_file` と `layout.result_directory` はwork/solverからの相対パスです。`assets` は原本をinput/assetsへ保管し、指定の実行配置へコピーします。入力形状自体のincludeや固定資材の入れ子includeは未対応です。

待機時間は利用者のプロセス別設定、プロセス定義、全体設定、600秒の順で決定します。press-zは1200秒です。Compute起動時に `-ProcessId press-z` を指定すると、この設定からサーバー待機を1260秒以上にします。起動済みComputeの設定は自動変更しません。GH内の固定出力先をrun相対に修正・確認するまでは準備のみ実行します。

press-zの更新GHは `output_directory_parameter` で出力先を公開します。Agentが実行ごとにinput_runのパスを渡すため、固定パスの置換やGHの書き換えは不要です。

## 配布後のプロセス編集

利用者は明示的な追加・編集作業として `processes/` を変更できます。通常の解析実行中は原本を変更しません。配置と手順は [プロセス管理](processes/README.md) を参照してください。同梱原本はprocess.jsonから参照されるため、configでGHやcfileのパスを指定する必要はありません（外部原本への上書きは可能です）。

### cfileの実行契約

明示的に登録したcfileを実行対象とします。コマンドの許可リストは設けず、解釈・実行はLS-PrePostに任せます。原本を保存したまま作業コピー上の `openc d3plot "..."`（1件）と `print png "..."` のパスを置換し、表示窓など後続オプションは維持します。置換できない形式、画像名の不一致・重複は実行前に停止します。他のコマンドや追加のファイル参照はそのまま渡すため、そのパスと副作用はプロセス編集時に確認してください。実行後は設定された全PNGの整合性とRaw・定義の不変性を確認します。
