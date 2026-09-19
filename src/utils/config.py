import os
import yaml
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")
with open(config_path, "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

QDRANT_COLLECTION = config["qdrant"]["collection_name"]
EMBEDDING_MODEL = config["models"]["embedding"]
LLM_PROVIDER = config.get("llm_params", {}).get("provider", "ollama")
LLM_MODEL = config.get("llm_params", {}).get("model", config["models"]["llm"])
LLM_TEMPERATURE = config.get("llm_params", {}).get("temperature", 0.1)

# Hyperparameters
THRESH_DIEU = config.get("chunking", {}).get("thresh_dieu", 600)
THRESH_KHOAN_DEFAULT = config.get("chunking", {}).get("thresh_khoan_default", 500)
MIN_CHUNK = config.get("chunking", {}).get("min_chunk", 30)
MIN_CHUNK_DIEM = config.get("chunking", {}).get("min_chunk_diem", 5)

TOP_K = config.get("retrieval", {}).get("top_k", 3)
USE_RERANKER = config.get("retrieval", {}).get("use_reranker", False)
RERANKER_MODEL = config.get("retrieval", {}).get("reranker_model", "BAAI/bge-reranker-base")
TOP_K_RAW = config.get("retrieval", {}).get("top_k_raw", 20)
