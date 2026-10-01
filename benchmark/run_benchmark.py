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
from benchmark.metrics import evaluate_retrieval_metrics

def main():
    load_dotenv()
    
    dataset_path = 'benchmark/eval_dataset_test.jsonl'
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
        
        # Sinh multi-query và truy xuất (Chấp nhận chậm để kết quả chính xác)
        queries = generate_multi_queries(question, llm)
        retrieved_docs = retriever.retrieve_multi(queries)
        
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
        
    print("="*50)

if __name__ == "__main__":
    main()
