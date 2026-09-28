import json
import os

def filter_dataset(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"File {input_file} không tồn tại!")
        return

    banned_phrases = [
        "theo đoạn văn bản này",
        "theo quy định trên",
        "trong đoạn này",
        "dựa vào văn bản",
        "văn bản này",
        "đoạn văn trên"
    ]

    valid_lines = []
    seen_questions = set()
    total_lines = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            total_lines += 1
            try:
                data = json.loads(line)
                question = data.get("question", "").strip()
                question_lower = question.lower()

                # 1. Bỏ qua câu quá ngắn hoặc quá dài
                word_count = len(question.split())
                if word_count < 8 or word_count > 60:
                    continue

                # 2. Bỏ qua nếu chứa từ khóa cấm
                has_banned_phrase = False
                for phrase in banned_phrases:
                    if phrase in question_lower:
                        has_banned_phrase = True
                        break
                if has_banned_phrase:
                    continue

                # 3. Lọc trùng lặp
                if question_lower in seen_questions:
                    continue
                
                seen_questions.add(question_lower)
                valid_lines.append(data)
            except json.JSONDecodeError:
                continue

    # Ghi ra file mới
    with open(output_file, 'w', encoding='utf-8') as f:
        for d in valid_lines:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')

    print(f"Tổng số câu ban đầu: {total_lines}")
    print(f"Số câu hợp lệ sau khi lọc: {len(valid_lines)}")
    print(f"Đã loại bỏ: {total_lines - len(valid_lines)} câu bị lỗi/trùng lặp.")
    print(f"File đã lọc được lưu tại: {output_file}")

if __name__ == "__main__":
    filter_dataset("eval_dataset.jsonl", "eval_dataset_filtered.jsonl")
