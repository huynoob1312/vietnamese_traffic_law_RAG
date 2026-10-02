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
from src.utils.config import USE_MULTI_QUERY, BENCHMARK_DATASET_SIZE
from benchmark.metrics import evaluate_retrieval_metrics
import concurrent.futures

def main():
    load_dotenv()
    
    if BENCHMARK_DATASET_SIZE == "full":
        dataset_path = 'benchmark/eval_dataset_filtered.jsonl'
    else:
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
        
        # Xử lý Retry khi dính lỗi từ LLM
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Ép thời gian chạy tối đa là 60 giây/câu để chống kẹt
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    if USE_MULTI_QUERY:
                        future = executor.submit(generate_multi_queries, question, llm)
                        queries = future.result(timeout=60)
                    else:
                        queries = [question]
                    
                    retrieved_docs = retriever.retrieve_multi(queries)
                break
            except concurrent.futures.TimeoutError:
                print(f"\n[CẢNH BÁO] Treo quá 60s ở câu này! Đang hủy tiến trình (Lần {attempt+1}/{max_retries})...")
                retrieved_docs = []
                break
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
        
        # Xử lý Ground Truth (Hỗ trợ cả trường hợp 1 đáp án hoặc nhiều đáp án dạng List)
        raw_sources = item.get('chunk_source', '')
        raw_dieus = item.get('chunk_dieu', '')
        
        if not isinstance(raw_sources, list):
            raw_sources = [raw_sources]
        if not isinstance(raw_dieus, list):
            raw_dieus = [raw_dieus]
            
        # Đảm bảo 2 mảng bằng nhau
        ground_truth_ids = []
        for src, dieu in zip(raw_sources, raw_dieus):
            src_normalized = str(src).replace('\\', '/')
            ground_truth_ids.append(f"{src_normalized}_{str(dieu)}")
        
        raw_retrieved_ids = [f"{d.metadata.get('source', '').replace('\\', '/')}_{str(d.metadata.get('dieu', ''))}" for d in retrieved_docs]
        
        # Loại bỏ các ID trùng lặp (vì nhiều chunk có thể thuộc cùng 1 Điều) nhưng vẫn giữ đúng thứ tự
        seen_ids = set()
        retrieved_ids = []
        for rid in raw_retrieved_ids:
            if rid not in seen_ids:
                retrieved_ids.append(rid)
                seen_ids.add(rid)
            
        retrieval_results.append({
            "retrieved": retrieved_ids,
            "ground_truths": ground_truth_ids
        })

    print("\n" + "="*50)
    print("KẾT QUẢ BENCHMARK (CẤU HÌNH HIỆN TẠI TỪ CONFIG.YAML)")
    print("="*50)
    
    final_scores = evaluate_retrieval_metrics(retrieval_results)
    
    for metric, score in final_scores.items():
        print(f"{metric}: {score}")

if __name__ == "__main__":
    main()
