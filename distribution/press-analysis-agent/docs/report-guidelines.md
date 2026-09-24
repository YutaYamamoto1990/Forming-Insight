# HTMLレポートの作成基準

これはレポート記載のルールであり、成形性の評価基準ではありません。解析理論・材料固有の判定基準は未整備です。

## 責務と出力

AgentはRaw・実行記録・ポスト処理画像と必要な専門資料を参照し、構造化JSONに説明を記述します。`scripts/render_report.py` は値の計算や良否判断を行わず、JSONを `assets/report/template.html` に組み込みます。HTMLは画像を埋め込んだ単独ファイルで、外部通信やJavaScriptを使いません。ブラウザー印刷向けのCSSを含みます。正式なPDF生成は対象外です。

出力は `workspace/runs/<process-id>/<run-id>/report/<report-id>/`。HTML、入力JSONのスナップショット、参照ファイル・テンプレート・生成スクリプトのSHA-256記録を保存します。既存report-idへの上書きは禁止です。ハッシュは出典の同一性を示す記録であり、数値的妥当性の証明ではありません。

## 内容

1. Input: 入力名・プロセス・実行ID。
2. Analysis Conditions: GH、cfile、確認済み条件、未確認条件。
3. Raw Analysis Results: 結果の事実と画像。画像はRawからの派生成果物と明記。
4. Interpretation: 根拠に基づく解釈。推定や未評価を明記。
5. Engineering Comments: 提案を観察事実と分離。
6. Warnings / Uncertainties: 警告、欠損、未確認事項。
7. Evidence: 元ファイルのrun相対パスと識別子。
8. Conclusion: 確認できた範囲と判断できない範囲。

各記述・画像はEvidence IDを付けます。図の観察は見える分布や形状に限定します。画像から読み取った数値は「画像表記」と記し、Rawからの直接抽出と混同しません。時刻単位、材料、板厚、境界条件を推測で補いません。表示範囲の違う図では自動スケールの最小値が異なる場合があるため、色だけで比較しません。グラフがなければ生成済みと記しません。

GH応答の受信とソルバー内部の成功検証を区別します。失敗・状態未確定のrunからレポートを作る場合は、その状態をタイトル・結論にも明示します。生成スクリプトは実行記録の状態を自動掲載しますが、文章の正確性はAgentが確認します。

## JSONと実行

`assets/report/report-data.example.json` をrun内の `report/` にコピーして編集します。サンプル内の例示値とEvidenceを実データに置き換えます。全8セクション、figures、evidenceを用意します。不要な配列は空配列にできますが、未評価の理由はwarnings/conclusionに記載してください。

Evidenceパスは同一run内の既存ファイル、図は同一runのpost内のPNGに限定します。専門資料を参照する場合は必要な資料をrunのreport内へコピーし、元資料の版と出典を併記します。資料のコピーは原本の変更ではありません。

```powershell
python scripts/render_report.py --run 'workspace/runs/process-test/<run-id>' --data 'workspace/runs/process-test/<run-id>/report/report-data.json' --name report-001
```

生成後はHTMLを開いて、画像、見出し、凡例、出典、未確認事項を確認します。GH→LS-PrePost→レポートの自動連結は未実装です。

## 第2版の表示方針

日本語の見出し・本文に統一し、標準4図は2列で配置します。A4約2枚を目安に余白を詰め、解釈以降を2ページ目に配置します。図中の解析ソフト原出力は改変しません。本文の参照リンク・ハッシュ一覧は表示せず、入力ファイルと解析結果の保存場所だけを掲載します。根拠ID・参照資料・ハッシュは添付JSONに保持します。長い内容は省略せず、必要ならページ数を増やします。
