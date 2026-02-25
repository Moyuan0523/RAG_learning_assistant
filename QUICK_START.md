# 🚀 快速啟動指南

## 問題已解決！✅

你的系統已經修復並升級，現在支持：
- ✅ RAG 聊天系統（使用遠端 Ollama）
- ✅ LLM-as-a-Judge 數據集生成
- ✅ 統一啟動菜單
- ✅ 完整的測試工具

---

## 三種啟動方式

### 方式 1：統一菜單（推薦）⭐

```bash
./start.sh
```

選擇你需要的功能：
- **選項 1**：🌐 啟動 RAG 聊天系統
- **選項 2-3**：🔌 測試遠端連接
- **選項 4-9**：📊 生成測試數據集

### 方式 2：直接啟動 RAG

```bash
./start_rag.sh
```
或
```bash
python app.py
```

然後打開瀏覽器訪問：http://localhost:5000

### 方式 3：直接生成數據集

```bash
# 列出可用來源
python generate_golden_dataset.py --list-sources

# 生成 QA 數據集
python generate_golden_dataset.py --source weaviate --count 50
```

---

## 系統驗證

運行完整檢查（推薦首次使用前執行）：

```bash
./testing/system_check.sh
```

預期輸出：
```
✅ 通過: 20
❌ 失敗: 0
🎉 所有測試通過！
```

---

## 配置說明

### 當前配置（`.env`）

```bash
# RAG 聊天系統
USE_LOCAL_LLM=true                              # 使用遠端 Ollama
LOCAL_LLM_BASE_URL=http://140.116.96.66:11434  # Ollama 地址
LOCAL_LLM_MODEL=llama3.2:3b                     # 聊天模型

# LLM-as-a-Judge
OLLAMA_BASE_URL=http://140.116.96.66:11434     # 同上
GENERATOR_MODEL=qwen2.5:7b-instruct-q4_K_M     # 生成器
EVALUATOR_MODEL=llama3.2:3b                     # 評估器

# Weaviate 向量資料庫
SERVER_IP=140.116.96.67                         # Weaviate 服務器
```

### 模型分工

| 用途 | 模型 | 特點 |
|------|------|------|
| RAG 聊天 | Llama 3.2 (3B) | 快速響應 |
| QA 生成 | Qwen 2.5 (7B) | 高質量生成 |
| QA 評估 | Llama 3.2 (3B) | 嚴格驗證 |

---

## 常用命令

### 測試連接

```bash
# 測試 Ollama
python testing/test_remote_ollama.py

# 測試 Weaviate
./testing/test_weaviate.sh

# 完整系統檢查
./testing/system_check.sh
```

### RAG 系統

```bash
# 啟動 Web 界面
python app.py

# 快速啟動（帶提示）
./start_rag.sh
```

### 數據集生成

```bash
# 快速測試（5 組）
python generate_golden_dataset.py \
  --source weaviate \
  --count 5 \
  --output test.json

# 標準批量（50 組）
python generate_golden_dataset.py \
  --source weaviate \
  --count 50 \
  --output golden_dataset.json

# 特定來源
python generate_golden_dataset.py \
  --source "Data_Mining__The_Textbook_Aggarwal_2015-04-14" \
  --count 30
```

---

## 故障排除

### 問題：無法啟動 app.py

✅ **已解決**！現在使用遠端 Ollama，無需 OpenAI API key

驗證：
```bash
python -c "from app.generator_local import client; print('OK')"
```

### 問題：連接失敗

檢查網絡連接：
```bash
# 測試 Ollama
curl http://140.116.96.66:11434/api/version

# 測試 Weaviate
curl http://140.116.96.67:8080/v1/.well-known/ready
```

### 問題：模型未找到

列出可用模型：
```bash
curl http://140.116.96.66:11434/api/tags
```

---

## 文件說明

### 主要腳本

- `start.sh` - 統一啟動菜單 ⭐
- `start_rag.sh` - RAG 系統快速啟動
- `app.py` - RAG Web 應用
- `generate_golden_dataset.py` - 數據集生成工具

### 測試工具（`testing/`）

- `system_check.sh` - 完整系統驗證
- `test_remote_ollama.py` - Ollama 連接測試
- `test_weaviate.sh` - Weaviate 連接測試

### 文檔（`building_note/`）

- `SYSTEM_FIX.md` - 詳細修復說明
- `WEAVIATE_INTEGRATION.md` - Weaviate 使用指南
- `LLM_AS_JUDGE.md` - LLM-as-a-Judge 技術文檔

---

## 下一步

### 1. 啟動 RAG 聊天系統

```bash
./start_rag.sh
```

打開瀏覽器：http://localhost:5000

### 2. 生成測試數據集

```bash
./start.sh  # 選擇選項 5
```

### 3. 探索更多功能

查看統一菜單的所有選項：
```bash
./start.sh
```

---

## 技術支持

- 完整文檔：[README.md](README.md)
- 修復說明：[SYSTEM_FIX.md](SYSTEM_FIX.md)
- Weaviate 整合：[WEAVIATE_INTEGRATION.md](WEAVIATE_INTEGRATION.md)

---

**系統已就緒！開始使用吧！** 🎉
