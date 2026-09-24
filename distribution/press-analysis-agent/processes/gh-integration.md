# GH外部実行の調査メモ

調査日: 2026-09-18。公式資料に基づく接続方式と、利用者と合意した待機方針を記録します。実機検証結果は [process-test](process-test/README.md) を参照してください。

## 確認できたこと

- HopsはRhino.Computeを呼び出すGrasshopper側のクライアント。外部のHTTPクライアントからRhino.Computeを呼び出すこともできる。[公式FAQ](https://developer.rhino3d.com/guides/compute/compute-faq/)
- HopsはヘッドレスのRhino/GHで定義を評価する。現在開いているGHキャンバスの操作を前提とする仕組みではない。[What is Hops](https://developer.rhino3d.com/guides/compute/what-is-hops/)
- GH定義の入出力を公開して呼び出し、結果をHTTP応答で返す仕組みがある。[How Hops Works](https://developer.rhino3d.com/guides/compute/how-hops-works/)
- Python用の公式クライアントがある。[Calling Compute with Python](https://developer.rhino3d.com/guides/compute/compute-python-getting-started/)
- HopsのAsynchronous設定は待機中のUIをブロックしないためのもの。長時間処理ではクライアント側とサーバー側のタイムアウトを別々に考慮する。[Hops Component](https://developer.rhino3d.com/guides/compute/hops-component/) / [公式FAQ](https://developer.rhino3d.com/guides/compute/compute-faq/)

## このAgentへの適用

Agent → Python呼び出しスクリプト → ローカルRhino.Compute → 対象GH定義 → 解析エンジン、という構成を実装した。共有GHには実行用kファイルのパスを文字列として渡し、要求とrun-idの対応はAgent側で記録する。HTTPでパスを渡すだけではファイルは転送されないので、初版は同じPCでの実行に限定する。

利用者の指定により、明示的な `done` 値は追加しない。GHからの通常応答の受信を、Agentの成功判定に用いる。

## 合意した待機方針

GHは外部解析の終了まで待って応答する構成とする。利用者との合意により、HTTP正常応答としてComputeの結果JSONを受信したら成功扱いにする。ソルバー内部の成功検証は要求せず、成功根拠を `gh_response_received` と記録する。応答中の警告・エラーは隠さず保存する。

1回の実行要求に対するHTTP応答を待つ。GHへrun-idの入出力を追加する必要はない。`/io` で公開入力 `Get File Path`、出力 `Tx` を確認し、`/grasshopper` へ要求する。`cachesolve` はfalseとする。APIの根拠: [Rhino 8 Computeのエンドポイント実装](https://github.com/mcneel/compute.rhino3d/blob/8.x/src/compute.geometry/ResthopperEndpoints.cs)。

利用者の申告ではテスト解析は約30秒。Agentの完了応答待ちの既定値は10分（600秒）で、利用者設定で変更可能。短いタイムアウトでの疑似応答試験と、共有GHでの実解析を実施した。実際に600秒待たせる長時間試験は未実施。

Rhino.Computeを使う場合は、意図した600秒の待機が途中で打ち切られないようクライアント・サーバー両側のタイムアウトを整合させる。具体的な設定方法と起動時間等の余裕は実機で確認する。通信切断やタイムアウトは解析終了の証拠ではないため、状態未確定として記録し、自動再送やポスト処理への移行を行わない。待機上限到達だけで解析プロセスを強制終了しない。

## 提供された最小構成の画像

画像では、ファイルパス取得からC#コンポーネントを経て解析コンポーネントのK入力へ接続されている。解析コンポーネントにはLSRunDir、DynaDir、Run等の入力があり、出力はファイルパスを表示するパネルとテキスト出力コンポーネントへ接続されている。

その後、共有GHに対して文字列パスの外部入力と応答受信を実機確認した。明示的なdone出力は不要と合意している。画像中のローカルパスを配布用の既定値にはしない。

## 検証対象と残る範囲

1. 利用するRhino/Hops/Computeの版と、ローカル起動方法。
2. 小さなGH定義へrun-idとパスを渡し、その値を応答として受け取れること。
3. 既存GHの依存コンポーネント、外部ソルバー、ライセンスがヘッドレス実行で動くこと。
4. 合意したとおりGHが外部解析完了まで待つこと。約30秒のテスト解析による実測と、既定600秒の待機設定。
5. 通常応答の受信と通信失敗を区別すること。必要な結果ファイルの判定は今後のポスト処理で扱う。
6. 実行要求のキャッシュや再送で解析が省略・重複しないこと。runごとに異なるIDを渡し、状態未確定時に自動再実行しないこと。

現在のローカルRhino 8/Hops 0.17.0でロードと実解析を確認済み。その他のGH・実行環境、複数入力、ポスト処理は今後の対象。
