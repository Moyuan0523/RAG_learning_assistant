#!/bin/bash

# RAG 學習助手 - 統一啟動菜單
# 整合 RAG 聊天系統 + LLM-as-a-Judge 數據集生成

echo "========================================"
echo "🎓 RAG 學習助手統一啟動"
echo "========================================"
echo ""
echo "📋 遠端服務器配置:"
echo "  Ollama: 140.116.96.66:11434"
echo "  Weaviate: 140.116.96.67:8080"
echo ""
echo "🤖 可用模型:"
echo "  - Llama 3.2 (3B) - RAG 聊天"
echo "  - Qwen 2.5 (7B) - QA 生成"
echo ""
echo "────────────────────────────────────────"
echo ""

PS3="請選擇功能 (輸入數字): "
options=(
    "🌐 啟動 RAG 聊天系統（Web 界面）"
    "🔌 測試遠端 Ollama 連接"
    "🔌 測試遠端 Weaviate 連接"
    "📋 列出 Weaviate 中的來源"
    "🧪 從 Weaviate 生成 5 組測試 QA（快速）"
    "📊 從 Weaviate 生成 50 組 Golden Dataset"
    "🎯 從 Weaviate 特定來源生成 QA"
    "📁 從本地 pickle 生成 QA（舊方式）"
    "🚀 背景執行生成 200 組（Weaviate）"
    "� 用 Golden Dataset 評估 RAG 系統"
    "�📜 查看最新生成日誌"
    "❌ 離開"
)

select opt in "${options[@]}"
do
    case $opt in
        "🌐 啟動 RAG 聊天系統（Web 界面）")
            echo ""
            echo "🚀 啟動 RAG 聊天系統..."
            echo ""
            echo "📝 提示："
            echo "  1. 服務器啟動後，打開瀏覽器訪問: http://localhost:5000"
            echo "  2. 按 Ctrl+C 停止服務器"
            echo ""
            echo "========================================"
            python app.py
            break
            ;;
        "🔌 測試遠端 Ollama 連接")
            echo ""
            echo "🔌 測試遠端 Ollama 連接..."
            python testing/test_remote_ollama.py
            echo ""
            break
            ;;
        "🔌 測試遠端 Weaviate 連接")
            echo ""
            echo "🔌 測試遠端 Weaviate 連接..."
            ./testing/test_weaviate.sh
            echo ""
            break
            ;;
        "📋 列出 Weaviate 中的來源")
            echo ""
            echo "📋 列出 Weaviate 中的來源..."
            python evaluate/generate_golden_dataset.py --list-sources
            echo ""
            break
            ;;
        "🧪 從 Weaviate 生成 5 組測試 QA（快速）")
            echo ""
            echo "🧪 從 Weaviate 生成 5 組測試 QA..."
            mkdir -p datasets
            python evaluate/generate_golden_dataset.py \
                --source weaviate \
                --output datasets/test_weaviate_5_qa.json \
                --count 5
            echo ""
            echo "✓ 完成！查看結果:"
            echo "  cat datasets/test_weaviate_5_qa.json | grep -o '\"question\"' | wc -l"
            echo ""
            break
            ;;
        "📊 從 Weaviate 生成 50 組 Golden Dataset")
            echo ""
            echo "📊 從 Weaviate 生成 50 組 Golden Dataset..."
            mkdir -p datasets
            python evaluate/generate_golden_dataset.py \
                --source weaviate \
                --output datasets/golden_weaviate_50_qa.json \
                --count 50
            echo ""
            echo "✓ 完成！"
            echo ""
            break
            ;;
        "🎯 從 Weaviate 特定來源生成 QA")
            echo ""
            echo "📋 可用來源："
            python evaluate/generate_golden_dataset.py --list-sources
            echo ""
            read -p "請輸入來源名稱: " source_name
            read -p "要生成幾組 QA？(預設 30): " count
            count=${count:-30}
            echo ""
            echo "📊 從來源 '$source_name' 生成 $count 組 QA..."
            mkdir -p datasets
            python evaluate/generate_golden_dataset.py \
                --source "$source_name" \
                --output "datasets/golden_${source_name}_${count}_qa.json" \
                --count "$count"
            echo ""
            break
            ;;
        "📁 從本地 pickle 生成 QA（舊方式）")
            echo ""
            echo "📂 從本地 pickle 生成 QA..."
            if [ -f "chunks/data_mining.pkl" ]; then
                read -p "要生成幾組 QA？(預設 10): " count
                count=${count:-10}
                mkdir -p datasets
                python evaluate/generate_golden_dataset.py \
                    --input chunks/data_mining.pkl \
                    --output datasets/golden_pickle_${count}_qa.json \
                    --count "$count"
            else
                echo "❌ 找不到 chunks/data_mining.pkl"
                echo "請使用 Weaviate 方式（推薦）"
            fi
            echo ""
            break
            ;;
        "🚀 背景執行生成 200 組（Weaviate）")
            echo ""
            echo "🚀 背景執行從 Weaviate 生成 200 組 QA..."
            echo "⚠️  預計需要 1-2 小時"
            read -p "是否繼續？(y/n) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                mkdir -p datasets logs
                timestamp=$(date +%Y%m%d_%H%M%S)
                nohup python evaluate/generate_golden_dataset.py \
                    --source weaviate \
                    --output datasets/golden_weaviate_200_qa_${timestamp}.json \
                    --count 200 \
                    > logs/generation_weaviate_${timestamp}.log 2>&1 &
                
                echo ""
                echo "✓ 已在背景啟動！"
                echo ""
                echo "查看進度:"
                echo "  tail -f logs/generation_weaviate_${timestamp}.log"
                echo ""
                echo "查看所有背景任務:"
                echo "  jobs"
            fi
            echo ""
            break
            ;;
        "� 用 Golden Dataset 評估 RAG 系統")
            echo ""
            echo "📈 RAG 系統性能評估"
            echo ""
            
            # 檢查是否有 Golden Dataset
            if [ -d "datasets" ] && [ "$(ls -A datasets/*.json 2>/dev/null | grep -v '\.jsonl$')" ]; then
                echo "📂 可用的 Golden Datasets："
                echo ""
                
                # 列出所有 .json 文件（排除 .jsonl）並編號
                json_files=(datasets/*.json)
                i=1
                for file in "${json_files[@]}"; do
                    # 跳過不存在的文件
                    [ -f "$file" ] || continue
                    size=$(ls -lh "$file" | awk '{print $5}')
                    echo "  [$i] $file ($size)"
                    ((i++))
                done
                
                echo ""
                echo "請選擇："
                read -p "  輸入編號 [1-$((i-1))] 或完整路徑: " dataset_choice
                
                # 判斷用戶輸入的是編號還是路徑
                if [[ "$dataset_choice" =~ ^[0-9]+$ ]] && [ "$dataset_choice" -ge 1 ] && [ "$dataset_choice" -lt "$i" ]; then
                    # 用戶輸入編號
                    dataset_path="${json_files[$((dataset_choice-1))]}"
                else
                    # 用戶輸入路徑
                    dataset_path="$dataset_choice"
                fi
                
                # 驗證文件是否存在
                if [ ! -f "$dataset_path" ]; then
                    echo ""
                    echo "❌ 錯誤：找不到文件 '$dataset_path'"
                    echo ""
                    break
                fi
                
                echo ""
                echo "✓ 已選擇：$dataset_path"
                read -p "限制測試數量？(留空=全部測試): " limit
                
                echo ""
                echo "🚀 開始評估..."
                mkdir -p evaluation_reports
                
                if [ -z "$limit" ]; then
                    python evaluate/evaluate_rag.py \
                        --golden-dataset "$dataset_path" \
                        --output-report evaluation_reports/report_$(date +%Y%m%d_%H%M%S).txt \
                        --output-json evaluation_reports/results_$(date +%Y%m%d_%H%M%S).json
                else
                    python evaluate/evaluate_rag.py \
                        --golden-dataset "$dataset_path" \
                        --limit "$limit" \
                        --output-report evaluation_reports/report_$(date +%Y%m%d_%H%M%S).txt \
                        --output-json evaluation_reports/results_$(date +%Y%m%d_%H%M%S).json
                fi
            else
                echo "❌ 找不到 Golden Dataset"
                echo ""
                echo "請先生成 Golden Dataset："
                echo "  選擇選項 5 或 6 來生成"
            fi
            echo ""
            break
            ;;
        "�📜 查看最新生成日誌")
            echo ""
            if [ -d "logs" ] && [ "$(ls -A logs/generation_*.log 2>/dev/null)" ]; then
                latest_log=$(ls -t logs/generation_*.log | head -1)
                echo "📋 最新日誌: $latest_log"
                echo ""
                tail -30 "$latest_log"
            else
                echo "⚠️  找不到生成日誌"
            fi
            echo ""
            break
            ;;
        "❌ 離開")
            echo ""
            echo "👋 再見！"
            echo ""
            break
            ;;
        *) 
            echo "❌ 無效選項 $REPLY"
            ;;
    esac
done
