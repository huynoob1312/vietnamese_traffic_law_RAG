import os
import sys
import json
import time
import numpy as np
import torch
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

    checkpoint_file = 'benchmark/benchmark_checkpoint.json'
    retrieval_results = []
    processed_count = 0
    
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            retrieval_results = json.load(f)
        processed_count = len(retrieval_results)
        print(f"\n[HỆ THỐNG] Đã tìm thấy Checkpoint! Khôi phục thành công {processed_count} câu đã chạy.")

    print(f"BẮT ĐẦU CHẠY BENCHMARK TRÊN {len(dataset)} CÂU HỎI...")
    
    for item in tqdm(dataset[processed_count:], initial=processed_count, total=len(dataset), desc="Evaluating"):
        question = item['question']
        
        # Xử lý Retry khi dính lỗi từ LLM
        max_retries = 5
        for attempt in range(max_retries):
            try:
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                if USE_MULTI_QUERY:
                    future = executor.submit(generate_multi_queries, question, llm)
                    queries = future.result(timeout=240)
                else:
                    queries = [question]
                
                retrieved_docs = retriever.retrieve_multi(queries)
                executor.shutdown(wait=False)
                break
            except concurrent.futures.TimeoutError:
                print(f"\n[CẢNH BÁO] Treo quá 240s ở câu này (Lần {attempt+1}/{max_retries}). Máy chủ Ollama có thể đã chết lâm sàng do tràn RAM!")
                
                os.system("pkill -9 ollama")
                
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass
                    
                time.sleep(10)
                os.system("nohup ollama serve > /dev/null 2>&1 &")
                time.sleep(10)
                
                if attempt >= 1:
                    print("Skip")
                    retrieved_docs = []
                    break
                
                continue
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
            src_basename = os.path.basename(str(src).replace('\\', '/'))
            ground_truth_ids.append(f"{src_basename}_{str(dieu)}")
        
        raw_retrieved_ids = [f"{os.path.basename(d.metadata.get('source', '').replace('\\', '/'))}_{str(d.metadata.get('dieu', ''))}" for d in retrieved_docs]
        
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
        
        # Lưu Checkpoint (Save Game) sau mỗi câu
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(retrieval_results, f, ensure_ascii=False, indent=2)

    print("\n" + "="*50)
    print("KẾT QUẢ BENCHMARK (CẤU HÌNH HIỆN TẠI TỪ CONFIG.YAML)")
    print("="*50)
    
    final_scores = evaluate_retrieval_metrics(retrieval_results)
    
    for metric, score in final_scores.items():
        print(f"{metric}: {score}")

if __name__ == "__main__":
    main()
