# AI-DLC 仕様変更/バグ修正ガバナンス 組み込み差分仕様書

## 1. 目的
修正依頼を以下の2系統に強制分岐し、AI-DLC運用の一貫性と監査可能性を高める。

1. 仕様書未記載: 仕様変更として扱う
2. 仕様書記載済みかつ実装不一致: バグ修正として扱う

本仕様書は、現行ルールに対する組み込み差分を定義する。

## 2. 適用範囲
以下のルールファイルを変更対象とする。

1. .aidlc-rule-details/inception/requirements-analysis.md
2. .aidlc-rule-details/common/workflow-changes.md
3. .aidlc-rule-details/construction/code-generation.md
4. .aidlc-rule-details/construction/build-and-test.md
5. .aidlc-rule-details/common/error-handling.md
6. .aidlc-rule-details/common/terminology.md
7. .github/copilot-instructions.md

## 3. To-Be ワークフロー

### 3.1 修正依頼トリアージ
修正依頼を受けたら、実装変更前に必ず Inception 成果物を照合する。

照合対象の優先順位:
1. aidlc-docs/inception/requirements/requirements.md
2. aidlc-docs/inception/user-stories/stories.md
3. aidlc-docs/inception/application-design/application-design.md

判定ロジック:
1. 仕様未記載: 仕様変更ルート (SPEC_CHANGE)
2. 仕様記載ありかつ実装不一致: バグ修正ルート (BUG_FIX)
3. 仕様記載ありかつ実装一致だがユーザー期待不一致: 仕様変更ルート (SPEC_CHANGE)
4. 判定不能: 要件分析に戻って明確化質問を実施

### 3.2 仕様変更ルート
1. 要件/仕様書へ追記
2. 影響分析 (影響を受けるユニット・設計・テストの特定)
3. 影響範囲を含めてユーザー承認
4. 実装修正 (影響ユニット含む)
5. テスト
6. 変更履歴記録

### 3.3 バグ修正ルート
1. 不一致根拠の明示
2. 実装修正
3. 回帰テスト必須実行
4. バグ修正履歴記録

## 4. 差分仕様 (パッチ形式)
以下は実装時に適用すべき差分の規範。

### 4.1 inception/requirements-analysis.md
```diff
@@ Step: Analyze User Request (Intent Analysis)
+#### 2.5 Change Classification Gate (MANDATORY for modification requests)
+- If request is a modification/fix, MUST classify before implementation:
+  - Spec Not Documented -> SPEC_CHANGE
+  - Spec Documented but Behavior Mismatch -> BUG_FIX
+  - Spec Documented + Implementation Matches + User Expectation Mismatch -> SPEC_CHANGE
+  - If unclear, return to clarification questions and stop progression
+
+#### 2.6 Evidence Capture (MANDATORY)
+- Create `aidlc-docs/inception/requirements/change-classification.md`
+- Include:
+  - Request summary
+  - Referenced inception artifacts and sections
+  - Classification result (SPEC_CHANGE/BUG_FIX)
+  - Rationale
@@ Step: Generate Requirements Document
+- If classification == SPEC_CHANGE:
+  - Update requirements.md with new/changed requirement entries
+  - Mark change as approved before proceeding to implementation stages
+  - Record approval in `aidlc-docs/audit.md` with timestamp and user confirmation reference
```

### 4.2 common/workflow-changes.md
```diff
@@ ## Types of Mid-Workflow Changes
+### 0. Modification Request Classification (MANDATORY)
+
+**Scenario**: User requests a fix or behavior change
+
+**Handling**:
+1. Check inception artifacts for explicit requirement coverage
+2. Classify request as SPEC_CHANGE or BUG_FIX
+3. Route to the corresponding mandatory path
+4. Log classification decision in `audit.md` and change-classification.md
+
+**Do Not Proceed**: No implementation before classification is complete
```

### 4.3 construction/code-generation.md
```diff
@@ Step: Execute Current Step
+- If classification == SPEC_CHANGE:
+  - Verify requirements.md has been updated and approved
+  - Do not proceed if approval evidence is missing from `aidlc-docs/audit.md`
+- If classification == BUG_FIX:
+  - Link implementation step to bugfix-record entry
+  - Preserve existing behavior outside bug scope
@@ Step: Update Progress
+- Update `aidlc-docs/construction/{unit-name}/code/change-log.md`
+- If BUG_FIX, also update `aidlc-docs/construction/{unit-name}/code/bugfix-record.md`
@@ Completion Criteria
+- Every modification has a classification (SPEC_CHANGE/BUG_FIX)
+- Every BUG_FIX has bugfix-record and regression test evidence
@@ Step 15: Wait for Explicit Approval
+- If user requests changes ("Request Changes"):
+  1. MANDATORY: Route through `common/workflow-changes.md` Section 0
+  2. Classify the change request as SPEC_CHANGE or BUG_FIX before any code modification
+  3. If SPEC_CHANGE: update requirements.md → get approval → update plan → then implement
+  4. If BUG_FIX: create bugfix-record → implement fix → regression test required
+  5. Do NOT directly modify code without completing classification
+  6. After classification and implementation, repeat the approval process from Step 14
```

### 4.3b .github/copilot-instructions.md
```diff
@@ Code Generation section
+7. **MANDATORY**: If user chooses "Request Changes", route through
+   `common/workflow-changes.md` Section 0 (Modification Request Classification)
+   BEFORE any code modification. Classify as SPEC_CHANGE or BUG_FIX first.
```

### 4.4 construction/build-and-test.md
```diff
@@ Step: Analyze Testing Requirements
+- If any BUG_FIX exists in this unit, regression testing is MANDATORY
@@ Step: Generate Additional Test Instructions
+- Create `aidlc-docs/construction/build-and-test/regression-test-instructions.md`
+  when classification includes BUG_FIX
+- Regression test scope:
+  - MUST include: the fixed behavior itself
+  - MUST include: directly dependent units (per dependency graph)
+  - SHOULD include: previously passing tests for the modified unit
@@ Step: Validate Test Outcomes
+- Do not mark Build and Test complete for BUG_FIX work
+  until regression tests pass and are recorded
```

### 4.5 common/error-handling.md
```diff
@@ Section: Requirements Analysis Errors
+**Error**: Modification request not classified (SPEC_CHANGE/BUG_FIX)
+- **Cause**: Classification gate skipped
+- **Solution**: Stop execution, classify request with evidence, then resume
+
+**Error**: BUG_FIX implemented without regression evidence
+- **Cause**: Regression step skipped
+- **Solution**: Re-open Build and Test stage, execute regression tests, update records
```

### 4.6 common/terminology.md
```diff
@@ Section: Terminology
+**SPEC_CHANGE**: Requested behavior not documented in approved inception artifacts;
+requires requirements update and approval before implementation.
+
+**BUG_FIX**: Behavior documented in approved inception artifacts but implementation
+does not conform; requires bugfix record and regression evidence.
```

## 5. 非対象
1. デプロイ自動化方式の変更
2. モデル選定ルールの変更
3. 拡張機能 opt-in の仕組み変更
