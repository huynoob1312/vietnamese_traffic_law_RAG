import json
import random
import os

def view_beautiful_json(num_samples=5, random_pick=False):
    jsonl_file = "chunk_preview.jsonl"
    
    if not os.path.exists(jsonl_file):
        print(f"Lỗi: Không tìm thấy file {jsonl_file}. Hãy chạy test_chunking.py trước.")
        return
        
    with open(jsonl_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    if not lines:
        return
        
    print(f"Tổng số chunks trong file: {len(lines)}")
    
    if random_pick:
        selected_lines = random.sample(lines, min(num_samples, len(lines)))
        print(f"\n---> ĐANG HIỂN THỊ NGẪU NHIÊN {len(selected_lines)} CHUNKS <---")
    else:
        selected_lines = lines[:num_samples]
        print(f"\n---> ĐANG HIỂN THỊ {len(selected_lines)} CHUNKS ĐẦU TIÊN <---")

    for i, line in enumerate(selected_lines):
        data = json.loads(line.strip())
        
        print("\n")
        print(f"CHUNK SỐ {i+1}")
        
        print("[METADATA]")
        # In metadata định dạng JSON có thụt lề (indent) để dễ đọc
        print(json.dumps(data.get("metadata", {}), indent=4, ensure_ascii=False))
        
        print("\n📝 [NỘI DUNG VĂN BẢN]")
        print("-" * 70)
        print(data.get("content", ""))
        print("-" * 70)
        print("\n")

if __name__ == "__main__":
    print("TÙY CHỌN XEM CHUNKS:")
    print("1. Xem 3 chunks đầu tiên (Mặc định)")
    print("2. Xem 3 chunks ngẫu nhiên (Để kiểm tra độ đa dạng)")
    
    choice = input("Nhập lựa chọn của bạn (1 hoặc 2): ").strip()
    
    if choice == "2":
        view_beautiful_json(num_samples=3, random_pick=True)
    else:
        view_beautiful_json(num_samples=3, random_pick=False)
