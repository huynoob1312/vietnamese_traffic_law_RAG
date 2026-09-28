import sys
import os
sys.path.append(os.getcwd())

from src.retrieval.rag_chain import build_rag_chain
from src.vectordb.qdrant_client import get_qdrant_client

try:
    process_func, qa_chain = build_rag_chain()
    print("Successfully built rag chain!")
    
    query = "nói giúp tôi điều 5 của luật 35 GTVT"
    inputs = {"input": query}
    
    retrieved = process_func(inputs)
    print("CONTEXT LENGTH:", len(retrieved["context"]))
    print("CONTEXT SNEAK PEEK:", retrieved["context"][:500])
except Exception as e:
    print("ERROR:", e)
