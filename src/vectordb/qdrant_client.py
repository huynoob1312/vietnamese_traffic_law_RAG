from langchain_qdrant import QdrantVectorStore
from src.utils.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION
from src.embedding.local_embedding import get_embedding_model

def get_qdrant_client():
    embeddings = get_embedding_model()
    
    if not QDRANT_URL or not QDRANT_API_KEY or "your-cluster-url" in QDRANT_URL:
        raise ValueError("Vui lòng cấu hình QDRANT_URL và QDRANT_API_KEY trong file .env")

    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=QDRANT_COLLECTION,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

def push_to_qdrant(chunks):
    embeddings = get_embedding_model()
    
    if not QDRANT_URL or not QDRANT_API_KEY or "your-cluster-url" in QDRANT_URL:
        raise ValueError("Vui lòng cấu hình QDRANT_URL và QDRANT_API_KEY trong file .env")

    print("Đang khởi tạo Collection và đẩy đợt dữ liệu đầu tiên (500 chunks)...")
    vector_store = QdrantVectorStore.from_documents(
        chunks[:500],
        embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=QDRANT_COLLECTION,
        force_recreate=True,
        timeout=120,
    )

    batch_size = 500
    total = len(chunks)
    for i in range(500, total, batch_size):
        batch = chunks[i : i + batch_size]
        print(f"-> Đang đẩy tiếp từ chunk {i} đến {i + len(batch)} / {total} ...")
        vector_store.add_documents(batch)
        
    return vector_store
