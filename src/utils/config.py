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
LLM_PROVIDER = config.get("llm_params", {}).get("provider", "gemini")
LLM_MODEL = config.get("llm_params", {}).get("model", "gemini-3.6-flash")
LLM_TEMPERATURE = config.get("llm_params", {}).get("temperature", 0.1)

# Hyperparameters
THRESH_DIEU = config.get("chunking", {}).get("thresh_dieu", 600)
THRESH_KHOAN_DEFAULT = config.get("chunking", {}).get("thresh_khoan_default", 500)
MIN_CHUNK = config.get("chunking", {}).get("min_chunk", 30)
MIN_CHUNK_DIEM = config.get("chunking", {}).get("min_chunk_diem", 5)

TOP_K = config.get("retrieval", {}).get("top_k", 3)
USE_RERANKER = config.get("retrieval", {}).get("use_reranker", False)
USE_MULTI_QUERY = config.get("retrieval", {}).get("use_multi_query", False)
RERANKER_MODEL = config.get("retrieval", {}).get("reranker_model", "BAAI/bge-reranker-base")
TOP_K_RAW = config.get("retrieval", {}).get("top_k_raw", 20)
SEARCH_TYPE = config.get("retrieval", {}).get("search_type", "hybrid")

def reload_config():
    """Tải lại nội dung file config.yaml và cập nhật các biến toàn cục."""
    global config, QDRANT_COLLECTION, EMBEDDING_MODEL, LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE
    global THRESH_DIEU, THRESH_KHOAN_DEFAULT, MIN_CHUNK, MIN_CHUNK_DIEM
    global TOP_K, USE_RERANKER, RERANKER_MODEL, TOP_K_RAW, SEARCH_TYPE
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    QDRANT_COLLECTION = config.get("qdrant", {}).get("collection_name", "legal_docs_vietnamese_bi_encoder")
    EMBEDDING_MODEL = config.get("models", {}).get("embedding", "bkai-foundation-models/vietnamese-bi-encoder")
    LLM_PROVIDER = config.get("llm_params", {}).get("provider", "ollama")
    LLM_MODEL = config.get("llm_params", {}).get("model", config.get("models", {}).get("llm", "qwen2.5:3b"))
    LLM_TEMPERATURE = config.get("llm_params", {}).get("temperature", 0.1)

    THRESH_DIEU = config.get("chunking", {}).get("thresh_dieu", 600)
    THRESH_KHOAN_DEFAULT = config.get("chunking", {}).get("thresh_khoan_default", 500)
    MIN_CHUNK = config.get("chunking", {}).get("min_chunk", 30)
    MIN_CHUNK_DIEM = config.get("chunking", {}).get("min_chunk_diem", 5)

    TOP_K = config.get("retrieval", {}).get("top_k", 3)
    USE_RERANKER = config.get("retrieval", {}).get("use_reranker", False)
    RERANKER_MODEL = config.get("retrieval", {}).get("reranker_model", "BAAI/bge-reranker-v2-m3")
    TOP_K_RAW = config.get("retrieval", {}).get("top_k_raw", 20)
    SEARCH_TYPE = config.get("retrieval", {}).get("search_type", "hybrid")
    return config

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "traffic_law_rag")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)

# JWT & Security Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "traffic-law-rag-secret-key-change-in-production-2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

BENCHMARK_DATASET_SIZE = config.get("benchmark", {}).get("dataset_size", "sample")
