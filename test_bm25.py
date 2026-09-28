import sys, os
sys.path.append(os.getcwd())

import pickle
from pyvi import ViTokenizer
from langchain_community.retrievers import BM25Retriever

def pyvi_tokenize(text: str) -> list[str]:
    return ViTokenizer.tokenize(text).split()

with open("data/cached_chunks.pkl", "rb") as f:
    chunks = pickle.load(f)

bm25 = BM25Retriever.from_documents(chunks, preprocess_func=pyvi_tokenize)
res = bm25.invoke("Điều 5 Luật Đường bộ 35/2024")
print("FOUND:", len(res))
if res:
    print(res[0].page_content[:200])
