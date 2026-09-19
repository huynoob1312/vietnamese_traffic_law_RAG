import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.vectordb.qdrant_client import get_qdrant_client
from src.utils.config import config
from src.retrieval.rag_chain import get_ensemble_retriever

def test_retrieval():
    qdrant = get_qdrant_client()
    top_k = config.get("retrieval", {}).get("top_k", 5)
    
    # EnsembleRetriever (Hybrid Search BM25 + Qdrant)
    retriever = get_ensemble_retriever(qdrant)
    
    while True:
        query = input("\nNhập câu hỏi (hoặc 'exit' để thoát): ").strip()
        if query.lower() in ["exit", "quit", "thoát"]:
            break
            
        if not query:
            continue
            
        docs = retriever.invoke(query)
        
        if not docs:
            print("Không tìm thấy kết quả nào!")
            continue
            
        for i, doc in enumerate(docs):
            print(f"\n{'='*75}")
            print(f"CHUNK SỐ {i+1}")
            print(f"THÔNG TIN (METADATA):")
            
            source = doc.metadata.get('source', '')
            source_name = source.split('\\')[-1] if '\\' in source else source.split('/')[-1]
            
            print(f"   - Nguồn: {source_name}")
            print(f"   - Điều: {doc.metadata.get('dieu', '')}")
            if doc.metadata.get("khoan"):
                print(f"   - Khoản: {doc.metadata.get('khoan')}")
            if doc.metadata.get("diem"):
                print(f"   - Điểm: {doc.metadata.get('diem')}")
                
            print("-" * 75)
            print(doc.page_content)
            print("-" * 75)

if __name__ == "__main__":
    test_retrieval()
