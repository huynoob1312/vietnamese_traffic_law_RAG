from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from src.ingestion.docx_loader import load_and_chunk_data
from src.llm.local_llm import get_llm
from src.vectordb.qdrant_client import get_qdrant_client
from src.prompt.legal_prompt import get_legal_prompt
from src.utils.config import TOP_K, USE_RERANKER, RERANKER_MODEL, TOP_K_RAW, LLM_PROVIDER
from pyvi import ViTokenizer
from sentence_transformers import CrossEncoder
from langchain_community.retrievers import BM25Retriever

import os
import pickle
import concurrent.futures


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def reciprocal_rank_fusion(results, k=60):
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            content = doc.page_content
            if content not in fused_scores:
                fused_scores[content] = {"doc": doc, "score": 0}
            fused_scores[content]["score"] += 1 / (rank + k)
            
    reranked = [item["doc"] for item in sorted(fused_scores.values(), key=lambda x: x["score"], reverse=True)]
    return reranked

def get_ensemble_retriever(qdrant):
    cache_path = os.path.join("data", "cached_chunks.pkl")
    
    # init Qdrant Retriever
    qdrant_retriever = qdrant.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": TOP_K_RAW}
    )
    
    # BM25 Retriever (Keyword Search)
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            chunks = pickle.load(f)
    else:
        chunks = load_and_chunk_data("data")
        with open(cache_path, "wb") as f:
            pickle.dump(chunks, f)
            
    dieu_index = {}
    for doc in chunks:
        source = doc.metadata.get("source", "")
        dieu = str(doc.metadata.get("dieu", ""))
        if source and dieu:
            key = (source, dieu)
            if key not in dieu_index:
                dieu_index[key] = []
            dieu_index[key].append(doc)

    def pyvi_tokenize(text: str) -> list[str]:
        return ViTokenizer.tokenize(text).split()
        
    bm25_retriever = BM25Retriever.from_documents(chunks, preprocess_func=pyvi_tokenize)
    bm25_retriever.k = TOP_K_RAW

    reranker = None
    if USE_RERANKER:
        reranker = CrossEncoder(RERANKER_MODEL)

    # 3. Custom Retriever (RRF/Reranker + Sibling Enrichment)
    class CustomEnsembleRetriever:
        def retrieve_multi(self, queries: list[str]):
            all_lists = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                bm25_futures = [executor.submit(bm25_retriever.invoke, q) for q in queries]
                qdrant_futures = [executor.submit(qdrant_retriever.invoke, q) for q in queries]
                
                for f in bm25_futures + qdrant_futures:
                    all_lists.append(f.result())
                    
            if USE_RERANKER and reranker is not None:
                raw_candidates = []
                seen = set()
                for lst in all_lists:
                    for doc in lst:
                        if doc.page_content not in seen:
                            raw_candidates.append(doc)
                            seen.add(doc.page_content)
                
                # Chấm điểm toàn bộ bằng Reranker
                pairs = [[queries[0], doc.page_content] for doc in raw_candidates]
                scores = reranker.predict(pairs)
                
                # Sắp xếp lại và lấy TOP_K
                scored_docs = list(zip(raw_candidates, scores))
                scored_docs.sort(key=lambda x: x[1], reverse=True)
                fused_docs = [doc for doc, score in scored_docs][:TOP_K]
            else:
                # RRF toàn cục (Global RRF) nếu KHÔNG dùng Reranker
                fused_docs = reciprocal_rank_fusion(all_lists)[:TOP_K]
             
            enriched_docs = []
            seen_contents = set()
            
            for doc in fused_docs:
                if doc.page_content not in seen_contents:
                    enriched_docs.append(doc)
                    seen_contents.add(doc.page_content)
                    
                source = doc.metadata.get("source", "")
                dieu = str(doc.metadata.get("dieu", ""))
                khoan_str = str(doc.metadata.get("khoan", ""))
                
                if not source or not dieu or not khoan_str.isdigit():
                    continue
                    
                khoan = int(khoan_str)
                siblings = dieu_index.get((source, dieu), [])
                
                for sib in siblings:
                    sib_khoan_str = str(sib.metadata.get("khoan", ""))
                    if sib_khoan_str.isdigit():
                        sib_khoan = int(sib_khoan_str)
                        if abs(sib_khoan - khoan) <= 2 and sib_khoan != khoan:
                            if sib.page_content not in seen_contents:
                                enriched_docs.append(sib)
                                seen_contents.add(sib.page_content)
                                
            return enriched_docs
            
        def invoke(self, query: str):
            return self.retrieve_multi([query])
            
    return CustomEnsembleRetriever()

def generate_multi_queries(query: str, llm) -> list[str]:
    if LLM_PROVIDER.lower() == "gemini":
        template = """Bạn là một chuyên gia pháp lý tại Việt Nam.
Nhiệm vụ của bạn là tạo ra 3 câu truy vấn để tối ưu hóa việc tìm kiếm trong cơ sở dữ liệu luật.
QUY TẮC:
1. Tập trung chuyển đổi từ lóng sang thuật ngữ pháp lý chính xác (ví dụ: 'kẹp 3' -> 'chở quá số người', 'vượt đèn đỏ' -> 'không chấp hành đèn tín hiệu').
2. NẾU CÂU HỎI CÓ NHIỀU LỖI VI PHẠM, hãy tách mỗi lỗi thành một câu truy vấn riêng biệt để tìm kiếm chính xác hơn.
Trả lời dưới dạng danh sách, mỗi câu hỏi một dòng. Không giải thích thêm.

Câu hỏi gốc: {question}"""
    else:
        template = """<|im_start|>system
Bạn là chuyên gia pháp lý. Nhiệm vụ của bạn là tạo ra 3 câu truy vấn để tối ưu hóa việc tìm kiếm luật.
QUY TẮC:
1. Chuyển đổi từ lóng sang thuật ngữ chính xác (vd: 'kẹp 3' -> 'chở quá số người').
2. NẾU CÓ NHIỀU LỖI VI PHẠM, bắt buộc tách mỗi lỗi thành 1 câu truy vấn riêng biệt.
Trả lời dưới dạng danh sách, mỗi câu một dòng. TUYỆT ĐỐI không giải thích thêm.
<|im_end|>
<|im_start|>user
Câu hỏi gốc: {question}
<|im_end|>
<|im_start|>assistant
"""
    prompt = PromptTemplate(template=template, input_variables=["question"])
    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({"question": query})
    queries = [q.strip("- *1234567890.") for q in res.split("\n") if q.strip()]
    return [query] + queries[:3]

def build_rag_chain():
    qdrant = get_qdrant_client()
    retriever = get_ensemble_retriever(qdrant)
    
    llm = get_llm()
    prompt = get_legal_prompt(LLM_PROVIDER)
    
    def process_and_retrieve(inputs):
        original_query = inputs["input"]
        
        queries = generate_multi_queries(original_query, llm)
        
        # Gọi Global RRF bằng hàm retrieve_multi
        final_docs = retriever.retrieve_multi(queries)
        
        context = format_docs(final_docs)
        
        return {
            "context": context,
            "input": original_query
        }

    answer_chain = prompt | llm | StrOutputParser()
    return process_and_retrieve, answer_chain
