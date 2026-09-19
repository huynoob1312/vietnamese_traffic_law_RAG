from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.config import EMBEDDING_MODEL

class E5EmbeddingsWrapper(HuggingFaceEmbeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed_texts = [f"passage: {text}" for text in texts]
        return super().embed_documents(prefixed_texts)
        
    def embed_query(self, text: str) -> list[float]:
        return super().embed_query(f"query: {text}")

def get_embedding_model():
    if "e5" in EMBEDDING_MODEL.lower():
        return E5EmbeddingsWrapper(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
