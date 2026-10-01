# press-z

入力形状kをGHへ渡し、GHが実行用kの生成と解析を担当します。通常応答を成功扱いとする方針は既存プロセスと共通です。

## 実行配置

```
run/
  input/入力原本.k
  input/assets/cal_setup.k
  work/solver/
    input_shape/input.k    # GHへ渡す形状コピー
    input_run/             # GHがinput.kと解析結果を生成
    cal_setup.k            # input_run/input.kの ../cal_setup.k
  raw/solver/              # input_runの保存コピー
  raw/cal_setup.k          # Raw内でも相対includeを維持
```

GHは `gh/process_press-z.gh`、固定資材は `assets/cal_setup.k` を原本として使用します。利用者設定で上書きしない限りprocess.jsonの配布ルート相対パスを使用します。GHの出力先には、外部入力Get File Path_cal directoryを使用します。Agentが今回のinput_runのパスを渡します。

待機時間は1200秒。優先順位は利用者設定processes.<id>.timeout_seconds、process.json、全体設定、600秒です。Compute起動スクリプトに `-ProcessId press-z` を渡すと、1260秒以上のサーバー待機を設定します。

```
python scripts/run_analysis.py --process press-z --input <形状k> --prepare-only
```

実行時はprepare-onlyを外します。入力形状内のincludeとcal_setup.k内の追加includeは未対応です。GHが生成する ../cal_setup.k は上記配置で対応します。結果はraw/solverへ保存するため既存のレポート保存場所と整合します。ポスト処理原本は `post/press_z_post.cfile` です。旧 `post/lspost.cfile` は保管のみで使用しません。新原本は変形前後・塑性ひずみ・グラフのPNG計4枚を出力します。process.jsonのpostprocessに登録済みです。

## 更新GHの2入力（2026-09-25確認）

Computeの/ioで `Get File Path_input shape` と `Get File Path_cal directory` のText入力を確認しました。前述の固定出力先による保留は解消し、Agentが入力形状パスとinput_runの絶対パスを各入力へ渡します。GHの相対パス化やrun_relative_output_confirmedはこのプロセスでは不要です。原本GHの書き換えは行いません。

## 実行確認

2026-09-25、input_shape_50.kでGHの2入力を通した解析を実行。run-idは20260925T042554Z-c6259eb37d67。約8分16秒で通常応答を受信し、GH errors/warningsは空。Raw結果とcal_setup.kの相対配置を保存しました。判定方針はgh_response_receivedのままです。
