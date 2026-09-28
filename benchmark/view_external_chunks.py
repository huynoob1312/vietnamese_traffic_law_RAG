import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader
from src.chunking.legal_chunker import LegalDocumentChunker

def test_chunking():
    external_dir = os.path.join("benchmark", "data_ngoai")
    
    loader = DirectoryLoader(
        external_dir, 
        glob="**/*.docx", 
        exclude=["**/~$*.docx"],
        loader_cls=Docx2txtLoader
    )
    documents = loader.load()
    if not documents:
        print("Không tìm thấy file nào.")
        return

    chunks = []
    for doc in documents:
        filename = doc.metadata.get("source", "").lower()
        if "nd-cp" in filename or "nd" in filename or "nghidinh" in filename or "nghị định" in filename:
            doc_type = "nghidinh"
        elif "tt" in filename or "thongtu" in filename or "thông tư" in filename:
            doc_type = "thongtu"
        else:
            doc_type = "luat"
            
        doc.metadata["doc_type"] = doc_type
        chunker = LegalDocumentChunker(doc_type=doc_type)
        chunks.extend(chunker.split_documents([doc]))
    
    print(f"Tổng số chunk cắt được: {len(chunks)}\n")
    
    # Ghi ra file JSONL để dễ dàng xem toàn bộ
    output_preview = os.path.join("scripts", "chunk_preview_external.jsonl")
    os.makedirs("scripts", exist_ok=True)
    
    import json
    with open(output_preview, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            record = {
                "chunk_id": i + 1,
                "source": chunk.metadata.get('source', ''),
                "doc_type": chunk.metadata.get('doc_type', ''),
                "dieu": chunk.metadata.get('dieu', ''),
                "content": chunk.page_content
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
    print(len(chunks))

if __name__ == "__main__":
    test_chunking()
