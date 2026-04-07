# QNAP Agentic Playwright 測試專案 — 技術全覽

> 匯出日期：2026-04-07
> 來源：agentic-playwright-tests 專案分析

---

## 專案概覽

- **框架**：Playwright + TypeScript
- **模式**：Page Object Model (POM)
- **目標**：QNAP NAS 應用程式 E2E 自動化測試
- **核心特色**：高度 Agentic 的 AI 驅動測試自動化系統

---

## Agentic 技術架構全覽

```
┌─────────────────────────────────────────────────────────────┐
│                    🧠 AI Orchestration Layer                 │
│                                                             │
│  CLAUDE.md / copilot-instructions.md（全局行為指令）          │
│  ralph-setup-prompt.md（探索精靈）                           │
│  code-audit-setup-prompt.md（審計精靈）                      │
├─────────────────────────────────────────────────────────────┤
│                    🔌 MCP Layer（感知 + 動作）                │
│                                                             │
│  playwright-test ×5（瀏覽器操控）                            │
│  QNAP_DQV_MCP（JIRA 操作）                                 │
├─────────────────────────────────────────────────────────────┤
│                    🎭 Agent Layer（5 個專屬 Agent）           │
│                                                             │
│  playwright-test-generator / healer / planner               │
│  hdp-locale-verifier / project-greeter                      │
├─────────────────────────────────────────────────────────────┤
│                    📚 Skill Layer（51 個 SKILL.md）           │
│                                                             │
│  qpkg/（16 App）  fw/（5）  tools/（20）  security/（1）     │
│  universal/（1）  sf-case-reply/（1）                        │
├─────────────────────────────────────────────────────────────┤
│                    ⚡ Hook Layer（6 個自動觸發）              │
│                                                             │
│  PreToolUse: protect-files / safe-bash                      │
│  PostToolUse: auto-format / auto-test / skill-structure     │
│  UserPromptSubmit: skill-suggest                            │
├─────────────────────────────────────────────────────────────┤
│                    🎯 Command Layer（9 個 Slash 指令）        │
│                                                             │
│  /commit /generate-test /heal-test /plan-test /setup ...    │
├─────────────────────────────────────────────────────────────┤
│                    🏗️ CI/CD Layer                            │
│                                                             │
│  Jenkinsfile / Jenkinsfile.main / Jenkinsfile.elfscan       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Ralph Loop（核心 Agentic 迴圈）

專案最具代表性的 agentic 技術。AI **自主迭代探索**未知 App：

```
Phase 1: 人機問答 → 生成 explore-prompt.md + SKILL.md + STATUS.md
             │
Phase 2: Ralph Loop 自動迴圈（無人值守）
             │
    Phase A → 開瀏覽器，導航到 App
    Phase B → 用 browser_snapshot 觀察 UI
    Phase C → 記錄 selector、workflow、驗證點
    Phase D → 更新 SKILL.md → 自動回到 Phase A
             │
    反覆迭代直到 L7 收斂（知識完備）
```

> **這是「AI 自己去用 App、自己寫文件」的流程。**

---

## 2. MCP（Model Context Protocol）

MCP 是 AI 的「眼睛和手」，讓 AI 能即時操控瀏覽器和外部服務。

### 使用中的 MCP Server

| MCP Server | 用途 | 實例數 |
|------------|------|:------:|
| **playwright-test** | 瀏覽器自動化（深度探索核心） | ×5 |
| **QNAP_DQV_MCP** | JIRA transition、NAS 操作 | ×1 |
| **test-echo** | 測試用 echo server | ×1 |

### playwright-test MCP 提供的能力

| 工具 | 功能 |
|------|------|
| `browser_navigate` | 開啟 NAS 網頁 |
| `browser_click` | 點擊 UI 元素 |
| `browser_snapshot` | 截取 accessibility tree（AI 的視覺） |
| `browser_run_code` | 執行 JavaScript 操作 |
| `browser_press_key` | 鍵盤操作 |
| `browser_hover` | 滑鼠懸停 |
| `browser_close` | 結束瀏覽器 |

### MCP vs SKILL 的關係

```
MCP  ──產出──→  SKILL  ──指導──→  測試開發
 ↑                                    │
 └──────── 過時時需要重新 ←────────────┘
```

> **SKILL 是 MCP 的快取（cache）**— 命中時不需要 MCP，但 cache 過期時必須回源。

### MCP 停掉的影響

| 功能 | 影響 |
|------|------|
| 🔴 Ralph Loop 深度探索 | **完全癱瘓** |
| 🔴 explore-prompt 自動探索 | **完全癱瘓** |
| 🔴 playwright-test-healer | 無法自動修復 |
| 🟡 DQV JIRA transition | 可用 jira-cli.ts 替代 |
| 🟢 跑測試 (npx tsx main.ts) | **不受影響** |
| 🟢 寫程式碼 / 讀檔案 | **不受影響** |

---

## 3. Hooks（自動護欄系統）

6 個 Hook 腳本，在 AI 操作的不同時機自動觸發：

| Hook | 觸發時機 | 功能 |
|------|---------|------|
| `protect-files.sh` | 編輯前 (PreToolUse) | 阻止修改敏感檔案 |
| `safe-bash.sh` | 執行指令前 (PreToolUse) | 攔截危險命令（rm -rf 等） |
| `auto-format.sh` | 編輯後 (PostToolUse) | 自動格式化程式碼 |
| `auto-test.sh` | 編輯後 (PostToolUse) | 改 spec 自動跑測試 |
| `skill-structure-guard.sh` | 編輯後 (PostToolUse) | 確保 SKILL 遵守三層結構 |
| `skill-suggest.sh` | 用戶輸入時 (UserPromptSubmit) | 根據提示詞推薦適用 Skill |

---

## 4. Agents（5 個專屬 AI 角色）

| Agent | 職責 |
|-------|------|
| `playwright-test-planner` | 分析 App UI → 產出測試計畫 |
| `playwright-test-generator` | 依計畫 → 生成 spec.ts |
| `playwright-test-healer` | 測試失敗 → 自動診斷修復 |
| `hdp-locale-verifier` | 多語系自動切換驗證（21 語言） |
| `project-greeter` | 新對話開場引導 |

---

## 5. Skills 知識庫（51 個 SKILL.md）

Skills 是 AI 的**長期記憶**，記錄每個 App 的 UI 結構、selector、workflow、驗證點。

### 分類統計

| 類別 | 數量 | 路徑 | 範例 |
|------|:----:|------|------|
| QPKG App | 16 | `.claude/skills/qpkg/` | QuMagie、HDP、McAfee、MMC、AppLab、ADRA... |
| Firmware/系統 | 5 | `.claude/skills/fw/` | QTS、MEGA、ACL |
| 工具鏈 | 20 | `.claude/skills/tools/` | JIRA、Jenkins、Playwright、ELFScan、OSS... |
| 安全 | 1 | `.claude/skills/security-bug/` | 資安漏洞迴歸測試 |
| 通用 | 1 | `.claude/skills/universal/` | 通用 App UI 測試規格 |
| 客訴 | 1 | `.claude/skills/sf-case-reply/` | Salesforce 客訴快速回覆 |

### 完整 SKILL 清單

#### QPKG App（16 個）

| Skill | 說明 |
|-------|------|
| qumagie-testing | QuMagie 照片管理 |
| hdp-testing | HDP 虛擬機備份 |
| hdp-business-testing | HDP Business 測試 |
| adra-ndr-testing | ADRA NDR 網路安全 |
| adra-sa-testing | ADRA SA 測試 |
| hbs3-testing | HBS 3 混合備份同步 |
| boxafe | HDP for SaaS 雲端備份 |
| virtualization-station-testing | Virtualization Station 虛擬化平台 |
| qmcp-testing | QMCP MCP Assistant |
| multimedia-console-testing | Multimedia Console |
| mcafee-testing | McAfee Antivirus 防毒 |
| applab-testing | APPLAB 相容性測試 |
| hdstation-testing | HD Station |
| qaueshop-testing | QNAP AU eShop 電商 |
| ai-core-docker-validation | AI Core Docker Image 驗證 |
| software-store-testing | Software Store 測試 |

#### 工具鏈（20 個）

| Skill | 說明 |
|-------|------|
| jira-integration | JIRA API 整合 |
| jenkins-integration | Jenkins CI/CD 整合 |
| playwright-test | Playwright 測試流程指南 |
| qpkg-installation | QPKG 安裝管理 |
| deep-exploration | 深度探索流程（Ralph Loop） |
| elfscan-automation | ELFScan 弱掃分類自動化 |
| elfscan | ELFScan 基礎工具 |
| oss-vulnerability-scanning | OSS 弱點掃描開單 |
| test-report-upload | 測試報告上傳與數據庫 |
| xml-jira-validator | XML JIRA 單驗證 |
| qpkg-xml-comparison | QPKG XML 差異比對 |
| xml-pipeline | XML 送測自動化整合 |
| opencv-image-matching | OpenCV 圖像識別（VNC 自動化） |
| testlink-integration | TestLink API 整合 |
| playground-development | 架構 Playground 開發 |
| code-depth-audit | 測試深度審計 |
| auto-repair-loop | 整夜自動修復迴圈 |
| exploration-audit | 探索品質稽核 |
| qsync-client-testing | QSync Client 測試 |
| code-review | 程式碼審查 |

---

## 6. Slash Commands（9 個快捷工作流）

| 指令 | 功能 |
|------|------|
| `/generate-test` | 讀 .plan.md → 自動產生測試 |
| `/heal-test` | 分析失敗 → 自動修復 |
| `/plan-test` | 建立測試計畫 |
| `/commit` | git add + commit + push |
| `/setup` | 初始化新 App 測試環境 |
| `/report` | 檢視測試報告 |
| `/import-data` | 匯入測試資料 |
| `/test-env` | 檢查環境 |
| `/skill` | 查看/探索 Skills |

---

## 7. 資安自動化三大模組

| 模組 | Skill | 功能 |
|------|-------|------|
| **ELFScan 自動化** | elfscan-automation v1.4 | NAS 掃描 → CSV 上傳 DB → 新舊比對 → 自動開/關 JIRA Bug → 三問表格留言 → whitelist 分類（19 個腳本） |
| **OSS 弱掃開單** | oss-vulnerability-scanning | Dependency-Track CVSS ≥ 7.0 → 批量建 JIRA Task + Bug |
| **資安迴歸測試** | security-test-development | JIRA 資安單 → 安裝 QPKG → 執行 PoC → 驗證漏洞是否已修 |

---

## 8. APPLAB 相容性測試

APPLAB 測試的核心任務：**安裝一個 QPKG 到 NAS 上，驗證不會搞壞其他 App**。

```
步驟 1: 從 JIRA 取得 QPKG 的 Build Path
步驟 2: 下載 QPKG 檔案
步驟 3: PRETEST — 記錄所有 App 的開啟狀態（基準線）
步驟 4: 安裝受測 QPKG
步驟 5: TEST — 再開一次所有 App
步驟 6: 比對 PRETEST vs TEST → 有沒有 App 壞掉
```

- Skill 版本：v2.1.0（含 Phase 2.5 Webhook 自動觸發）
- CLI 工具：`run-test.ts`、`create-task.ts`、`webhook-trigger.ts`、`jira-comment.ts`、`upload-result.ts`
- 整合鏈：JIRA → Jenkins → Webhook → 自動跑測試 → DB 上傳 → JIRA 留言

---

## 9. CI/CD 整合

| 檔案 | 用途 |
|------|------|
| `Jenkinsfile` | 主測試 Pipeline |
| `Jenkinsfile.main` | main.ts 統一入口 Pipeline |
| `Jenkinsfile.elfscan` | ELFScan 弱掃 Pipeline |

---

## 10. Copilot CLI vs Claude Code 差異

| 能力 | Claude Code | Copilot CLI |
|------|:-----------:|:-----------:|
| MCP playwright-test（瀏覽器操控） | ✅ | ❌ |
| MCP QNAP_DQV_MCP（JIRA transition） | ✅ | ❌ |
| Ralph Loop 深度探索 | ✅ | ❌ |
| GitHub MCP Server（GitHub API） | ❌ | ✅ |
| 讀寫檔案、執行指令 | ✅ | ✅ |
| JIRA 查詢（jira-cli.ts） | ✅ | ✅ |
| 開發/修改測試程式碼 | ✅ | ✅ |

---

## 一句話總結

> 這個專案把 **Claude Code 打造成一個「有眼睛（MCP）、有記憶（SKILL）、有護欄（Hooks）、有專長（Agents）、能自我迭代（Ralph Loop）」的自主測試工程師**，而不只是一個程式碼生成器。
