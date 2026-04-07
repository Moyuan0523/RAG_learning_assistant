# Skill: 自動提交工作流程（Commit Workflow）

> 當用戶說「上 Code」、「commit」、「提交變更」時，執行以下完整 Git 流程。

---

## 觸發詞

- 「上 Code」
- 「commit」
- 「提交變更」
- 「推上去」
- 「上版」

---

## 完整流程

### 1. 檢查變更

```bash
git status
git diff --stat
```

確認有哪些檔案被修改、新增或刪除。

### 2. 建立功能分支

根據變更內容自動命名：

```bash
git checkout -b <type>/<描述性名稱>
```

**命名規則**：

| 類型 | 前綴 | 範例 |
|------|------|------|
| 新功能 | `feature/` | `feature/add-streaming-response` |
| 修復 | `fix/` | `fix/embedding-dimension-mismatch` |
| 重構 | `refactor/` | `refactor/retriever-pipeline` |
| 文件 | `docs/` | `docs/update-readme` |
| 維護 | `chore/` | `chore/update-dependencies` |

### 3. 暫存檔案

```bash
git add <相關檔案>
```

**不要加入以下檔案**：
- `__pycache__/`
- `*.pyc`
- `.env`
- `chunks/`
- `datasets/`
- `logs/`
- `building_note/`
- `testing/`
- `evaluation_reports/`
- `.DS_Store`

### 4. 執行品質檢查

```bash
# 在 commit 前執行 pre-commit
pre-commit run --all-files
```

如果失敗：
1. 讓 ruff 自動修復：`ruff check . --fix && ruff format .`
2. 重新暫存修復的檔案：`git add -u`
3. 再次執行：`pre-commit run --all-files`

### 5. 提交變更

使用 Conventional Commits 格式：

```
<type>: <簡短描述>

## 變更內容
- <具體變更 1>
- <具體變更 2>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

**Type 類型**：

| Type | 說明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修復 Bug |
| `refactor` | 重構（不改功能） |
| `docs` | 文件更新 |
| `test` | 測試相關 |
| `chore` | 維護工作（依賴更新、CI 調整等） |
| `style` | 程式碼格式（不影響邏輯） |

### 6. 推送分支

```bash
git push -u origin <branch-name>
```

### 7. 合併到主線（視情況）

```bash
git checkout main
git pull origin main
git merge <branch-name> --no-edit
git push origin main
```

### 8. 清理分支

```bash
git branch -d <branch-name>
git push origin --delete <branch-name>
```

### 9. 報告結果

顯示完成摘要：
- ✅ 提交的檔案數量
- ✅ 分支名稱
- ✅ Commit hash
- ✅ 遠端推送狀態
- ✅ CI 狀態（如可查詢）

---

## 互動確認

在以下關鍵步驟前，**必須詢問用戶確認**：

1. **步驟 3 後**：顯示即將提交的檔案清單，確認無誤
2. **步驟 5 前**：顯示 commit message 草稿，確認內容
3. **步驟 7 前**：確認是否要直接合併到 main

---

## 緊急提交（跳過檢查）

如果用戶明確要求跳過檢查：

```bash
git commit --no-verify -m "<message>"
```

> ⚠️ 僅在緊急情況下使用，CI 仍會檢查。
