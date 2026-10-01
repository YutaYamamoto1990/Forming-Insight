# process-test — ローカル実行確認済み

共有された `process_test.gh` と `hemi.draw.k` の静的確認・実行確認記録です。接続設定を `process.json` に登録しています。実行確認済みのHidden設定GHを `gh/process_test.gh`、画像出力確認済みcfileを `post/original.cfile` に保管し、process.jsonから参照します。入力データは同梱しません。独立したcal_setup.kはこのプロセスでは使用しません。

## 確認した環境

- Rhino: 8.32.26160.13001（ローカル実行ファイルのバージョン）
- Hops: 0.17.0のインストール先にHopsとRhino.Computeの実行ファイルを確認
- GHの保存済み参照: MinerGH 1.1.4.0、LoggerGrasshopper 1.1.2.0
- MinerGHとLoggerのローカルファイル配置と、ComputeによるGHロード・実行を確認
- テスト所要時間: 約30秒（利用者申告）。完了応答待ちの既定値: 600秒

## GHの静的確認

Rhino付属のGH_IOを使ってGHアーカイブをXMLへ変換しました。GHのソリューションやソルバーは実行していません。

- 入力はGrasshopperの `Get File Path`（Description: `Contextual file path input.`）から `File Path` を経て、解析コンポーネントの `K` に接続されています。Computeの `/io` で入力名 `Get File Path`、型Text、出力名 `Tx` を確認しました。
- 解析コンポーネントはMinerGHの `Run Dyna Sync (Toreo)`。保存済みの説明は同期実行を示しますが、実際の待機・失敗時動作は静的確認だけでは確定できません。
- 解析コンポーネントの出力は `D / AnalysisDirectory` で、Panelと `Context Print` の `Tx` に接続されています。
- 明示的なdone出力、run-id入力、作業フォルダー入力はありません。利用者の指定により、通常のGH応答受信を成功扱いとします。これはソルバー内部の成功証明ではありません。要求とrun-idはAgent側で対応付けます。
- 保存済みの選択はSingle、SMP、Normal、Overwrite、ANSYSです。配布時の既定値としての採用は未決定です。特に原本を上書きしない出力配置と、外部実行時のウィンドウ設定を確認します。
- GHには環境固有の設定も含まれるため、利用先でソルバー等の設定を確認します。

## kファイルの静的確認

- ファイルサイズ: 213,074 bytes
- `*KEYWORD` と `*END` を確認
- `*INCLUDE` 系キーワードは確認範囲内で検出されませんでした
- メッシュ・材料・接触・出力指定等を含む入力です。ソルバーによる妥当性検証はまだ行っていません

## コピーと実行状態

検証用run: `inspection-20260918-163608-dc969cff`

`workspace/runs/process-test/<run-id>/input/` にGHとkファイルを原本からコピーし、両方ともSHA-256の一致を確認しました。`exchange/inspection-manifest.json` にコピー元とハッシュ、`work/process_test.ghx` に静的確認用のXMLを保存しました。これらはGit管理対象外です。

この静的確認用runの状態は `prepared_not_executed` です。原本は変更していません。後続の実解析は以下の別runで行いました。

## 実行確認（2026-09-18）

- 最初の実行 `20260918T075147Z-5c88d7f7e0a8` は日本語パスがソルバー起動時に文字化けし、入力待ちになりました。このrunに対応するソルバーのみ停止しました。停止後もGHは通常応答を返しました。このrunの `exchange/test-observation.json` に中止理由を記録しています。成功フラグがGH応答だけに基づくことの実例です。
- 英数字のjunction経由で再実行した `20260918T075451Z-6560bdd602bd` ではHTTP 200の応答を受信しました。要求からRaw保存まで約3秒、ComputeログのGH処理時間は約2.61秒でした。利用者申告の約30秒とは実行条件によって異なります。
- `raw/solver/` に `d3plot`、`d3plot01`、`d3plot02`、`glstat`、`matsum`、`messag` 等を保存しました。ログには `Normal termination` に相当する表記を確認しました。汎用runner自体にソルバー内部の正常終了判定を追加したわけではありません。
- 元のkファイルとGHを変更せず、検証用GHコピーのウィンドウ設定だけNormalからHiddenに変更しました。ファイル入力はコピーした `work/solver/input.k` を指します。
- 600秒の待機設定を使用しました。短い期限でのタイムアウト、HTTPエラー、重複実行防止、原本保全、定義変更検出はローカルHTTPテストで検証しています。実ソルバーを600秒動かす長時間試験は未実施です。

## 残る範囲

このrunnerは入力パス1つのGHを対象とし、結果が入力と同じ実行用フォルダーに出る前提です。別解析の追加時はこの条件を確認します。ポスト処理はd3plotと設定済みPNG群を必須とし、run_pipeline.pyで下書きHTMLまで生成できます。コンポーネントのソースコード提供や追加のdone出力は要求しません。
