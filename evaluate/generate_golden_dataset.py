"""
Golden Dataset Generator
從現有的文檔 chunks 生成高品質的 QA 測試集

支持兩種來源：
1. 本地 Pickle 文件: --input chunks/data_mining.pkl
2. 遠端 Weaviate 資料庫: --source weaviate (或指定特定來源)

使用方法：
    # 從本地 pickle 載入
    python generate_golden_dataset.py --input chunks/data_mining.pkl --output golden_dataset.json --count 50
    
    # 從 Weaviate 載入所有 chunks
    python generate_golden_dataset.py --source weaviate --output golden_dataset.json --count 50
    
    # 從 Weaviate 載入特定來源
    python generate_golden_dataset.py --source "data_mining" --output golden_dataset.json --count 50
"""

import pickle
import argparse
from pathlib import Path
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 添加專案根目錄到 Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluate.llm_as_judge import LLMAsJudgePipeline
from app.weaviate_loader import load_all_chunks_from_weaviate, get_available_sources


def load_chunks_from_pickle(pickle_path: str) -> list[str]:
    """
    從 pickle 檔案載入 chunks
    
    Args:
        pickle_path: pickle 檔案路徑
        
    Returns:
        chunks 列表
    """
    print(f"📂 載入 chunks 從: {pickle_path}")
    
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    # 根據不同的 pickle 格式提取 chunks
    if isinstance(data, list):
        # 直接是 chunks 列表
        chunks = [chunk if isinstance(chunk, str) else chunk.page_content for chunk in data]
    elif isinstance(data, dict):
        # 可能是包含 chunks 的字典
        if 'chunks' in data:
            chunks = data['chunks']
        elif 'documents' in data:
            chunks = data['documents']
        else:
            raise ValueError("無法從字典中找到 chunks")
    else:
        raise ValueError(f"不支援的 pickle 格式: {type(data)}")
    
    print(f"✓ 成功載入 {len(chunks)} 個 chunks")
    
    # 顯示第一個 chunk 的預覽
    if chunks:
        preview = chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0]
        print(f"\n第一個 chunk 預覽:")
        print(f"─" * 60)
        print(preview)
        print(f"─" * 60)
    
    return chunks


def load_chunks_from_weaviate(source_filter: str = None) -> list[str]:
    """
    從 Weaviate 資料庫載入 chunks
    
    Args:
        source_filter: 來源過濾器（None = 全部, "weaviate" = 全部, 其他 = 特定來源）
        
    Returns:
        chunks 文本列表
    """
    # 如果 source_filter 是 "weaviate"，則載入全部
    if source_filter == "weaviate":
        source_filter = None
    
    # 從 Weaviate 載入
    chunk_dicts = load_all_chunks_from_weaviate(source_filter=source_filter)
    
    if not chunk_dicts:
        print("⚠️  警告：從 Weaviate 未載入任何 chunks")
        return []
    
    # 提取文本（LLM-as-a-Judge 只需要文本）
    chunks = [chunk["text"] for chunk in chunk_dicts]
    
    # 顯示第一個 chunk 的預覽
    if chunks:
        preview = chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0]
        print(f"\n第一個 chunk 預覽:")
        print(f"─" * 60)
        print(preview)
        print(f"─" * 60)
    
    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="使用 LLM-as-a-Judge 架構生成高品質的 QA 測試集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:
  # 從本地 pickle 檔案生成 50 組 QA 對
  python generate_golden_dataset.py --input chunks/data_mining.pkl --output datasets/golden_qa.json --count 50
  
  # 從遠端 Weaviate 載入所有 chunks
  python generate_golden_dataset.py --source weaviate --output datasets/golden_qa.json --count 50
  
  # 從 Weaviate 載入特定來源的 chunks
  python generate_golden_dataset.py --source "data_mining" --output datasets/golden_qa.json --count 50
  
  # 列出 Weaviate 中可用的來源
  python generate_golden_dataset.py --list-sources
  
  # 使用不同的模型
  python generate_golden_dataset.py --source weaviate --generator qwen2:7b --evaluator llama3:8b --count 50
        """
    )
    
    # 互斥群組：必須選擇 --input 或 --source 或 --list-sources
    input_group = parser.add_mutually_exclusive_group(required=True)
    
    input_group.add_argument(
        '--input', '-i',
        type=str,
        help='輸入的 chunks pickle 檔案路徑'
    )
    
    input_group.add_argument(
        '--source', '-s',
        type=str,
        help='從 Weaviate 載入 chunks（"weaviate" = 全部，或指定特定來源名稱）'
    )
    
    input_group.add_argument(
        '--list-sources',
        action='store_true',
        help='列出 Weaviate 中所有可用的來源並退出'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=f'evaluation_reports/golden_dataset_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        help='輸出的 JSON 檔案路徑（預設: evaluation_reports/golden_dataset_時間戳記.json）'
    )
    
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=None,
        help='想要生成的 QA 對數量（預設: 處理全部 chunks）'
    )
    
    parser.add_argument(
        '--generator', '-g',
        type=str,
        default=os.getenv('GENERATOR_MODEL', 'qwen2.5:7b-instruct-q4_K_M'),
        help='Generator 模型名稱（預設: 從環境變數讀取或 qwen2.5:7b-instruct-q4_K_M）'
    )
    
    parser.add_argument(
        '--evaluator', '-e',
        type=str,
        default=os.getenv('EVALUATOR_MODEL', 'llama3.2:3b'),
        help='Evaluator 模型名稱（預設: 從環境變數讀取或 llama3.2:3b）'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=int(os.getenv('MAX_RETRIES', '2')),
        help='每個 chunk 最大重試次數（預設: 從環境變數讀取或 2）'
    )
    
    parser.add_argument(
        '--base-url',
        type=str,
        default=os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
        help='Ollama API 端點（預設: 從環境變數讀取或 http://localhost:11434）'
    )
    
    args = parser.parse_args()
    
    # 特殊功能：列出 Weaviate 來源
    if args.list_sources:
        print(f"\n{'='*70}")
        print("列出 Weaviate 中可用的來源")
        print(f"{'='*70}\n")
        try:
            sources = get_available_sources()
            if sources:
                print(f"\n✓ 找到 {len(sources)} 個來源")
                print("\n使用範例：")
                print(f"  python generate_golden_dataset.py --source weaviate --count 50")
                print(f"  python generate_golden_dataset.py --source \"{sources[0]}\" --count 50")
            else:
                print("⚠️  Weaviate 中沒有找到任何來源")
        except Exception as e:
            print(f"❌ 獲取來源列表失敗: {e}")
        sys.exit(0)
    
    # 載入 chunks (from pickle or Weaviate)
    try:
        if args.input:
            # 從本地 pickle 載入
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"❌ 錯誤: 找不到輸入檔案 {args.input}")
                sys.exit(1)
            chunks = load_chunks_from_pickle(args.input)
            
        elif args.source:
            # 從 Weaviate 載入
            chunks = load_chunks_from_weaviate(args.source)
        else:
            print("❌ 錯誤: 必須指定 --input 或 --source")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 載入 chunks 失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if not chunks:
        print("❌ 錯誤: chunks 列表為空")
        sys.exit(1)
    
    # 初始化 Pipeline
    print(f"\n{'='*70}")
    print("初始化 LLM-as-a-Judge Pipeline")
    print(f"{'='*70}")
    
    try:
        pipeline = LLMAsJudgePipeline(
            generator_model=args.generator,
            evaluator_model=args.evaluator,
            base_url=args.base_url,
            max_retries=args.max_retries
        )
        
        # 顯示模型配置
        print(f"\n🤖 模型配置:")
        print(f"   Generator:  {args.generator}")
        print(f"   Evaluator:  {args.evaluator}")
        print(f"   Base URL:   {args.base_url}")
        print(f"   Max Retries: {args.max_retries}")
        
    except Exception as e:
        print(f"❌ Pipeline 初始化失敗: {e}")
        print("\n💡 請確認:")
        print("   1. Ollama 服務正在運行")
        print("   2. 模型已下載（執行 'ollama pull <model_name>'）")
        sys.exit(1)
    
    # 確保輸出目錄存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 執行處理
    print(f"\n開始生成 Golden Dataset...")
    print(f"輸出路徑: {args.output}\n")
    
    try:
        results = pipeline.process_chunks(
            chunks=chunks,
            max_qa_pairs=args.count,
            save_to_file=args.output
        )
        
        # 顯示成功訊息
        print(f"\n{'='*70}")
        print("🎉 Golden Dataset 生成完成！")
        print(f"{'='*70}")
        print(f"✓ 成功生成: {len(results['passed'])} 組高品質 QA 對")
        print(f"✓ JSON 檔案: {args.output}")
        print(f"✓ JSONL 檔案: {Path(args.output).with_suffix('.jsonl')}")
        print(f"\n這些 QA 對已通過雙 LLM 對抗驗證，可用於:")
        print("  • RAG 系統的測試集")
        print("  • 模型微調的訓練資料")
        print("  • 評估不同 chunking 策略的效果")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷執行")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 執行過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
