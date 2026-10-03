import os
import sys
import json
import time
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv

sys.path.append(os.path.abspath('.'))

from langchain_core.output_parsers import StrOutputParser

from src.retrieval.rag_chain import get_ensemble_retriever, generate_multi_queries
from src.vectordb.qdrant_client import get_qdrant_client
from src.llm.local_llm import get_llm
from src.prompt.legal_prompt import get_legal_prompt
from src.utils.config import LLM_PROVIDER, USE_MULTI_QUERY

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def evaluate_latency(experiment_name: str, retriever, llm, dataset: list) -> dict:
    print(f"\n{'='*60}\n RUNNING LATENCY EVAL: {experiment_name}\n{'='*60}")
    
    retrieval_times = []
    
    for item in tqdm(dataset, desc="Evaluating Latency"):
        question = item['question']
        is_trap = item.get('is_trap', False)
        
        # 1. Đo Retrieval
        for attempt in range(5):
            try:
                t0 = time.time()
                if USE_MULTI_QUERY:
                    queries = generate_multi_queries(question, llm)
                else:
                    queries = [question]
                    
                retrieved_docs = retriever.retrieve_multi(queries)
                t1 = time.time()
                break
            except Exception as e:
                error_msg = str(e).lower()
                if '429' in error_msg or 'quota' in error_msg or 'exhausted' in error_msg or '503' in error_msg or 'unavailable' in error_msg:
                    print(f"\n[CẢNH BÁO] Kẹt API hoặc Server quá tải (Lần {attempt+1}/5). Chờ 30s...")
                    time.sleep(30)
                else:
                    raise e
        
        retrieval_times.append(t1 - t0)
                
    # Trả về kết quả
    res = {
        "Kịch bản": experiment_name,
        "Latency (s)": round(np.mean(retrieval_times), 3)
    }
    
    print(f"Average Latency: {res['Latency (s)']} s")
    
    return res

def main():
    load_dotenv()
    
    dataset_path = 'benchmark/eval_dataset_test.jsonl'
    if not os.path.exists(dataset_path):
        dataset_path = 'benchmark/eval_dataset.jsonl'
        
    dataset = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                dataset.append(json.loads(line))
                
    SAMPLE_SIZE = 20
    if len(dataset) > SAMPLE_SIZE:
        import random
        random.seed(42)
        dataset = random.sample(dataset, SAMPLE_SIZE)
        
    print(f"Đã tải {len(dataset)} câu hỏi (Sample) từ {dataset_path}")
    
    # SETUP COMPONENT
    qdrant = get_qdrant_client()
    retriever = get_ensemble_retriever(qdrant)
    
    llm = get_llm()
    
    all_results = []
    
    res_1 = evaluate_latency(
        experiment_name="Cấu hình hiện tại (từ config.yaml)", 
        retriever=retriever, 
        llm=llm, 
        dataset=dataset
    )
    all_results.append(res_1)
    
    # IN BÁO CÁO
    print("\n" + "="*70)
    print("BẢNG TỔNG SẮP ĐỘ TRỄ (LATENCY)")
    print("="*70)
    
    header = f"{'KỊCH BẢN':<35} | {'LATENCY (s)':<13}"
    print(header)
    print("-" * 50)
    for res in all_results:
        print(f"{res['Kịch bản']:<35} | {res['Latency (s)']:<13}")
    print("="*50)

if __name__ == "__main__":
    main()
