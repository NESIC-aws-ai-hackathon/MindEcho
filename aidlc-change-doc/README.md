# GitHub Copilot向け AIDLC 展開パッケージ

このパッケージは GitHub Copilot での運用を前提に、
ドキュメントを aidlc-docs ではなく copilot-docs に配置しています。

## 構成
- copilot-docs/AIDLC-CHANGE-DELTA.md
- copilot-docs/README.md
- .github/ (Copilot 設定/指示ファイル)
- .aidlc-rule-details/inception/requirements-analysis.md
- .aidlc-rule-details/construction/code-generation.md
- .aidlc-rule-details/construction/build-and-test.md
- .aidlc-rule-details/common/workflow-changes.md
- .aidlc-rule-details/common/error-handling.md
- .aidlc-rule-details/common/terminology.md

## 適用手順
1. 展開先リポジトリでバックアップ取得
2. .aidlc-rule-details 配下を上書きコピー
3. .github 配下を上書きコピー
4. copilot-docs/AIDLC-CHANGE-DELTA.md で変更点レビュー
