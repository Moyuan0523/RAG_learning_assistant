# Skill: GitHub Actions CI/CD

> 本專案透過 GitHub Actions 在 push / PR 到 `main` 時自動執行品質檢查。

---

## Workflow 總覽

**檔案**：`.github/workflows/lint.yml`
**名稱**：`Lint & Security Check`

```
觸發條件
├── push → main
└── pull_request → main

Job: lint (ubuntu-latest)
├── 1. Checkout 程式碼
├── 2. 安裝 Python 3.10
├── 3. 安裝工具 (ruff, detect-secrets)
├── 4. Ruff lint check        ← ruff check .
├── 5. Ruff format check      ← ruff format --check .
└── 6. Detect secrets scan    ← detect-secrets scan ...
```

## 與 Pre-commit 的對應關係

| 檢查項目 | Pre-commit (本地) | CI (雲端) |
|----------|------------------|-----------|
| Ruff lint | ✅ `ruff --fix` (自動修復) | ✅ `ruff check .` (只檢查) |
| Ruff format | ✅ 自動格式化 | ✅ `ruff format --check .` (只檢查) |
| detect-secrets | ✅ 用 baseline 比對 | ✅ 用 baseline 掃描 |
| trailing-whitespace | ✅ | ❌ |
| end-of-file-fixer | ✅ | ❌ |
| check-yaml/json | ✅ | ❌ |
| check-added-large-files | ✅ | ❌ |

> **關鍵差異**：Pre-commit 會自動修復（`--fix`），CI 只做檢查不修改。
> 如果本地跑過 `pre-commit run --all-files` 且通過，CI 通常也會通過。

## CI 失敗的排查流程

### 步驟 1：確認失敗的 step

到 GitHub Actions 頁面查看哪個 step 失敗：
- `Ruff lint check` → 程式碼品質問題
- `Ruff format check` → 格式問題
- `Detect secrets` → 偵測到機密

### 步驟 2：本地重現

```bash
# 模擬 CI 環境檢查
ruff check .
ruff format --check .
detect-secrets scan --exclude-files '^(Sources/|datasets/|chunks/|logs/)' --baseline .secrets.baseline
```

### 步驟 3：修復後推送

```bash
# 修復 lint 問題
ruff check . --fix

# 修復格式問題
ruff format .

# 確認全部通過
pre-commit run --all-files

# 提交修復
git add -A && git commit -m "fix: resolve lint and format issues"
git push
```

## 新增 CI 步驟的指引

如果需要擴充 CI workflow，遵循以下原則：

1. **與 pre-commit 保持一致**：CI 檢查的項目應與 pre-commit 對齊
2. **只檢查不修改**：CI 使用 `--check` 模式，不要自動修改檔案
3. **排除相同目錄**：`Sources/`, `datasets/`, `chunks/`, `logs/`
4. **使用 Python 3.10**：與專案 `requires-python` 一致

### 擴充範例：加入單元測試

```yaml
- name: Install dependencies
  run: pip install -r requirements.txt

- name: Run tests
  run: pytest tests/ -v
```

## 工作流程圖

```
開發者修改程式碼
       │
       ▼
  git commit
       │
       ▼
 ┌─────────────┐
 │ pre-commit   │ ← 本地自動檢查 + 修復
 │ (ruff, etc.) │
 └──────┬──────┘
        │ 通過
        ▼
   git push
        │
        ▼
 ┌─────────────┐
 │ GitHub CI    │ ← 雲端只檢查不修復
 │ (lint.yml)   │
 └──────┬──────┘
        │ 通過
        ▼
   ✅ 合併到 main
```
