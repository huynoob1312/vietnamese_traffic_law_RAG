import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from src.ingestion.docx_loader import load_and_chunk_data

def test_chunking():
    base_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    chunks = load_and_chunk_data(base_data_dir)
    
    if not chunks:
        print("Không có chunk nào được tạo")
        return
        
    print(f"\n=> Tổng số chunks tạo ra: {len(chunks)}")
    print("-" * 50)
    
        
    output_file = os.path.join(os.path.dirname(__file__), "chunk_preview.jsonl")
    with open(output_file, "w", encoding="utf-8") as f:
        for chunk in chunks:
            data = {
                "metadata": chunk.metadata,
                "content": chunk.page_content
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
            
    print(f"\nĐã xuất toàn bộ {len(chunks)} chunks ra file để bạn kiểm tra tại:")
    print(f" -> {output_file}")

if __name__ == "__main__":
    test_chunking()
