import os
import sys
import json
import time
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv

sys.path.append(os.path.abspath('.'))

from src.vectordb.qdrant_client import get_qdrant_client
from src.retrieval.rag_chain import get_ensemble_retriever, generate_multi_queries
from src.llm.local_llm import get_llm
from src.utils.config import USE_MULTI_QUERY
from benchmark.metrics import evaluate_retrieval_metrics

def main():
    load_dotenv()
    
    dataset_path = 'benchmark/eval_dataset_sample_200.jsonl'
    if not os.path.exists(dataset_path):
        dataset_path = 'benchmark/eval_dataset.jsonl'
        
    dataset = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                if not item.get('is_trap', False):
                    dataset.append(item)
    qdrant = get_qdrant_client()
    retriever = get_ensemble_retriever(qdrant)
    llm = get_llm()

    retrieval_results = []

    print(f"BẮT ĐẦU CHẠY BENCHMARK TRÊN {len(dataset)} CÂU HỎI...")
    
    for item in tqdm(dataset, desc="Evaluating"):
        question = item['question']
        ground_truth_source = item.get('chunk_source', '')
        ground_truth_dieu = str(item.get('chunk_dieu', ''))
        
        # Xử lý Retry khi dính lỗi từ LLM
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if USE_MULTI_QUERY:
                    queries = generate_multi_queries(question, llm)
                else:
                    queries = [question] # Dùng mỗi câu hỏi gốc, bỏ qua LLM
                
                retrieved_docs = retriever.retrieve_multi(queries)
                break # Nếu thành công thì thoát vòng lặp retry
            except Exception as e:
                error_msg = str(e).lower()
                if '429' in error_msg or 'quota' in error_msg or 'exhausted' in error_msg or '503' in error_msg or 'unavailable' in error_msg:
                    print(f"\n[CẢNH BÁO] Kẹt API hoặc Mạng (Lần {attempt+1}/{max_retries}). Chờ 30 giây rồi thử lại...")
                    time.sleep(30)
                else:
                    print(f"\n[LỖI LẠ] Bỏ qua câu này do lỗi: {error_msg}")
                    retrieved_docs = []
                    break
        else:
            print("\n[THẤT BẠI] Đã thử 5 lần nhưng vẫn kẹt API, bỏ qua câu này.")
            retrieved_docs = []
        
        # Tạo định danh (ID) chuẩn
        ground_truth_id = f"{ground_truth_source}_{ground_truth_dieu}"
        retrieved_ids = [f"{d.metadata.get('source', '')}_{str(d.metadata.get('dieu', ''))}" for d in retrieved_docs]
            
        retrieval_results.append({
            "retrieved": retrieved_ids,
            "ground_truths": [ground_truth_id]
        })

    print("\n" + "="*50)
    print("KẾT QUẢ BENCHMARK (CẤU HÌNH HIỆN TẠI TỪ CONFIG.YAML)")
    print("="*50)
    
    final_scores = evaluate_retrieval_metrics(retrieval_results)
    
    for metric, score in final_scores.items():
        print(f"{metric}: {score}")

if __name__ == "__main__":
    main()
