# Skill: Pre-commit 本地品質檢查

> 本專案使用 pre-commit 在 `git commit` 時自動執行程式碼品質檢查。

---

## 架構總覽

```
.pre-commit-config.yaml
├── 1. 基本檔案衛生 (pre-commit-hooks v5.0.0)
│   ├── trailing-whitespace    — 移除行尾空白（排除 Sources/）
│   ├── end-of-file-fixer      — 確保檔案末尾有換行（排除 Sources/）
│   ├── check-yaml             — 驗證 YAML 語法
│   ├── check-json             — 驗證 JSON 語法
│   └── check-added-large-files — 阻擋 >1000KB 的大檔案
│
├── 2. Ruff 程式碼品質 (ruff-pre-commit v0.9.10)
│   ├── ruff check (--fix)     — Lint 檢查 + 自動修復
│   └── ruff format            — 程式碼格式化
│
└── 3. 機密偵測 (detect-secrets v1.5.0)
    └── detect-secrets         — 偵測意外提交的密鑰
        排除：Sources/, datasets/, chunks/, logs/
```

## Ruff 設定（pyproject.toml）

```toml
[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "S"]  # pycodestyle + pyflakes + isort + pyupgrade + bandit
ignore = ["E501", "S101", "S603", "S607"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 規則說明

| 規則 | 說明 | 範圍 |
|------|------|------|
| E | pycodestyle 錯誤 | 全域 |
| F | pyflakes 邏輯錯誤 | 全域 |
| W | pycodestyle 警告 | 全域 |
| I | isort import 排序 | 全域 |
| UP | pyupgrade 語法升級 | 全域 |
| S | flake8-bandit 安全檢查 | 全域（evaluate/ 放寬） |

### 排除目錄

`Sources`, `chunks`, `datasets`, `logs`, `building_note`, `testing`, `evaluation_reports`, `.git`, `__pycache__`

## 常用指令

```bash
# 安裝 pre-commit hooks
pre-commit install

# 手動對所有檔案執行
pre-commit run --all-files

# 只執行 ruff
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files

# 只執行機密偵測
pre-commit run detect-secrets --all-files

# 更新 hooks 版本
pre-commit autoupdate

# 跳過 pre-commit（緊急時）
git commit --no-verify -m "emergency fix"
```

## 常見問題與修復

### 1. Ruff lint 失敗

```bash
# 查看具體錯誤
ruff check . --show-source

# 自動修復
ruff check . --fix

# 如果是 import 排序問題
ruff check . --select I --fix
```

### 2. Ruff format 失敗

```bash
# 查看差異
ruff format --diff .

# 自動格式化
ruff format .
```

### 3. detect-secrets 失敗

```bash
# 查看偵測到的機密
detect-secrets scan

# 如果是誤報，更新 baseline
detect-secrets scan --baseline .secrets.baseline
# 審核後提交更新的 .secrets.baseline
```

### 4. 大檔案被擋

```
# 檢查哪些檔案超過 1MB
find . -size +1M -not -path './.git/*'

# 應加入 .gitignore 或 Git LFS
```

## 修改 Python 檔案後的檢查清單

當你修改了 Python 檔案，提交前請確認：

1. ✅ `ruff check <file>` 無錯誤
2. ✅ `ruff format --check <file>` 格式正確
3. ✅ 沒有硬編碼的 API key / token / password
4. ✅ import 順序正確（stdlib → third-party → local）
5. ✅ 使用 `"double quotes"` 風格
