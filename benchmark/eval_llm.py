import os
import sys
import json
import time
from dotenv import load_dotenv

sys.path.append(os.path.abspath('.'))

# Bắt buộc cài đặt: pip install ragas datasets langchain-openai
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

from src.retrieval.rag_chain import build_rag_chain

def format_docs(docs):
    return [doc.page_content for doc in docs]

def main():
    load_dotenv()
    
    # 1. Chuẩn bị dữ liệu mẫu (Sample 10-20 câu để test trước cho đỡ tốn API)
    dataset_path = 'benchmark/eval_dataset.jsonl'
    raw_data = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                # Đánh giá LLM thường bỏ qua câu bẫy (is_trap), chỉ tập trung câu hỏi In-domain
                if not item.get('is_trap', False): 
                    raw_data.append(item)
    
    import random
    random.seed(42)
    sample_data = random.sample(raw_data, min(10, len(raw_data)))

    process_func, qa_chain = build_rag_chain()
    
    # Chuẩn bị danh sách API Keys Fallback
    api_keys_str = os.getenv("GEMINI_API_KEYS_FALLBACK", os.getenv("GEMINI_API_KEY", ""))
    fallback_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
    current_key_idx = 0
    
    questions = []
    answers = []
    contexts = []
    
    for item in sample_data:
        q = item['question']
        
        # Chạy Retrieval
        processed = process_func({"input": q})
        retrieved_docs = processed['context']  # Trích xuất list documents gốc
        # Chạy Generation có Retry và Auto-Rotate API Key
        max_retries = 5
        ans = ""
        for attempt in range(max_retries):
            try:
                ans = qa_chain.invoke(processed)
                break
            except Exception as e:
                error_msg = str(e).lower()
                if ('429' in error_msg or 'quota' in error_msg or 'exhausted' in error_msg) and len(fallback_keys) > 1:
                    current_key_idx = (current_key_idx + 1) % len(fallback_keys)
                    new_key = fallback_keys[current_key_idx]
                    os.environ["GEMINI_API_KEY"] = new_key
                    print(f"\n[QUOTA EXHAUSTED] Đã hết Quota! Chuyển sang API Key thứ {current_key_idx + 1}...")
                    process_func, qa_chain = build_rag_chain() # Rebuild lại chain với Key mới
                    time.sleep(2)
                    continue
                
                print(f"Lỗi API: Chờ 30s thử lại... ({attempt+1}/{max_retries})")
                time.sleep(30)
        
        questions.append(q)
        answers.append(ans)
        contexts.append(format_docs(retrieved_docs)) # Ragas yêu cầu mảng các chuỗi (string)
        
    # 3. Đóng gói thành Format Dataset của HuggingFace (Yêu cầu bắt buộc của Ragas)
    data_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts
    }
    hf_dataset = Dataset.from_dict(data_dict)
    
    # 4. Cấu hình Giám khảo (LLM-as-a-judge) qua OpenRouter
    # Dùng chuẩn ChatOpenAI kết nối tới OpenRouter để xài các model miễn phí.
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "nhap_key_openrouter_vao_day_neu_chua_co_trong_env")
    
    evaluator_llm = ChatOpenAI(
        openai_api_key=openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        # Bạn có thể dùng google/gemini-1.5-flash-exp:free hoặc meta-llama/llama-3.1-8b-instruct:free
        model_name="meta-llama/llama-3.1-8b-instruct:free" 
    )
    
    # Ragas cần thêm 1 Embedding model để đo Answer Relevancy.
    # Thay vì tốn tiền API, ta tái sử dụng luôn model Embedding Local bạn đang có sẵn. Miễn phí 100%!
    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-small", # Hoặc BAAI/bge-m3 tùy ý
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print(f"⚖️ Đang gọi Ragas để chấm điểm (LLM Judge: OpenRouter - {evaluator_llm.model_name})...")
    
    # 5. Khởi chạy Ragas Evaluate
    # Lưu ý: Chạy cái này sẽ tốn request lên API của Gemini.
    result = evaluate(
        dataset=hf_dataset,
        metrics=[
            faithfulness,      # Chấm điểm Trung thực (Không bịa đặt ngoài tài liệu)
            answer_relevancy   # Chấm điểm Đúng trọng tâm (Không trả lời lan man)
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        raise_exceptions=False # Để nếu bị lỗi timeout API thì không crash app
    )
    
    print("\n" + "="*50)
    print("KẾT QUẢ ĐÁNH GIÁ LLM")
    print("="*50)
    print(f"🔸 Faithfulness (Độ trung thực)       : {round(result['faithfulness'], 4)}")
    print(f"🔸 Answer Relevancy (Độ đúng trọng tâm): {round(result['answer_relevancy'], 4)}")
    print("="*50)
    
    # Bạn có thể xuất pandas dataframe để xem chi tiết điểm từng câu
    df = result.to_pandas()
    df.to_csv("benchmark/ragas_results.csv", index=False)
    print("Đã lưu kết quả chi tiết từng câu ra file: benchmark/ragas_results.csv")

if __name__ == "__main__":
    main()
