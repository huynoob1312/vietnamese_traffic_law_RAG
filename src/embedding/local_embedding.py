from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.config import EMBEDDING_MODEL
import torch

class E5EmbeddingsWrapper(HuggingFaceEmbeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed_texts = [f"passage: {text}" for text in texts]
        return super().embed_documents(prefixed_texts)
        
    def embed_query(self, text: str) -> list[float]:
        return super().embed_query(f"query: {text}")


import torch

def get_embedding_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    if "e5" in EMBEDDING_MODEL.lower():
        return E5EmbeddingsWrapper(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 16}
        )
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True, 'batch_size': 16}
    )
