import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath('.'))

from src.ingestion.docx_loader import load_and_chunk_data
from src.vectordb.qdrant_client import push_to_qdrant

def main():
    load_dotenv()
    print("⏳ Đang đọc dữ liệu từ thư mục data...")
    chunks = load_and_chunk_data("data")
    
    if not chunks:
        print("❌ Không tìm thấy dữ liệu trong thư mục data!")
        return
        
    print(f"✅ Tìm thấy {len(chunks)} chunks. Đang đẩy lên Qdrant...")
    push_to_qdrant(chunks)
    print("🎉 Hoàn tất đẩy dữ liệu! Bây giờ bạn có thể chạy Benchmark hoặc Chat.")

if __name__ == "__main__":
    main()
