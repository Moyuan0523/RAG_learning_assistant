#!/usr/bin/env python3
"""
重新生成並上傳所有 PDF 的 embeddings 到 Weaviate

⚠️ 使用時機：
- 更換了 embedding 模型後
- 修改了 chunk 分割策略後
- Weaviate 數據庫需要重置時

使用方法：
    python rebuild_embeddings.py
    
    # 或只處理特定 PDF
    python rebuild_embeddings.py --pdf "Data_Mining__The_Textbook_Aggarwal_2015-04-14.pdf"
"""

import warnings
# 隐藏 PyMuPDF 的 DeprecationWarning
warnings.filterwarnings('ignore', category=DeprecationWarning)

import argparse
import sys
from pathlib import Path
from app.gen_chunks_Index_to_weaviate import pdf_to_weaviate, connect_weaviate

def clear_weaviate_data():
    """清空 Weaviate 中的 Paragraph 類別"""
    print("🗑️  清空 Weaviate 中的舊數據...")
    client = connect_weaviate()
    
    try:
        # 刪除 Paragraph schema（會連同數據一起刪除）
        if "Paragraph" in [c['class'] for c in client.schema.get()["classes"]]:
            client.schema.delete_class("Paragraph")
            print("✓ 已清空舊數據")
        else:
            print("✓ 無需清空（沒有舊數據）")
    except Exception as e:
        print(f"⚠️  清空數據時發生錯誤：{e}")
        print("繼續執行...")

def rebuild_all_pdfs(sources_folder: str = "Sources"):
    """重新處理所有 PDF"""
    sources_path = Path(sources_folder)
    
    if not sources_path.exists():
        print(f"❌ 找不到資料夾: {sources_folder}")
        return
    
    # 找到所有 PDF 檔案
    pdf_files = list(sources_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ 在 {sources_folder} 中找不到 PDF 檔案")
        return
    
    print(f"\n📚 找到 {len(pdf_files)} 個 PDF 檔案")
    print("=" * 70)
    
    # 處理每個 PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 處理: {pdf_path.name}")
        print("-" * 70)
        
        try:
            pdf_to_weaviate(
                pdf_filename=pdf_path.name,
                upload_folder=sources_folder
            )
            print(f"✓ 完成: {pdf_path.name}")
        except Exception as e:
            print(f"❌ 失敗: {pdf_path.name}")
            print(f"   錯誤: {e}")
            continue
    
    print("\n" + "=" * 70)
    print("🎉 所有 PDF 處理完成！")

def rebuild_single_pdf(pdf_filename: str, sources_folder: str = "Sources"):
    """重新處理單一 PDF"""
    print(f"\n📄 處理: {pdf_filename}")
    print("=" * 70)
    
    try:
        pdf_to_weaviate(
            pdf_filename=pdf_filename,
            upload_folder=sources_folder
        )
        print(f"✓ 完成: {pdf_filename}")
    except Exception as e:
        print(f"❌ 失敗: {pdf_filename}")
        print(f"   錯誤: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="重新生成並上傳 embeddings 到 Weaviate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 重建所有 PDF 的 embeddings
  python rebuild_embeddings.py
  
  # 只重建特定 PDF
  python rebuild_embeddings.py --pdf "example.pdf"
  
  # 指定不同的來源資料夾
  python rebuild_embeddings.py --sources-folder "Documents"
  
  # 不清空舊數據（增量添加）
  python rebuild_embeddings.py --no-clear
        """
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='只處理指定的 PDF 檔案'
    )
    
    parser.add_argument(
        '--sources-folder',
        type=str,
        default='Sources',
        help='PDF 檔案所在的資料夾（預設: Sources）'
    )
    
    parser.add_argument(
        '--no-clear',
        action='store_true',
        help='不清空 Weaviate 中的舊數據（增量添加）'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔄 重新生成 Embeddings")
    print("=" * 70)
    print(f"📂 使用資料夾: {args.sources_folder}")
    print(f"🤖 Embedding 模型: paraphrase-multilingual-MiniLM-L12-v2")
    print("=" * 70)
    
    # 清空舊數據（除非使用 --no-clear）
    if not args.no_clear:
        clear_weaviate_data()
    else:
        print("⚠️  跳過清空步驟（使用 --no-clear）")
    
    # 處理 PDF
    if args.pdf:
        rebuild_single_pdf(args.pdf, args.sources_folder)
    else:
        rebuild_all_pdfs(args.sources_folder)
    
    print("\n" + "=" * 70)
    print("✅ 完成！現在可以重新運行評估測試。")
    print("   執行: python evaluate/evaluate_rag.py --golden-dataset datasets/golden_weaviate_50_qa.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
