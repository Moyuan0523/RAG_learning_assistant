# RAG_learning_assistant
RAG Learning Assistant is a Retrieval-Augmented Generation (RAG) based system that integrates the Weaviate vector database and **OpenAI API or Local LLM (Llama 3.2)** through a Flask web application, enabling document-based knowledge retrieval and natural language question answering from user-uploaded documents.
![Architecture](templates/architecture1.png)

## ✨ New: Local LLM Support
Now supports deploying **Llama 3.2** locally on your own server! No need to rely on OpenAI API anymore.
Choose between:
- **OpenAI API** (GPT-3.5/GPT-4) - Easy to use, high quality
- **Local Llama 3.2** (1B/3B) - Privacy-focused, cost-effective, full control

📚 **Quick Start Guides:**
- [🚀 5-Minute Quick Start](QUICKSTART.md) - Get Llama 3.2 running fast
- [📖 Complete Deployment Guide](LLAMA_DEPLOYMENT.md) - Detailed instructions for all deployment options

## Features
1. **Custom Sources**
Users can upload their own materials in PDF format.The system will automatically segment, vectorize, and index the content into the knowledge base for downstream question answering.
2. **Intelligent Chat with Memory**
The system features a conversaction memory mechanism. AI considers previous questions and answers to provide more coherent and context-aware responses.
3. **Answering Questions on Trusted Sources**
AI responses are primarily generated from the content of user-uploaded documents.
Each answer includes clearly marked citations to improve verifiability and trustworthiness.
4. **Source Selection and Control**
Users can choose specific sources from uploaded materials to be used for answering, helping to avoid interference from irrelevant documents.
5. **Flexible LLM Backend** 🆕
Switch between OpenAI API and self-hosted Llama 3.2 with a simple configuration change.

Instead of generating answers purely from a language model, this project uses a Retrieval-Augmented Generation (RAG) approach to improve control and transparency.
Users can trace the source of each response, reducing hallucination and ensuring relevance to the uploaded content.

## installing
```bash
# Clone the repository
git clone https://github.com/Moyuan0523/RAG_learning_assistant

# Navigate into the directory
cd RAG-learning_assistant

# Install dependencies
conda env create -f environment.yml
```

## Runnung the Application
### Step 1. set up the enviornment
Create a `.env` file in `app/`，and add the text of following：
```
OPENAI_API_KEY = Your_API_key
SERVER_IP = Your_Server_Address:Database_Port
```
### Step 2. Start the weaviate vector database (via Docker)
Set up Weaviate v3 on your remote server using Docker
### Step 3. Run the Flask web application
```bash
python app.py
```
then Access the interface
- http://127.0.0.1:5000
### Step 4. Upload your document
Click **Upload** on the wed interface to upload PDFs. The system wil automatically chunk, index and mark their source into Weaviate.
### Step 5. Select sources
Select single or multiple source for answering on web interface (Default using all source when selecting nothing.)
### Step 6. Ask questions
Asking questions in the chat, AI retrieves and answers based on selected sources.
Click "Expand Reference" to view the supporting content and assess answer accuracy.

---

## 🛠️ CI/CD & Development Guide

This project enforces code quality through a **two-layer** automated pipeline:

1. **Pre-commit hooks** — Local checks that run automatically before every `git commit`
2. **GitHub Actions CI** — Remote checks that run on every `push` to `main` and on pull requests

### 🔧 Tools

| Tool | Role | Description |
|------|------|-------------|
| [**Ruff**](https://docs.astral.sh/ruff/) | Linter & Formatter | All-in-one Python linter + formatter + import sorter. Extremely fast (written in Rust). |
| [**detect-secrets**](https://github.com/Yelp/detect-secrets) | Security | Scans for API keys, passwords, and tokens to prevent accidental credential leaks. |
| [**pre-commit**](https://pre-commit.com/) | Hook Manager | Manages and orchestrates all git pre-commit hooks. |

### 🚀 Setup (for new developers)

```bash
# 1. Install dev tools
pip install pre-commit ruff detect-secrets

# 2. Install git hooks (run once after cloning)
pre-commit install
```

After this, every `git commit` will automatically run all checks. **Non-compliant code will be blocked from committing.**

### ✅ What gets checked

#### Pre-commit Hooks (local, on every commit)

| Hook | Auto-fix | Description |
|------|----------|-------------|
| **Ruff lint** | ✅ | Python linting — pycodestyle (E/W), pyflakes (F), import sorting (I), pyupgrade (UP), security (S) |
| **Ruff format** | ✅ | Consistent code formatting (line-length: 120, double quotes) |
| **detect-secrets** | ❌ | Blocks commits containing potential API keys or secrets |
| **trailing-whitespace** | ✅ | Removes trailing spaces from lines |
| **end-of-file-fixer** | ✅ | Ensures files end with a single newline |
| **check-yaml** | ❌ | Validates YAML file syntax |
| **check-json** | ❌ | Validates JSON file syntax |
| **check-added-large-files** | ❌ | Blocks files larger than 1MB from being committed |

> Hooks marked with ✅ auto-fix will automatically correct your files. If a hook modifies files, the commit is aborted — simply `git add` the fixed files and commit again.

#### GitHub Actions CI (remote, on push & PR)

The workflow (`.github/workflows/lint.yml`) runs the same checks on GitHub's servers:

```yaml
Trigger:  push to main, pull_request to main
Runner:   ubuntu-latest, Python 3.10
Checks:   ruff check → ruff format --check → detect-secrets scan
```

Pull requests will show ✅ or ❌ status based on CI results.

### 📋 Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Ruff configuration (rules, line-length, excluded directories, target Python version) |
| `.pre-commit-config.yaml` | Pre-commit hook definitions and versions |
| `.secrets.baseline` | detect-secrets baseline (known false positives whitelist) |
| `.github/workflows/lint.yml` | GitHub Actions CI workflow |

### 🔨 Manual Commands

```bash
# Run all hooks on all files (same as what runs on commit)
pre-commit run --all-files

# Lint check only
ruff check .

# Auto-fix lint issues
ruff check --fix .

# Format all Python files
ruff format .

# Check formatting without modifying files
ruff format --check .

# Scan for secrets
detect-secrets scan
```

### 💡 Tips

- **IDE Integration**: Install the [Ruff VS Code extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) for real-time linting and format-on-save.
- **Skipping hooks** (emergency only): `git commit --no-verify` — CI will still catch issues on push.
- **Updating hooks**: `pre-commit autoupdate` to update hook versions.

---

## 🆕 LLM-as-a-Judge: Automated QA Dataset Generation

Generate high-quality test datasets for your RAG system using **adversarial dual-LLM architecture**!

### 🎯 What is LLM-as-a-Judge?

A sophisticated system that uses two independent LLMs to generate and validate question-answer pairs:
- **Generator (Qwen 2.5)**: Creates QA pairs from document chunks
- **Evaluator (Llama 3.2)**: Strictly validates quality (PASS/REJECT)
- **Automatic Retry**: Regenerates rejected pairs for maximum quality

### 🚀 Quick Start

```bash
# 1. Test remote Ollama connection
python testing/test_remote_ollama.py

# 2. Generate 50 golden QA pairs
python generate_golden_dataset.py \
    --input chunks/data_mining.pkl \
    --output datasets/golden_qa.json \
    --count 50

# 3. Or use the interactive menu
./start.sh
```

### 📊 Server Configuration

```
Server:      140.116.96.66:11434
Generator:   qwen2.5:7b-instruct-q4_K_M (4.68 GB)
Evaluator:   llama3.2:3b (2.02 GB)
Status:      ✅ All tests passed
```

### 📚 Documentation

- **[Complete Guide](building_note/LLM_AS_JUDGE.md)** - Full documentation
- **[Config Summary](CONFIG_SUMMARY.md)** - Quick reference
- **[Server Alignment](building_note/SERVER_CONFIG_ALIGNMENT.md)** - Configuration details

### 🎁 Benefits

- ✅ **100% Private**: All processing on your server
- ✅ **Zero Cost**: Only electricity (no API fees)
- ✅ **High Quality**: Dual-LLM validation reduces hallucinations
- ✅ **Scalable**: Generate thousands of QA pairs automatically

**Perfect for:**
- Testing different chunking strategies
- Evaluating RAG system performance
- Creating training datasets for fine-tuning
- Benchmarking retrieval algorithms

---
