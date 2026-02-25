"""
Weaviate Loader for LLM-as-a-Judge
從遠端 Weaviate 資料庫載入所有 chunks 用於生成 Golden Dataset
"""

from app.retriever import connect_weaviate
from typing import List, Dict, Optional


def load_all_chunks_from_weaviate(
    source_filter: Optional[str] = None,
    limit: int = 10000
) -> List[Dict[str, str]]:
    """
    從 Weaviate 載入所有 chunks
    
    Args:
        source_filter: 僅載入特定來源的 chunks（None = 全部）
        limit: 最多載入多少個 chunks
        
    Returns:
        List of chunks，每個包含 {"text": "...", "source": "..."}
    """
    print(f"🔌 連接到 Weaviate...")
    weaviate_client = connect_weaviate()
    
    print(f"📥 載入 chunks from Weaviate...")
    
    # 構建查詢
    query_obj = weaviate_client.query.get("Paragraph", ["text", "source"]) \
        .with_limit(limit)
    
    # 如果指定來源，加入過濾條件
    if source_filter:
        print(f"   篩選來源: {source_filter}")
        query_obj = query_obj.with_where({
            "path": ["source"],
            "operator": "Equal",
            "valueText": source_filter
        })
    
    # 執行查詢
    try:
        results = query_obj.do()
        
        if "data" not in results or "Get" not in results["data"]:
            print("⚠️  Weaviate 中沒有找到任何 chunks")
            return []
        
        chunks = [
            {
                "text": item["text"],
                "source": item.get("source", "Unknown")
            }
            for item in results["data"]["Get"]["Paragraph"]
        ]
        
        print(f"✓ 成功載入 {len(chunks)} 個 chunks")
        
        # 顯示來源統計
        sources = {}
        for chunk in chunks:
            source = chunk["source"]
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n📊 來源統計:")
        for source, count in sources.items():
            print(f"   {source}: {count} chunks")
        print()
        
        return chunks
        
    except Exception as e:
        print(f"❌ 從 Weaviate 載入失敗: {e}")
        return []


def get_available_sources() -> List[str]:
    """
    獲取 Weaviate 中所有可用的文檔來源
    
    Returns:
        來源列表
    """
    print("🔌 連接到 Weaviate...")
    weaviate_client = connect_weaviate()
    
    try:
        # 使用 aggregate 查詢獲取所有 source
        result = weaviate_client.query.aggregate("Paragraph") \
            .with_group_by_filter(["source"]) \
            .with_fields("groupedBy { value }") \
            .do()
        
        if "data" not in result or "Aggregate" not in result["data"]:
            print("⚠️  無法獲取來源列表")
            return []
        
        sources = [
            group["groupedBy"]["value"]
            for group in result["data"]["Aggregate"]["Paragraph"]
        ]
        
        print(f"✓ 找到 {len(sources)} 個來源")
        for source in sources:
            print(f"   - {source}")
        print()
        
        return sources
        
    except Exception as e:
        print(f"⚠️  獲取來源列表失敗: {e}")
        # 備用方案：掃描所有 chunks
        print("   使用備用方案掃描...")
        chunks = load_all_chunks_from_weaviate(limit=10000)
        sources = list(set(chunk["source"] for chunk in chunks))
        return sources


if __name__ == "__main__":
    # 測試程式碼
    print("="*60)
    print("測試 Weaviate Loader")
    print("="*60)
    print()
    
    # 測試 1: 列出所有來源
    print("1️⃣  列出所有可用來源:")
    print("-"*60)
    sources = get_available_sources()
    
    # 測試 2: 載入所有 chunks
    print("\n2️⃣  載入所有 chunks（限制 10 個）:")
    print("-"*60)
    chunks = load_all_chunks_from_weaviate(limit=10)
    
    if chunks:
        print(f"\n第一個 chunk 預覽:")
        print(f"來源: {chunks[0]['source']}")
        print(f"內容: {chunks[0]['text'][:200]}...")
    
    # 測試 3: 載入特定來源
    if sources:
        print(f"\n3️⃣  載入特定來源的 chunks (來源: {sources[0]}, 限制 5 個):")
        print("-"*60)
        filtered_chunks = load_all_chunks_from_weaviate(
            source_filter=sources[0],
            limit=5
        )
        print(f"✓ 載入了 {len(filtered_chunks)} 個 chunks")
    
    print("\n" + "="*60)
    print("測試完成！")
    print("="*60)
