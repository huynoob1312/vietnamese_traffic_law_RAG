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
from src.utils.config import LLM_PROVIDER

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def evaluate_latency(experiment_name: str, retriever, llm, prompt, dataset: list) -> dict:
    print(f"\n{'='*60}\n RUNNING LATENCY EVAL: {experiment_name}\n{'='*60}")
    
    answer_chain = prompt | llm | StrOutputParser()
    
    retrieval_times = []
    generation_times = []
    total_times = []
    
    for item in tqdm(dataset, desc="Evaluating Latency"):
        question = item['question']
        is_trap = item.get('is_trap', False)
        
        t0 = time.time()
        
        # 1. Đo Retrieval
        queries = generate_multi_queries(question, llm)
        retrieved_docs = retriever.retrieve_multi(queries)
        t1 = time.time()
        
        # 2. Đo Generation
        context = format_docs(retrieved_docs)
        answer = answer_chain.invoke({'context': context, 'input': question})
        t2 = time.time()
        
        retrieval_times.append(t1 - t0)
        generation_times.append(t2 - t1)
        total_times.append(t2 - t0)
                
    # Trả về kết quả
    res = {
        "Kịch bản": experiment_name,
        "Retrieval (s)": round(np.mean(retrieval_times), 3),
        "Generation (s)": round(np.mean(generation_times), 3),
        "Total (s)": round(np.mean(total_times), 3)
    }
    
    print(f"Retrieval Latency: {res['Retrieval (s)']} s")
    print(f"Generation Latency: {res['Generation (s)']} s")
    print(f"Total Latency: {res['Total (s)']} s")
    
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
        
    print(f"📚 Đã tải {len(dataset)} câu hỏi (Sample) từ {dataset_path}")
    
    # ---------------------------------------------
    # SETUP COMPONENT
    # ---------------------------------------------
    qdrant = get_qdrant_client()
    retriever = get_ensemble_retriever(qdrant)
    
    llm = get_llm()
    prompt = get_legal_prompt(LLM_PROVIDER)
    
    all_results = []
    
    # Bạn có thể gọi evaluate_latency nhiều lần với các llm, prompt khác nhau ở đây
    res_1 = evaluate_latency(
        experiment_name="Cấu hình hiện tại (từ config.yaml)", 
        retriever=retriever, 
        llm=llm, 
        prompt=prompt, 
        dataset=dataset
    )
    all_results.append(res_1)
    
    # IN BÁO CÁO
    print("\n" + "="*70)
    print("⏱️ BẢNG TỔNG SẮP ĐỘ TRỄ (LATENCY)")
    print("="*70)
    
    header = f"{'KỊCH BẢN':<35} | {'RETRIEVAL (s)':<13} | {'GENERATION (s)':<14} | {'TOTAL (s)':<10}"
    print(header)
    print("-" * 70)
    for res in all_results:
        print(f"{res['Kịch bản']:<35} | {res['Retrieval (s)']:<13} | {res['Generation (s)']:<14} | {res['Total (s)']:<10}")
    print("="*70)

if __name__ == "__main__":
    main()
